"""Phase 3 routes: Chat Branching (Fork from Turn) and Contradiction / Knowledge-Gap Scan."""

import uuid
from collections.abc import Callable

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from core.contracts import KnowledgeChunk, WorkspaceConfig
from core.file_watcher import get_sync_status
from core.vault_analysis import analyze_workspace_gaps
from features.ui import chat_store, selection, workspace


def build_router(
    config: Callable[[], WorkspaceConfig],
    chunks: Callable[[], list[KnowledgeChunk]],
) -> APIRouter:
    router = APIRouter()

    @router.post("/api/chats/{chat_id}/fork")
    async def fork_chat(chat_id: str, request: Request) -> dict[str, object]:
        body: dict[str, object] = {}
        if "application/json" in request.headers.get("content-type", ""):
            try:
                raw = await request.json()
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Provide valid JSON") from exc
            if isinstance(raw, dict):
                body = raw
        raw_idx, free_chat = body.get("turn_index"), bool(body.get("free_chat"))

        def _apply() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                if not free_chat:
                    workspace.require_area(request, active)
                    if not active.active_dirs:
                        raise HTTPException(status_code=400, detail="Create or link a workspace first, or use Free Chat.")
                area = chat_store.FREE_CHAT_AREA if free_chat else active.knowledge_dir
                path = chat_store.area_chat_path(area)
                session = chat_store.get_chat_session(chat_id, path)
                if session is None or (not free_chat and not selection.chat_matches(session, active)):
                    raise HTTPException(status_code=404, detail="Chat session not found")
                if not session.turns:
                    raise HTTPException(status_code=400, detail="Cannot fork an empty chat")
                try:
                    idx = len(session.turns) - 1 if raw_idx is None else int(str(raw_idx))
                except (ValueError, TypeError) as exc:
                    raise HTTPException(status_code=400, detail="Invalid turn index for fork") from exc
                if idx < 0 or idx >= len(session.turns):
                    raise HTTPException(status_code=400, detail="Invalid turn index for fork")
                sliced = list(session.turns[: idx + 1])
                cleared_at = min(session.context_cleared_at, len(sliced))
                summary = session.compacted_summary if (session.context_cleared_at <= len(sliced) and idx >= session.context_cleared_at) else ""
                base_title = session.title.removesuffix(" (Branch)").strip() or "Chat"
                last_agent = next((t.agent_id for t in reversed(sliced) if t.agent_id), session.last_agent_id)
                forked = session.model_copy(
                    update={
                        "chat_id": f"chat-{uuid.uuid4().hex[:8]}",
                        "title": f"{base_title[:48]} (Branch)",
                        "updated_at": chat_store.utc_now_iso(),
                        "turns": sliced,
                        "last_agent_id": last_agent,
                        "context_cleared_at": cleared_at,
                        "compacted_summary": summary,
                    }
                )
                chat_store.save_chat_session(forked, path)
                return {"session": forked.model_dump(), "forked_from": chat_id, "turn_index": idx}

        return await run_in_threadpool(_apply)

    @router.post("/api/workspace/analyze-gaps")
    def analyze_gaps(request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            if not active.active_dirs:
                raise HTTPException(status_code=400, detail="Create or link a workspace before running a gap scan.")
            cur_chunks = list(chunks())
        report = analyze_workspace_gaps(cur_chunks)
        return {"area": active.knowledge_dir, "active_dirs": list(active.active_dirs), **report}

    @router.get("/api/workspace/sync-status")
    def sync_status() -> dict[str, object]:
        return get_sync_status()

    return router
