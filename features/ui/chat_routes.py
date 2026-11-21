"""Chat routes supporting vault chats, Free Chat, mid-chat vault attach, PDF export & Studio."""

import re
from collections.abc import AsyncIterator, Callable
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from core import agent_personas
from core.contracts import WorkspaceConfig
from core.pdf_export import render_chat_pdf, render_markdown_pdf
from features.ui import (
    chat_store,
    context_routes,
    format_routes,
    route_helpers,
    selection,
    workspace,
)

StreamMsgFn = Callable[..., AsyncIterator[dict[str, object]]]
_SLUG_RE = re.compile(r"[^a-zA-Z0-9_-]+")
def _logo_for_pdf() -> Path | None:
    return next((c for ext in (".png", ".jpg", ".jpeg") if (c := workspace.REPO_ROOT / f"custom_logo{ext}").is_file() and not c.is_symlink()), None)

def build_router(config: Callable[[], WorkspaceConfig], convert: Callable[[str, bytes, list[str] | None], str] | None = None, stream_messages: StreamMsgFn | None = None, inspect: Callable[[str, str], dict[str, object]] | None = None) -> APIRouter:
    router = APIRouter()
    @router.get("/api/chats")
    def list_chats(request: Request, free_chat: bool = False) -> list[dict[str, object]]:
        with workspace.STATE_LOCK:
            active = config()
            if free_chat or not active.active_dirs:
                return chat_store.list_chat_summaries(chat_store.area_chat_path(chat_store.FREE_CHAT_AREA)) if free_chat else []
            workspace.require_area(request, active)
            path = chat_store.area_chat_path(active.knowledge_dir)
            return [s for s in chat_store.list_chat_summaries(path) if s["area"] == active.knowledge_dir and s["active_dirs"] == active.active_dirs]
    @router.get("/api/chats/{chat_id}")
    def get_chat(chat_id: str, request: Request, free_chat: bool = False) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            if free_chat:
                if (session := chat_store.get_chat_session(chat_id, chat_store.area_chat_path(chat_store.FREE_CHAT_AREA))) is None:
                    raise HTTPException(status_code=404, detail="Free chat session not found")
                return session.model_dump()
            workspace.require_area(request, active)
            session = chat_store.get_chat_session(chat_id, chat_store.area_chat_path(active.knowledge_dir)) if active.active_dirs else None
            if session is None or not selection.chat_matches(session, active):
                raise HTTPException(status_code=404, detail="Chat session not found in this knowledge area")
            return session.model_dump()
    @router.delete("/api/chats/{chat_id}")
    def delete_chat(chat_id: str, request: Request, free_chat: bool = False) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            if free_chat:
                return {"chat_id": chat_id, "deleted": chat_store.delete_chat_session(chat_id, chat_store.area_chat_path(chat_store.FREE_CHAT_AREA))}
            workspace.require_area(request, active)
            if not active.active_dirs:
                return {"chat_id": chat_id, "deleted": False}
            path = chat_store.area_chat_path(active.knowledge_dir)
            session = chat_store.get_chat_session(chat_id, path)
            if session and not selection.chat_matches(session, active):
                raise HTTPException(status_code=404, detail="Chat not found in this knowledge area")
            return {"chat_id": chat_id, "deleted": chat_store.delete_chat_session(chat_id, path)}

    @router.post("/api/chats/{chat_id}/agent")
    async def set_chat_agent(chat_id: str, request: Request) -> dict[str, object]:
        body = await route_helpers.read_json_dict(request)
        if not (chosen_id := str(body.get("agent_id") or "").strip()):
            raise HTTPException(status_code=400, detail="Provide agent_id")
        free_chat = bool(body.get("free_chat"))

        def _apply() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                if not free_chat:
                    workspace.require_area(request, active)
                agent = agent_personas.get_agent(workspace.REPO_ROOT, chosen_id, active.agent_name)
                if not free_chat and not active.active_dirs:
                    raise HTTPException(status_code=404, detail="Chat session not found")
                path = chat_store.area_chat_path(chat_store.FREE_CHAT_AREA if free_chat else active.knowledge_dir)
                session = chat_store.get_chat_session(chat_id, path)
                if session is None or (not free_chat and not selection.chat_matches(session, active)):
                    raise HTTPException(status_code=404, detail="Chat session not found")
                updated = chat_store.save_chat_session(session.model_copy(update={"last_agent_id": agent.id}), path)
                return {"chat_id": updated.chat_id, "last_agent_id": updated.last_agent_id, "agent_name": agent.name}

        return await run_in_threadpool(_apply)

    @router.post("/api/chats/{chat_id}/attach-vault")
    async def attach_vault_to_chat(chat_id: str, request: Request) -> dict[str, object]:
        target_area = str((await route_helpers.read_json_dict(request, required=False)).get("area") or "").strip()

        def _migrate() -> dict[str, object]:
            with workspace.STATE_LOCK:
                dest_area = target_area or config().knowledge_dir
                workspace.resolve_safe_knowledge_dir(dest_area)
                src_path = chat_store.area_chat_path(chat_store.FREE_CHAT_AREA)
                session = chat_store.get_chat_session(chat_id, src_path)
                if session is None:
                    raise HTTPException(status_code=404, detail="Free chat session not found")
                migrated = session.model_copy(update={"area": dest_area, "active_dirs": [dest_area], "free_chat": False, "updated_at": chat_store.utc_now_iso()})
                chat_store.save_chat_session(migrated, chat_store.area_chat_path(dest_area))
                chat_store.delete_chat_session(chat_id, src_path)
                return {"session": migrated.model_dump(), "area": dest_area}

        return await run_in_threadpool(_migrate)

    @router.post("/api/export/pdf")
    async def export_pdf(request: Request) -> Response:
        body = await route_helpers.read_json_dict(request)
        logo, chat_id = _logo_for_pdf(), str(body.get("chat_id") or "").strip()

        def _render() -> tuple[str, bytes]:
            if chat_id:
                free_chat, turn_index = bool(body.get("free_chat")), body.get("turn_index")
                with workspace.STATE_LOCK:
                    active = config()
                    if not free_chat:
                        workspace.require_area(request, active)
                        if not active.active_dirs:
                            raise HTTPException(status_code=404, detail="Chat session not found")
                    area = chat_store.FREE_CHAT_AREA if free_chat else active.knowledge_dir
                    session = chat_store.get_chat_session(chat_id, chat_store.area_chat_path(area))
                    if session is None or (not free_chat and not selection.chat_matches(session, active)):
                        raise HTTPException(status_code=404, detail="Chat session not found")
                if isinstance(turn_index, int) and 0 <= turn_index < len(session.turns):
                    t = session.turns[turn_index]
                    title = t.format_name or t.query[:70] or session.title
                    sub = f"{t.agent_name} · {t.created_at[:10]}" if t.agent_name else t.created_at[:10]
                    return title, render_markdown_pdf(title, t.tutor.answer if t.tutor else t.query, subtitle=sub, citations=t.tutor.cited_titles if t.tutor else [], logo_path=logo)
                return session.title or "conversation", render_chat_pdf(session, logo_path=logo)
            title, md = str(body.get("title") or "REALM Document").strip(), str(body.get("markdown") or "").strip()
            if not md:
                raise HTTPException(status_code=400, detail="Provide chat_id or markdown content")
            raw_cites = body.get("citations")
            return title, render_markdown_pdf(title, md, citations=[str(c) for c in raw_cites] if isinstance(raw_cites, list) else [], logo_path=logo)

        title, pdf_bytes = await run_in_threadpool(_render)
        safe = _SLUG_RE.sub("-", title.lower()).strip("-")[:60] or "realm-export"
        return Response(pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{safe}.pdf"', "Cache-Control": "no-store"})

    router.include_router(format_routes.build_router(config, convert, inspect))
    router.include_router(context_routes.build_router(config, stream_messages))
    return router
