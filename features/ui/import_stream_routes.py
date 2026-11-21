"""Live SSE streaming progress route for native OS folder import."""

import asyncio
import json
import threading
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pypdf.errors import PdfReadError

from core.contracts import AnonymizationReport, KnowledgeChunk, WorkspaceConfig
from core.db import atomic_write_text
from core.linked_vaults import (
    is_linked_vault,
    pick_native_folder,
    validate_external_folder,
)
from features.ui import (
    folders,
    guide_edit_routes,
    native_import_routes,
    upload_guard,
    workspace,
)


def _sse(event: str, payload: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def build_router(config: Callable[[], WorkspaceConfig], reindex: Callable[[Path], list[KnowledgeChunk]], convert: Callable[[str, bytes, list[str] | None], str], inspect: Callable[[str, str], dict[str, object]], slug: Callable[[str, str], str], safe_segments: Callable[[tuple[str, ...]], str], max_files: int = 1000) -> APIRouter:
    router = APIRouter()

    @router.post("/api/workspace/import-native-folder/stream")
    async def import_native_folder_stream(request: Request) -> StreamingResponse:
        body: dict[str, object] = {}
        if "application/json" in request.headers.get("content-type", ""):
            try:
                raw_body = await request.json()
                if isinstance(raw_body, dict):
                    body = raw_body
            except ValueError:
                body = {}
        raw_source = str(body.get("source_path") or "").strip()
        subfolder, save_area, anonymize = str(body.get("subfolder") or ""), body.get("area"), body.get("anonymize")

        async def events() -> AsyncIterator[str]:
            queue: asyncio.Queue[str | None] = asyncio.Queue()
            cancel_event = threading.Event()
            loop = asyncio.get_running_loop()

            def emit(event: str, payload: dict[str, object]) -> None:
                if not cancel_event.is_set():
                    loop.call_soon_threadsafe(queue.put_nowait, _sse(event, payload))

            def worker() -> None:
                try:
                    if not raw_source:
                        emit("stage", {"stage": "picking", "message": "Choose a folder in the dialog…"})
                    picked = Path(raw_source).expanduser() if raw_source else pick_native_folder("Choose a folder to import into your Library")
                    if picked is None or cancel_event.is_set():
                        emit("cancelled", {"cancelled": True})
                        return
                    try:
                        resolved = validate_external_folder(picked, workspace.REPO_ROOT, action="import", allow_under_root=True)
                    except ValueError as exc:
                        emit("error", {"detail": str(exc)})
                        return
                    with workspace.STATE_LOCK:
                        active = config()
                        workspace.require_area(request, active)
                        area = active.knowledge_dir if not isinstance(save_area, str) or not save_area else save_area
                        if area not in active.active_dirs:
                            emit("error", {"detail": "Save to one of the selected areas"})
                            return
                        if is_linked_vault(area, workspace.REPO_ROOT):
                            emit("error", {"detail": "Linked folders are read-safe — import into a managed workspace instead."})
                            return
                        target = workspace.resolve_safe_knowledge_dir(area, create=True)
                        destination = folders.resolve_subfolder(target, subfolder, create=True)
                        dest_res = destination.resolve()
                        if dest_res.is_relative_to(resolved) or resolved.is_relative_to(dest_res):
                            emit("error", {"detail": "Cannot import a folder into itself or a nested subfolder"})
                            return
                        do_anon = active.anonymize_uploads if anonymize is None else bool(anonymize)
                    candidates, skipped = native_import_routes.walk_import_files(resolved, max_files)
                    total, imported, total_redacted = len(candidates), 0, 0
                    emit("start", {"folder_name": resolved.name, "total": total})
                    for idx, item in enumerate(candidates, 1):
                        if cancel_event.is_set():
                            return
                        rel = item.relative_to(resolved)
                        try:
                            if item.stat().st_size > upload_guard.MAX_UPLOAD_BYTES:
                                skipped += 1
                            else:
                                stem, _ = workspace.validate_upload_filename(item.name)
                                rel_sub = safe_segments((resolved.name, *rel.parts[:-1]))
                                item_dest = folders.resolve_subfolder(destination, rel_sub, create=True) if rel_sub else destination
                                raw, final_stem = item.read_bytes(), (slug(item.name, stem) if do_anon else stem)
                                text = convert(item.name, raw, workspace.auto_tags_for_filename(item.name))
                                report = AnonymizationReport.model_validate(inspect(text, item.name)) if do_anon else None
                                out_path = guide_edit_routes._unique_md_path(item_dest, final_stem) if (do_anon and final_stem != stem) else (item_dest / f"{final_stem}.md")
                                atomic_write_text(out_path, report.scrubbed_text if report else text)
                                imported += 1
                                total_redacted += report.total_redacted if report else 0
                        except (ValueError, OSError, BadZipFile, ParseError, PdfReadError, EOFError, KeyError):
                            skipped += 1
                        if idx == total or idx % max(1, total // 40) == 0 or total <= 40:
                            emit("progress", {"done": idx, "total": total, "imported": imported, "skipped": skipped, "current": rel.as_posix()})
                    if cancel_event.is_set():
                        return
                    if not imported:
                        emit("error", {"detail": "No supported documents found in this folder"})
                        return
                    emit("stage", {"stage": "indexing", "message": f"Building search index for {imported} guides…"})
                    with workspace.STATE_LOCK:
                        latest_active = config()
                        if area not in latest_active.active_dirs:
                            emit("error", {"detail": "Workspace changed during import. Select it and sync to view imported files."})
                            return
                        payload = {**workspace.build_workspace_payload(latest_active, reindex(target)), "cancelled": False, "folder_name": resolved.name, "imported_count": imported, "skipped_count": skipped, "redacted_count": total_redacted}
                    emit("done", payload)
                except HTTPException as exc:
                    emit("error", {"detail": str(exc.detail)})
                except ValueError as exc:
                    emit("error", {"detail": str(exc) or "Could not import folder"})
                except (TypeError, OSError):
                    emit("error", {"detail": "Could not import folder"})
                finally:
                    loop.call_soon_threadsafe(queue.put_nowait, None)

            fut = loop.run_in_executor(None, worker)
            try:
                while (chunk := await queue.get()) is not None:
                    if await request.is_disconnected():
                        cancel_event.set()
                        break
                    yield chunk
            finally:
                cancel_event.set()
                await fut

        return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})

    return router
