"""Active-area upload, redaction preview, and guide mutation routes."""

import re
from collections.abc import Callable
from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from pypdf.errors import PdfReadError
from starlette.datastructures import UploadFile

from core import contracts
from features.ui import folder_routes, folders, upload_guard, workspace
from features.ui.native_import_routes import build_router as native_import_router

MAX_PREVIEW_BYTES = upload_guard.MAX_UPLOAD_BYTES
_BAD_SEG_RE = re.compile(r"[^\w .-]+", re.UNICODE)


def _safe_rel_folder(rel_path: str) -> str:
    parts = [p for p in rel_path.replace("\\", "/").split("/")[:-1] if p and p not in {".", ".."}]
    cleaned = [re.sub(r"\s+", " ", _BAD_SEG_RE.sub("_", p)).strip(" ._-")[:64] for p in parts]
    return "/".join(seg for seg in cleaned if seg and not seg.startswith("."))


def build_router(config: Callable[[], contracts.WorkspaceConfig], reindex: Callable[[Path], list[contracts.KnowledgeChunk]], convert: Callable[[str, bytes, list[str] | None], str], inspect: Callable[[str, str], dict[str, object]], slug: Callable[[str, str], str]) -> APIRouter:
    router = APIRouter()

    @router.post("/api/anonymize/preview", response_model=contracts.AnonymizationReport)
    async def preview(request: Request) -> JSONResponse:
        try:
            if "application/json" in request.headers.get("content-type", ""):
                if len(await request.body()) > MAX_PREVIEW_BYTES:
                    raise HTTPException(status_code=413, detail="Preview input is too large")
                body = await request.json()
                if isinstance(body, dict) and isinstance(body.get("text"), str):
                    upload_guard.check_file_size(body["text"].encode("utf-8"))
                payload = contracts.AnonymizationPreview.model_validate(body)
                if payload.doc_id is not None:
                    with workspace.STATE_LOCK:
                        active = config()
                        workspace.require_area(request, active)
                        base, local_id = workspace.resolve_selected_guide(active, payload.doc_id)
                        path = workspace.resolve_guide_file(base, local_id)
                        if path.stat().st_size > MAX_PREVIEW_BYTES:
                            raise HTTPException(status_code=413, detail="Guide is too large to preview")
                        text, filename = path.read_text(encoding="utf-8"), path.name
                elif payload.text is not None:
                    text, filename = payload.text, payload.filename
                else:
                    raise HTTPException(status_code=400, detail="Provide text, a document ID, or a file")
            else:
                form = await request.form()
                file = form.get("file") or form.get("files")
                if not isinstance(file, UploadFile):
                    raise HTTPException(status_code=400, detail="Provide a file to preview")
                try:
                    raw = await upload_guard.read_file(file)
                finally:
                    await form.close()
                filename = file.filename or ""
                workspace.validate_upload_filename(filename)
                text = convert(filename, raw, workspace.auto_tags_for_filename(filename))
            if len(text) > 1_000_000:
                raise HTTPException(status_code=413, detail="Extracted text is too large to preview")
            return JSONResponse(inspect(text, filename), headers={"Cache-Control": "no-store"})
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail="Invalid preview input") from exc
        except (ValueError, OSError, BadZipFile, ParseError, PdfReadError, EOFError, KeyError) as exc:
            raise HTTPException(status_code=400, detail="Unable to inspect this document") from exc

    @router.post("/api/upload")
    async def upload(request: Request) -> dict[str, object]:
        files, tags, anonymize, subfolder, save_area, rel_paths, skip_unsupported = await upload_guard.read_upload(request, workspace.decode_json_upload)
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            area = active.knowledge_dir if save_area is None else save_area
            if not isinstance(area, str) or area not in active.active_dirs:
                raise HTTPException(status_code=400, detail="Save to one of the selected areas")
            target = workspace.resolve_safe_knowledge_dir(area, create=True)
            try:
                destination = folders.resolve_subfolder(target, subfolder, create=True)
            except (ValueError, TypeError, OSError) as exc:
                raise HTTPException(status_code=400, detail="Invalid subfolder path") from exc
            total, skipped, titles, uploaded = 0, 0, [], []
            for idx, (filename, raw) in enumerate(files):
                rel = rel_paths[idx] if idx < len(rel_paths) else ""
                base_name = Path(filename.replace("\\", "/")).name if skip_unsupported else filename
                if skip_unsupported and (not base_name or base_name.startswith(".") or "__MACOSX" in rel.split("/")):
                    skipped += 1
                    continue
                try:
                    stem, _ = workspace.validate_upload_filename(base_name)
                    rel_sub = _safe_rel_folder(rel) if rel else ""
                    item_dest = folders.resolve_subfolder(destination, rel_sub, create=True) if rel_sub else destination
                    do_anon = active.anonymize_uploads if anonymize is None else bool(anonymize)
                    stem = slug(base_name, stem) if do_anon else stem
                    text = convert(base_name, raw, workspace.auto_tags_for_filename(base_name, tags))
                    report = contracts.AnonymizationReport.model_validate(inspect(text, base_name)) if do_anon else None
                    path = item_dest / f"{stem}.md"
                    if path.is_symlink():
                        raise ValueError("Uploads cannot replace symbolic links")
                    path.write_text(report.scrubbed_text if report else text, encoding="utf-8")
                    uploaded.append(rel or base_name)
                    titles.append((report.scrubbed_text if report else text).splitlines()[0].lstrip("# "))
                    total += report.total_redacted if report else 0
                except (ValueError, BadZipFile, ParseError, PdfReadError) as exc:
                    if skip_unsupported:
                        skipped += 1
                        continue
                    raise HTTPException(status_code=400, detail="Unable to index this document") from exc
            if not uploaded:
                raise HTTPException(status_code=400, detail="No supported documents found in this folder")
            return {**workspace.build_workspace_payload(active, reindex(target)), "uploaded_files": uploaded, "uploaded_titles": titles, "redacted_count": total, "skipped_files": skipped}

    @router.post("/api/guides/{doc_id:path}/anonymize")
    def anonymize_guide(doc_id: str, request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            target, local_id = workspace.resolve_selected_guide(active, doc_id)
            path = workspace.resolve_guide_file(target, local_id)
            report = contracts.AnonymizationReport.model_validate(inspect(path.read_text(encoding="utf-8"), path.name))
            path.write_text(report.scrubbed_text, encoding="utf-8")
            reindex(target)
            return {"doc_id": doc_id, "redacted_count": report.total_redacted}

    @router.delete("/api/guides/{doc_id:path}")
    def delete_guide(doc_id: str, request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            target, local_id = workspace.resolve_selected_guide(active, doc_id)
            workspace.resolve_guide_file(target, local_id).unlink()
            reindex(target)
            return {"doc_id": doc_id, "deleted": True}

    router.include_router(folder_routes.build_router(config, reindex))
    router.include_router(native_import_router(config, reindex, convert, inspect, slug))
    return router
