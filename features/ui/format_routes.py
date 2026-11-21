"""Routes for Output Formats Studio and mid-chat file/note attachments."""

import re
from collections.abc import Callable
from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from pypdf.errors import PdfReadError
from starlette.datastructures import UploadFile

from core.context_meter import compute_context_usage
from core.contracts import ChatSession, WorkspaceConfig
from core.output_formats import delete_custom_format, list_formats, save_custom_format
from features.ui import chat_store, selection, upload_guard, workspace

_CHAT_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,80}$")


def _validate_chat_id(chat_id: str) -> str:
    if not _CHAT_ID_RE.fullmatch(chat_id):
        raise HTTPException(status_code=400, detail="Invalid chat identifier")
    return chat_id


def build_router(config: Callable[[], WorkspaceConfig], convert: Callable[[str, bytes, list[str] | None], str] | None = None, inspect: Callable[[str, str], dict[str, object]] | None = None) -> APIRouter:
    router = APIRouter()

    @router.get("/api/formats")
    def get_formats() -> dict[str, object]:
        return {"formats": [f.model_dump() for f in list_formats(workspace.REPO_ROOT)]}

    @router.post("/api/formats")
    async def upsert_format(request: Request) -> dict[str, object]:
        try:
            body = await request.json()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Provide a JSON object") from exc
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="Provide a JSON object")
        raw_sections = body.get("sections")
        sections = [s.strip() for s in re.split(r"[\n,;]+", raw_sections) if s.strip()] if isinstance(raw_sections, str) else ([str(s).strip() for s in raw_sections if str(s).strip()] if isinstance(raw_sections, list) else [])

        def _save() -> dict[str, object]:
            with workspace.STATE_LOCK:
                try:
                    saved = save_custom_format(workspace.REPO_ROOT, name=str(body.get("name") or ""), sections=sections, category=str(body.get("category") or "Custom"), description=str(body.get("description") or ""), instructions=str(body.get("instructions") or ""), format_id=str(body.get("id") or ""))
                except ValueError as exc:
                    raise HTTPException(status_code=400, detail=str(exc)) from exc
                except OSError as exc:
                    raise HTTPException(status_code=500, detail="Could not save custom output format") from exc
                return {"format": saved.model_dump(), "formats": [f.model_dump() for f in list_formats(workspace.REPO_ROOT)]}

        return await run_in_threadpool(_save)

    @router.delete("/api/formats/{format_id}")
    def remove_format(format_id: str) -> dict[str, object]:
        with workspace.STATE_LOCK:
            try:
                deleted = delete_custom_format(workspace.REPO_ROOT, format_id)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except OSError as exc:
                raise HTTPException(status_code=500, detail="Could not delete custom output format") from exc
            return {"deleted": deleted, "formats": [f.model_dump() for f in list_formats(workspace.REPO_ROOT)]}

    @router.post("/api/chats/{chat_id}/attach")
    async def attach_to_chat(chat_id: str, request: Request) -> dict[str, object]:
        _validate_chat_id(chat_id)
        ctype, free_chat, raw_items, text_items = request.headers.get("content-type", ""), False, [], []
        if "application/json" in ctype:
            try:
                body = await request.json()
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Provide a JSON object") from exc
            if not isinstance(body, dict):
                raise HTTPException(status_code=400, detail="Provide a JSON object")
            free_chat = bool(body.get("free_chat"))
            name, content = str(body.get("name") or "Attached Note").strip()[:120], str(body.get("content") or "").strip()[:30_000]
            if not content:
                raise HTTPException(status_code=400, detail="Provide note content to attach")
            text_items.append((name, content))
        else:
            form = await request.form()
            try:
                free_chat = str(form.get("free_chat") or "").lower() == "true"
                uploads = [v for v in form.getlist("files") if isinstance(v, UploadFile)]
                if not uploads and isinstance(single := form.get("file"), UploadFile):
                    uploads = [single]
                if not uploads:
                    raise HTTPException(status_code=400, detail="Select at least one file to attach")
                for up in uploads[:6]:
                    raw_items.append((Path(up.filename or "note.txt").name, await upload_guard.read_file(up)))
            finally:
                await form.close()

        def _apply() -> dict[str, object]:
            raw_notes = list(text_items)
            for fname, raw in raw_items:
                try:
                    text = convert(fname, raw, []) if convert else raw.decode("utf-8", errors="replace")
                except (ValueError, BadZipFile, ParseError, PdfReadError, OSError) as exc:
                    raise HTTPException(status_code=400, detail=f"Could not extract text from {fname}") from exc
                raw_notes.append((fname, text[:30_000]))
            with workspace.STATE_LOCK:
                active = config()
                if not free_chat:
                    workspace.require_area(request, active)
                    if not active.active_dirs:
                        raise HTTPException(status_code=400, detail="Create or link a workspace first, or use Free Chat.")
                area = chat_store.FREE_CHAT_AREA if free_chat else active.knowledge_dir
                dirs = [chat_store.FREE_CHAT_AREA] if free_chat else active.active_dirs
                path = chat_store.area_chat_path(area)
                existing = chat_store.get_chat_session(chat_id, path)
                if not free_chat and existing and not selection.chat_matches(existing, active):
                    raise HTTPException(status_code=404, detail="Chat does not belong to this area")
                new_notes = [{"name": fn, "content": (str(inspect(txt, fn)["scrubbed_text"]) if (active.anonymize_uploads and inspect is not None) else txt)[:30_000]} for fn, txt in raw_notes]
                if existing is None:
                    existing = ChatSession(chat_id=chat_id, title=new_notes[0]["name"][:60], updated_at=chat_store.utc_now_iso(), area=area, active_dirs=dirs, free_chat=free_chat)
                updated = chat_store.save_chat_session(existing.model_copy(update={"attached_notes": [*existing.attached_notes, *new_notes][-8:], "updated_at": chat_store.utc_now_iso()}), path)
            return {"chat_id": chat_id, "attached_notes": [{"name": n["name"], "chars": len(n["content"])} for n in updated.attached_notes], "context_usage": compute_context_usage(updated)}

        return await run_in_threadpool(_apply)

    @router.delete("/api/chats/{chat_id}/attach/{note_index}")
    def detach_from_chat(chat_id: str, note_index: int, request: Request, free_chat: bool = False) -> dict[str, object]:
        _validate_chat_id(chat_id)
        with workspace.STATE_LOCK:
            active = config()
            if not free_chat:
                workspace.require_area(request, active)
                if not active.active_dirs:
                    raise HTTPException(status_code=404, detail="Attached note not found")
            area = chat_store.FREE_CHAT_AREA if free_chat else active.knowledge_dir
            path = chat_store.area_chat_path(area)
            existing = chat_store.get_chat_session(chat_id, path)
            if existing is None or (not free_chat and not selection.chat_matches(existing, active)) or note_index < 0 or note_index >= len(existing.attached_notes):
                raise HTTPException(status_code=404, detail="Attached note not found")
            remaining = [n for i, n in enumerate(existing.attached_notes) if i != note_index]
            updated = chat_store.save_chat_session(existing.model_copy(update={"attached_notes": remaining}), path)
        return {"chat_id": chat_id, "attached_notes": [{"name": n["name"], "chars": len(n["content"])} for n in updated.attached_notes], "context_usage": compute_context_usage(updated)}

    return router
