"""Routes for Output Formats Studio and mid-chat file/note attachments."""

import re
from collections.abc import Callable
from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from fastapi import APIRouter, HTTPException, Request
from pypdf.errors import PdfReadError
from starlette.datastructures import UploadFile

from core.context_meter import compute_context_usage
from core.contracts import ChatSession, WorkspaceConfig
from core.output_formats import delete_custom_format, list_formats, save_custom_format
from features.ui import chat_store, upload_guard, workspace


def build_router(
    config: Callable[[], WorkspaceConfig],
    convert: Callable[[str, bytes, list[str] | None], str] | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/formats")
    def get_formats() -> dict[str, object]:
        return {"formats": [f.model_dump() for f in list_formats(workspace.REPO_ROOT)]}

    @router.post("/api/formats")
    async def upsert_format(request: Request) -> dict[str, object]:
        body = await request.json()
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="Provide a JSON object")
        raw_sections = body.get("sections")
        if isinstance(raw_sections, str):
            sections = [s.strip() for s in re.split(r"[\n,;]+", raw_sections) if s.strip()]
        elif isinstance(raw_sections, list):
            sections = [str(s).strip() for s in raw_sections if str(s).strip()]
        else:
            sections = []
        try:
            saved = save_custom_format(
                workspace.REPO_ROOT,
                name=str(body.get("name") or ""),
                sections=sections,
                category=str(body.get("category") or "Custom"),
                description=str(body.get("description") or ""),
                instructions=str(body.get("instructions") or ""),
                format_id=str(body.get("id") or ""),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"format": saved.model_dump(), "formats": [f.model_dump() for f in list_formats(workspace.REPO_ROOT)]}

    @router.delete("/api/formats/{format_id}")
    def remove_format(format_id: str) -> dict[str, object]:
        try:
            deleted = delete_custom_format(workspace.REPO_ROOT, format_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"deleted": deleted, "formats": [f.model_dump() for f in list_formats(workspace.REPO_ROOT)]}

    @router.post("/api/chats/{chat_id}/attach")
    async def attach_to_chat(chat_id: str, request: Request) -> dict[str, object]:
        ctype, free_chat, new_notes = request.headers.get("content-type", ""), False, []
        if "application/json" in ctype:
            body = await request.json()
            if not isinstance(body, dict):
                raise HTTPException(status_code=400, detail="Provide a JSON object")
            free_chat = bool(body.get("free_chat"))
            name = str(body.get("name") or "Attached Note").strip()[:120]
            content = str(body.get("content") or "").strip()[:30_000]
            if not content:
                raise HTTPException(status_code=400, detail="Provide note content to attach")
            new_notes.append({"name": name, "content": content})
        else:
            form = await request.form()
            try:
                free_chat = str(form.get("free_chat") or "").lower() == "true"
                uploads = [v for v in form.getlist("files") if isinstance(v, UploadFile)]
                single = form.get("file")
                if not uploads and isinstance(single, UploadFile):
                    uploads = [single]
                if not uploads:
                    raise HTTPException(status_code=400, detail="Select at least one file to attach")
                for up in uploads[:6]:
                    raw = await upload_guard.read_file(up)
                    fname = Path(up.filename or "note.txt").name
                    try:
                        text = convert(fname, raw, []) if convert else raw.decode("utf-8", errors="replace")
                    except (ValueError, BadZipFile, ParseError, PdfReadError, OSError) as exc:
                        raise HTTPException(status_code=400, detail=f"Could not extract text from {fname}") from exc
                    new_notes.append({"name": fname, "content": text[:30_000]})
            finally:
                await form.close()
        with workspace.STATE_LOCK:
            active = config()
            area = chat_store.FREE_CHAT_AREA if free_chat else active.knowledge_dir
            dirs = [chat_store.FREE_CHAT_AREA] if free_chat else active.active_dirs
            path = chat_store.area_chat_path(area)
            existing = chat_store.get_chat_session(chat_id, path)
            if existing is None:
                existing = ChatSession(chat_id=chat_id, title=new_notes[0]["name"][:60], updated_at=chat_store.utc_now_iso(), area=area, active_dirs=dirs, free_chat=free_chat)
            merged = [*existing.attached_notes, *new_notes][-8:]
            updated = chat_store.save_chat_session(existing.model_copy(update={"attached_notes": merged, "updated_at": chat_store.utc_now_iso()}), path)
            return {"chat_id": chat_id, "attached_notes": [{"name": n["name"], "chars": len(n["content"])} for n in updated.attached_notes], "context_usage": compute_context_usage(updated)}

    @router.delete("/api/chats/{chat_id}/attach/{note_index}")
    def detach_from_chat(chat_id: str, note_index: int, free_chat: bool = False) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            area = chat_store.FREE_CHAT_AREA if free_chat else active.knowledge_dir
            path = chat_store.area_chat_path(area)
            existing = chat_store.get_chat_session(chat_id, path)
            if existing is None or note_index < 0 or note_index >= len(existing.attached_notes):
                raise HTTPException(status_code=404, detail="Attached note not found")
            remaining = [n for i, n in enumerate(existing.attached_notes) if i != note_index]
            updated = chat_store.save_chat_session(existing.model_copy(update={"attached_notes": remaining}), path)
            return {"chat_id": chat_id, "attached_notes": [{"name": n["name"], "chars": len(n["content"])} for n in updated.attached_notes], "context_usage": compute_context_usage(updated)}

    return router
