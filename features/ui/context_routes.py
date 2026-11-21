"""Routes for Context Meter, Context Compaction, Clear Context & Format Synthesis."""

from collections.abc import AsyncIterator, Callable
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from core import context_meter, contracts
from core.agent_personas import active_persona_prompt
from features.ui import (
    chat_store,
    route_helpers,
    selection,
    synthesize_routes,
    workspace,
)
from features.ui.privacy import require_local

StreamMsgFn = Callable[..., AsyncIterator[dict[str, object]]]


def build_router(config: Callable[[], contracts.WorkspaceConfig], stream_messages: StreamMsgFn | None = None) -> APIRouter:
    router = APIRouter()

    @router.get("/api/chats/{chat_id}/context")
    def get_context(chat_id: str, request: Request, provider: str = "ollama", model: str = "qwen3:8b", free_chat: bool = False, agent_id: str | None = None) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            area, _ = synthesize_routes.resolve_chat_target(request, active, free_chat, allow_empty=True)
            session = chat_store.get_chat_session(chat_id, chat_store.area_chat_path(area)) if area else None
            if not free_chat and session and not selection.chat_matches(session, active):
                raise HTTPException(status_code=404, detail="Chat does not belong to this area")
            _, persona_instr = active_persona_prompt(workspace.REPO_ROOT, agent_id or (session.last_agent_id if session and session.last_agent_id else active.active_agent), active.agent_name)
            notes = [{"name": n["name"], "chars": len(n["content"])} for n in session.attached_notes] if session else []
            summary_str = session.compacted_summary if session else ""
        return {"context_usage": context_meter.compute_context_usage(session, provider, model, persona_tokens=context_meter.approx_tokens(persona_instr)), "attached_notes": notes, "compacted_summary": summary_str}

    @router.post("/api/chats/{chat_id}/clear-context")
    async def clear_context(chat_id: str, request: Request) -> dict[str, object]:
        body = await route_helpers.read_json_dict(request, required=False)
        free_chat, provider, model = bool(body.get("free_chat")), str(body.get("provider") or "ollama"), str(body.get("model") or "qwen3:8b")

        def _apply() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                area, _ = synthesize_routes.resolve_chat_target(request, active, free_chat)
                path = chat_store.area_chat_path(area)
                session = chat_store.get_chat_session(chat_id, path)
                if session is None or (not free_chat and not selection.chat_matches(session, active)):
                    raise HTTPException(status_code=404, detail="Chat session not found")
                updated = chat_store.save_chat_session(session.model_copy(update={"compacted_summary": "", "context_cleared_at": len(session.turns)}), path)
            return {"session": updated.model_dump(), "context_usage": context_meter.compute_context_usage(updated, provider, model)}

        return await run_in_threadpool(_apply)

    @router.post("/api/chats/{chat_id}/compact")
    async def compact_context(chat_id: str, request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, object]:
        body = await route_helpers.read_json_dict(request, required=False)
        free_chat, provider, model = bool(body.get("free_chat")), str(body.get("provider") or "ollama"), str(body.get("model") or "qwen3:8b")
        api_key = x_api_key or str(body.get("api_key") or "")

        def _prep() -> tuple[Path, contracts.ChatSession, list[dict[str, str]], contracts.TutorConfig, contracts.WorkspaceConfig]:
            with workspace.STATE_LOCK:
                active = config()
                require_local(active, provider, model)
                area, _ = synthesize_routes.resolve_chat_target(request, active, free_chat)
                path = chat_store.area_chat_path(area)
                session = chat_store.get_chat_session(chat_id, path)
                if session is None or (not free_chat and not selection.chat_matches(session, active)):
                    raise HTTPException(status_code=404, detail="Chat session not found")
                if not session.turns:
                    raise HTTPException(status_code=400, detail="Nothing to compress yet in this chat.")
                t_cfg = workspace.build_tutor_config(provider, model, api_key or None, 0.1).model_copy(update={"daily_cloud_request_limit": active.daily_cloud_request_limit, "daily_budget_usd_limit": active.daily_budget_usd_limit, "response_language": active.language})
                return path, session, context_meter.build_compaction_messages(session, active.language), t_cfg, active

        path, session, messages, t_cfg, active = await run_in_threadpool(_prep)
        parts, err_detail = [], ""
        if stream_messages is not None:
            async for ev in stream_messages(messages, t_cfg, temperature=0.1, max_tokens=700):
                if ev.get("type") == "token" and ev.get("delta"):
                    parts.append(str(ev["delta"]))
                elif ev.get("type") == "error":
                    err_detail = str(ev.get("detail") or "Compaction failed.")
        if err_detail and not parts:
            raise HTTPException(status_code=502, detail=err_detail)
        summary = "".join(parts).strip() or "\n".join(f"- {t.query[:120]}: {(t.tutor.answer[:160] if t.tutor else '')}" for t in session.turns[-6:])

        def _save() -> dict[str, object]:
            with workspace.STATE_LOCK:
                latest = chat_store.get_chat_session(chat_id, path)
                if latest is None or (not free_chat and not selection.chat_matches(latest, active)):
                    raise HTTPException(status_code=409, detail="Chat session was deleted or moved during compaction.")
                updated = chat_store.save_chat_session(latest.model_copy(update={"compacted_summary": summary, "context_cleared_at": max(0, len(latest.turns) - 2)}), path)
            return {"session": updated.model_dump(), "summary": summary, "context_usage": context_meter.compute_context_usage(updated, provider, model)}

        return await run_in_threadpool(_save)

    router.include_router(synthesize_routes.build_router(config, stream_messages))
    return router
