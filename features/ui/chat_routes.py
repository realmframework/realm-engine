"""Chat routes scoped to a captured active knowledge area."""

from collections.abc import Callable

from fastapi import APIRouter, HTTPException, Request

from core.contracts import WorkspaceConfig
from features.ui import chat_store, selection, workspace


def build_router(config: Callable[[], WorkspaceConfig]) -> APIRouter:
    router = APIRouter()

    @router.get("/api/chats")
    def list_chats(request: Request) -> list[dict[str, object]]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            path = chat_store.area_chat_path(active.knowledge_dir)
            return [s for s in chat_store.list_chat_summaries(path) if s["area"] == active.knowledge_dir and s["active_dirs"] == active.active_dirs]

    @router.get("/api/chats/{chat_id}")
    def get_chat(chat_id: str, request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            session = chat_store.get_chat_session(chat_id, chat_store.area_chat_path(active.knowledge_dir))
            if session is None or not selection.chat_matches(session, active):
                raise HTTPException(status_code=404, detail="Chat session not found in this knowledge area")
            return session.model_dump()

    @router.delete("/api/chats/{chat_id}")
    def delete_chat(chat_id: str, request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            path = chat_store.area_chat_path(active.knowledge_dir)
            session = chat_store.get_chat_session(chat_id, path)
            if session and not selection.chat_matches(session, active):
                raise HTTPException(status_code=404, detail="Chat not found in this knowledge area")
            return {"chat_id": chat_id, "deleted": chat_store.delete_chat_session(chat_id, path)}

    return router
