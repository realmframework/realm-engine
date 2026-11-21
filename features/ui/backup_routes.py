"""Download and restore the selected workspace without extracting arbitrary archive paths."""

import json
import zipfile
from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from starlette.datastructures import UploadFile

from core.contracts import WorkspaceConfig
from features.ui import chat_store, folders, workspace
from features.ui.backup_apply import apply_restore
from features.ui.backup_archive import (
    MAX_ARCHIVE_BYTES,
    MAX_MEMBERS,
    bounded_bytes,
    make_archive,
    read_archive,
)
from features.ui.backup_state import current_chats


def _portable_chat_dump(chat: object) -> dict[str, object]:
    """Strip absolute host paths and vector floats from exported chat turns."""
    raw = chat.model_dump() if hasattr(chat, "model_dump") else {}  # type: ignore[attr-defined]
    for turn in raw.get("turns", []):
        if isinstance(turn, dict):
            for res in turn.get("results", []):
                if isinstance(res, dict) and isinstance((chunk := res.get("chunk")), dict):
                    chunk["embedding"] = None
                    doc_id = str(chunk.get("doc_id") or "")
                    chunk["file_path"] = f"{doc_id}.md" if doc_id else ""
    return raw


def build_router(config: Callable[[], WorkspaceConfig], activate: Callable[[WorkspaceConfig], dict[str, object]]) -> APIRouter:
    router = APIRouter()

    @router.get("/api/backup/export")
    def export_backup(request: Request) -> Response:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            if not active.knowledge_dir:
                raise HTTPException(status_code=400, detail="Create or link a workspace before exporting a backup.")
            target = workspace.resolve_safe_knowledge_dir(active.knowledge_dir)
            try:
                scoped_excl = {active.knowledge_dir: list(active.excluded_subfolders[active.knowledge_dir])} if active.knowledge_dir in active.excluded_subfolders else {}
                portable = active.model_copy(update={"active_dirs": [active.knowledge_dir], "excluded_subfolders": scoped_excl, "searxng_url": "", "enable_local_api": False})
                entries = {"workspace.json": portable.model_dump_json(indent=2).encode(), "chats.json": json.dumps([_portable_chat_dump(c) for c in current_chats(chat_store.area_chat_path(active.knowledge_dir)) if c.area == active.knowledge_dir and (c.active_dirs or [c.area]) == [active.knowledge_dir]]).encode()}
                total = sum(map(len, entries.values()))
                for path in target.rglob("*"):
                    if path.is_symlink() or any(part.startswith(".") for part in path.relative_to(target).parts):
                        continue
                    if not path.is_dir() and (not path.is_file() or path.suffix.lower() != ".md"):
                        continue
                    name = path.relative_to(target).as_posix()
                    try:
                        folders.contained_path(target, name)
                    except ValueError:
                        continue
                    entries[name + "/" if path.is_dir() else name] = b"" if path.is_dir() else bounded_bytes(path)
                    total += len(entries[name + "/" if path.is_dir() else name])
                    if total > MAX_ARCHIVE_BYTES or len(entries) > MAX_MEMBERS:
                        raise HTTPException(status_code=413, detail="Workspace exceeds the 64 MiB or 2,048-item backup limit.")
                raw = make_archive(entries)
            except (ValueError, TypeError, OSError) as exc:
                raise HTTPException(status_code=400, detail="Backup could not be read safely. Check workspace files and try again.") from exc
            filename = f"{active.knowledge_dir}_backup_{datetime.now(UTC):%Y-%m-%d}.zip"
            return Response(raw, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "no-store"})

    def restore(raw: bytes, request: Request, area: str) -> dict[str, object]:
        try:
            entries = read_archive(raw)
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                if area != active.knowledge_dir:
                    raise HTTPException(status_code=409, detail="Workspace changed. Select it again before restoring.")
                return apply_restore(entries, active, activate)
        except (ValueError, TypeError, OSError, zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
            raise HTTPException(status_code=400, detail="Backup could not be restored safely. Use a valid ZIP with relative paths and UTF-8 Markdown.") from exc

    @router.post("/api/backup/import")
    async def import_backup(request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            if not active.knowledge_dir:
                raise HTTPException(status_code=400, detail="Create or link a workspace before restoring a backup.")
            area = active.knowledge_dir
        form = await request.form()
        try:
            file = form.get("file")
            if not isinstance(file, UploadFile) or not (file.filename or "").lower().endswith(".zip"):
                raise HTTPException(status_code=400, detail="Choose a .zip backup file.")
            if file.size is not None and file.size > MAX_ARCHIVE_BYTES:
                raise HTTPException(status_code=413, detail="Backup ZIP must be 64 MiB or smaller.")
            raw = await file.read(MAX_ARCHIVE_BYTES + 1)
        finally:
            await form.close()
        return await run_in_threadpool(restore, raw, request, area)

    return router
