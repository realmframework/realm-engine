"""Chat routes supporting vault chats, Free Chat, mid-chat vault attach, PDF export & Studio."""

import re
from collections.abc import AsyncIterator, Callable
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from core.contracts import WorkspaceConfig
from core.pdf_export import render_chat_pdf, render_markdown_pdf
from core.runtime import bundle_root
from features.ui import chat_store, context_routes, format_routes, selection, workspace

StreamMsgFn = Callable[..., AsyncIterator[dict[str, object]]]
_SLUG_RE = re.compile(r"[^a-zA-Z0-9_-]+")


def _logo_for_pdf() -> Path | None:
    for ext in (".png", ".jpg", ".jpeg"):
        custom = workspace.REPO_ROOT / f"custom_logo{ext}"
        if custom.is_file() and not custom.is_symlink():
            return custom
    default_logo = bundle_root() / "features" / "ui" / "static" / "logo-192.png"
    return default_logo if default_logo.is_file() else None


def build_router(
    config: Callable[[], WorkspaceConfig],
    convert: Callable[[str, bytes, list[str] | None], str] | None = None,
    stream_messages: StreamMsgFn | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/chats")
    def list_chats(request: Request, free_chat: bool = False) -> list[dict[str, object]]:
        with workspace.STATE_LOCK:
            active = config()
            if free_chat:
                return chat_store.list_chat_summaries(chat_store.area_chat_path(chat_store.FREE_CHAT_AREA))
            workspace.require_area(request, active)
            path = chat_store.area_chat_path(active.knowledge_dir)
            return [s for s in chat_store.list_chat_summaries(path) if s["area"] == active.knowledge_dir and s["active_dirs"] == active.active_dirs]

    @router.get("/api/chats/{chat_id}")
    def get_chat(chat_id: str, request: Request, free_chat: bool = False) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            if free_chat:
                session = chat_store.get_chat_session(chat_id, chat_store.area_chat_path(chat_store.FREE_CHAT_AREA))
                if session is None:
                    raise HTTPException(status_code=404, detail="Free chat session not found")
                return session.model_dump()
            workspace.require_area(request, active)
            session = chat_store.get_chat_session(chat_id, chat_store.area_chat_path(active.knowledge_dir))
            if session is None or not selection.chat_matches(session, active):
                raise HTTPException(status_code=404, detail="Chat session not found in this knowledge area")
            return session.model_dump()

    @router.delete("/api/chats/{chat_id}")
    def delete_chat(chat_id: str, request: Request, free_chat: bool = False) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            if free_chat:
                path = chat_store.area_chat_path(chat_store.FREE_CHAT_AREA)
                return {"chat_id": chat_id, "deleted": chat_store.delete_chat_session(chat_id, path)}
            workspace.require_area(request, active)
            path = chat_store.area_chat_path(active.knowledge_dir)
            session = chat_store.get_chat_session(chat_id, path)
            if session and not selection.chat_matches(session, active):
                raise HTTPException(status_code=404, detail="Chat not found in this knowledge area")
            return {"chat_id": chat_id, "deleted": chat_store.delete_chat_session(chat_id, path)}

    @router.post("/api/chats/{chat_id}/attach-vault")
    async def attach_vault_to_chat(chat_id: str, request: Request) -> dict[str, object]:
        """Move an open Free Chat into a chosen vault so the user can continue chatting with RAG."""
        body = await request.json() if "application/json" in request.headers.get("content-type", "") else {}
        target_area = str(body.get("area") or "").strip() if isinstance(body, dict) else ""
        with workspace.STATE_LOCK:
            active = config()
            dest_area = target_area or active.knowledge_dir
            workspace.resolve_safe_knowledge_dir(dest_area)
            src_path = chat_store.area_chat_path(chat_store.FREE_CHAT_AREA)
            session = chat_store.get_chat_session(chat_id, src_path)
            if session is None:
                raise HTTPException(status_code=404, detail="Free chat session not found")
            migrated = session.model_copy(update={"area": dest_area, "active_dirs": [dest_area], "free_chat": False, "updated_at": chat_store.utc_now_iso()})
            chat_store.save_chat_session(migrated, chat_store.area_chat_path(dest_area))
            chat_store.delete_chat_session(chat_id, src_path)
            return {"session": migrated.model_dump(), "area": dest_area}

    @router.post("/api/export/pdf")
    async def export_pdf(request: Request) -> Response:
        body = await request.json()
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="Provide a JSON object")
        logo, chat_id = _logo_for_pdf(), str(body.get("chat_id") or "").strip()
        if chat_id:
            free_chat, turn_index = bool(body.get("free_chat")), body.get("turn_index")
            with workspace.STATE_LOCK:
                area = chat_store.FREE_CHAT_AREA if free_chat else config().knowledge_dir
                session = chat_store.get_chat_session(chat_id, chat_store.area_chat_path(area))
            if session is None:
                raise HTTPException(status_code=404, detail="Chat session not found")
            if isinstance(turn_index, int) and 0 <= turn_index < len(session.turns):
                t = session.turns[turn_index]
                title = t.format_name or t.query[:70] or session.title
                pdf_bytes = render_markdown_pdf(title, t.tutor.answer if t.tutor else t.query, subtitle=f"REALM Engine · {t.created_at[:16].replace('T', ' ')}", citations=t.tutor.cited_titles if t.tutor else [], logo_path=logo)
            else:
                title, pdf_bytes = session.title or "conversation", render_chat_pdf(session, logo_path=logo)
        else:
            title, md = str(body.get("title") or "REALM Document").strip(), str(body.get("markdown") or "").strip()
            if not md:
                raise HTTPException(status_code=400, detail="Provide chat_id or markdown content")
            raw_cites = body.get("citations")
            pdf_bytes = render_markdown_pdf(title, md, citations=[str(c) for c in raw_cites] if isinstance(raw_cites, list) else [], logo_path=logo)
        safe = _SLUG_RE.sub("-", title.lower()).strip("-")[:60] or "realm-export"
        return Response(pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{safe}.pdf"', "Cache-Control": "no-store"})

    router.include_router(format_routes.build_router(config, convert))
    router.include_router(context_routes.build_router(config, stream_messages))
    return router
