"""Redaction preview route for text, existing guides, and uploaded documents."""

from collections.abc import Callable
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from pypdf.errors import PdfReadError
from starlette.datastructures import UploadFile

from core import contracts
from features.ui import route_helpers, selection, upload_guard, workspace

MAX_PREVIEW_BYTES = upload_guard.MAX_UPLOAD_BYTES
TEXT_SUFFIXES = frozenset({".md", ".txt", ".html", ".csv", ".tsv"})


def build_router(
    config: Callable[[], contracts.WorkspaceConfig],
    convert: Callable[[str, bytes, list[str] | None], str],
    inspect: Callable[[str, str], dict[str, object]],
) -> APIRouter:
    router = APIRouter()

    @router.post("/api/anonymize/preview", response_model=contracts.AnonymizationReport)
    async def preview(request: Request) -> JSONResponse:
        try:
            is_json = "application/json" in request.headers.get("content-type", "")
            raw_json: object = None
            raw_file: tuple[str, bytes] | None = None
            if is_json:
                if len(await request.body()) > MAX_PREVIEW_BYTES:
                    raise HTTPException(status_code=413, detail="Preview input is too large")
                raw_json = await request.json()
            else:
                form = await request.form()
                if not isinstance(file := form.get("file") or form.get("files"), UploadFile):
                    raise HTTPException(status_code=400, detail="Provide a file to preview")
                try:
                    raw_file = (file.filename or "", await upload_guard.read_file(file))
                finally:
                    await form.close()

            def _run() -> dict[str, object]:
                if is_json:
                    if isinstance(raw_json, dict) and isinstance(raw_json.get("text"), str):
                        upload_guard.check_file_size(raw_json["text"].encode("utf-8"))
                    payload = contracts.AnonymizationPreview.model_validate(raw_json)
                    if payload.doc_id is not None:
                        with workspace.STATE_LOCK:
                            active = config()
                            workspace.require_area(request, active)
                            base, local_id = workspace.resolve_selected_guide(active, payload.doc_id)
                            selection.assert_guide_not_excluded(active, route_helpers.guide_area_slug(active, payload.doc_id), local_id)
                            path = workspace.resolve_guide_file(base, local_id)
                            if path.stat().st_size > MAX_PREVIEW_BYTES:
                                raise HTTPException(status_code=413, detail="Guide is too large to preview")
                            filename = path.name
                            text = path.read_text(encoding="utf-8", errors="replace") if path.suffix.lower() in TEXT_SUFFIXES else convert(filename, path.read_bytes(), None)
                    elif payload.text is not None:
                        text, filename = payload.text, payload.filename
                    else:
                        raise HTTPException(status_code=400, detail="Provide text, a document ID, or a file")
                else:
                    assert raw_file is not None
                    filename, raw = raw_file
                    workspace.validate_upload_filename(filename)
                    text = convert(filename, raw, workspace.auto_tags_for_filename(filename))
                if len(text) > 1_000_000:
                    raise HTTPException(status_code=413, detail="Extracted text is too large to preview")
                return inspect(text, filename)

            return JSONResponse(await run_in_threadpool(_run), headers={"Cache-Control": "no-store"})
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail="Invalid preview input") from exc
        except (ValueError, OSError, BadZipFile, ParseError, PdfReadError, EOFError, KeyError) as exc:
            raise HTTPException(status_code=400, detail="Unable to inspect this document") from exc

    return router
