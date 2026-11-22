"""Streaming format-synthesis route preserving scope lock and session integrity."""

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from core import context_meter, contracts, model_routing
from core.agent_personas import active_persona_prompt
from core.agent_presets import AgentPersona
from core.cancellation import begin_request, check_cancelled, end_request
from core.output_formats import build_format_instruction, get_format
from features.ui import chat_store, route_helpers, selection, workspace
from features.ui.privacy import require_local

StreamMsgFn = Callable[..., AsyncIterator[dict[str, object]]]


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def resolve_chat_target(
    request: Request,
    active: contracts.WorkspaceConfig,
    free_chat: bool,
    *,
    allow_empty: bool = False,
) -> tuple[str, list[str]]:
    if free_chat:
        return chat_store.FREE_CHAT_AREA, [chat_store.FREE_CHAT_AREA]
    workspace.require_area(request, active)
    if not active.active_dirs:
        if allow_empty:
            return "", []
        raise HTTPException(status_code=400, detail="Create or link a workspace first, or use Free Chat.")
    return active.knowledge_dir, active.active_dirs


def build_router(config: Callable[[], contracts.WorkspaceConfig], stream_messages: StreamMsgFn | None = None) -> APIRouter:
    router = APIRouter()

    @router.post("/api/chats/{chat_id}/synthesize")
    async def synthesize_format(chat_id: str, request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key"), x_request_id: str | None = Header(default=None, alias="x-request-id")) -> StreamingResponse:
        body = await route_helpers.read_json_dict(request, required=True)
        fmt = get_format(workspace.REPO_ROOT, str(body.get("format_id") or ""))
        if fmt is None:
            raise HTTPException(status_code=404, detail="Output format not found")
        free_chat, extra_note = bool(body.get("free_chat")), str(body.get("extra_instruction") or "").strip()
        provider, model, api_key = str(body.get("provider") or "ollama"), str(body.get("model") or ""), x_api_key or str(body.get("api_key") or "")

        def _prep() -> tuple[contracts.WorkspaceConfig, str, list[str], Path, contracts.ChatSession, contracts.TutorConfig, list[str], AgentPersona, str, str, str]:
            with workspace.STATE_LOCK:
                active = config()
                require_local(active, provider, model)
                area, dirs = resolve_chat_target(request, active, free_chat)
                path = chat_store.area_chat_path(area)
                session = chat_store.get_chat_session(chat_id, path)
                if session is None or (not free_chat and not selection.chat_matches(session, active)):
                    raise HTTPException(status_code=404, detail="Chat session not found")
                if not session.turns and not session.attached_notes:
                    raise HTTPException(status_code=400, detail="Have at least one message or attached note before synthesizing a format.")
                agent, persona_instr = active_persona_prompt(workspace.REPO_ROOT, str(body.get("agent_id") or "") or active.active_agent, active.agent_name)
                eff_prov, eff_model, eff_key, _, _ = model_routing.resolve_agent_model(agent, active, provider, model, api_key or None)
                require_local(active, eff_prov, eff_model)
                t_cfg = workspace.build_tutor_config(eff_prov, eff_model or None, eff_key, 0.2).model_copy(update={"daily_cloud_request_limit": active.daily_cloud_request_limit, "daily_budget_usd_limit": active.daily_budget_usd_limit, "response_language": active.language})
                cited = list(dict.fromkeys(c for t in session.turns if t.tutor for c in t.tutor.cited_titles))[:8]
                return active, area, dirs, path, session, t_cfg, cited, agent, persona_instr, eff_prov, eff_model or ""

        active, area, dirs, path, session, t_cfg, cited, agent, persona_instr, eff_prov, eff_model = await run_in_threadpool(_prep)
        summary, history, notes = context_meter.active_history_for_session(session)
        instruction, p_tokens = (f"{persona_instr}\n\n" if persona_instr else "") + build_format_instruction(fmt, extra_note), context_meter.approx_tokens(persona_instr)
        prompt_parts = ([f"Compacted memory:\n{summary}"] if summary else []) + [f"Turn {i} User: {q}\nAssistant: {a}" for i, (q, a) in enumerate(history, 1)] + [f"Attached File ({n['name']}):\n{n['content'][:10000]}" for n in notes[-6:]]
        messages = [{"role": "system", "content": instruction}, {"role": "user", "content": "\n\n".join(prompt_parts)}]

        async def _gen() -> AsyncIterator[str]:
            token = begin_request(x_request_id)
            emitted, thought, meta = [], [], {}
            try:
                if stream_messages is not None:
                    async for ev in stream_messages(messages, t_cfg, temperature=0.2, request_id=x_request_id, max_tokens=3072):
                        if await request.is_disconnected():
                            raise InterruptedError("Generation stopped by user.")
                        check_cancelled()
                        et = ev.get("type")
                        if et == "thinking" and ev.get("delta"):
                            thought.append(str(ev["delta"]))
                            yield _sse("thinking", {"delta": str(ev["delta"])})
                        elif et == "token" and ev.get("delta"):
                            emitted.append(str(ev["delta"]))
                            yield _sse("token", {"delta": str(ev["delta"])})
                        elif et == "meta":
                            meta = dict(ev)
                        elif et == "error":
                            yield _sse("error", {"detail": str(ev.get("detail") or "Synthesis failed.")})
                            return
                turn = contracts.ChatTurn(query=f"Synthesize as {fmt.name}" + (f" — {extra_note}" if extra_note else ""), ask_tutor=True, tutor=contracts.TutorResponse(answer="".join(emitted).strip() or f"# {fmt.name}\n\nNo content generated.", cited_titles=cited, knowledge_gap_detected=False, recommended_topics=[]), results=[], created_at=chat_store.utc_now_iso(), subfolder=session.subfolder, doc_id=session.doc_id, thinking="".join(thought).strip(), telemetry=meta, format_name=fmt.name, agent_id=agent.id, agent_name=agent.name)

                def _commit() -> contracts.ChatSession | None:
                    with workspace.STATE_LOCK:
                        latest = chat_store.get_chat_session(chat_id, path)
                        if latest is None or (not free_chat and not selection.chat_matches(latest, active)):
                            return None
                        return chat_store.append_chat_turn(chat_id, turn, path, area, dirs)

                updated = await asyncio.to_thread(_commit)
                if updated is None:
                    yield _sse("error", {"detail": "Chat session was deleted or moved during synthesis."})
                    return
                ctx_usage = await asyncio.to_thread(context_meter.compute_context_usage, updated, eff_prov, eff_model, persona_tokens=p_tokens)
                yield _sse("telemetry", {**meta, "context_usage": ctx_usage})
                yield _sse("done", {**updated.model_dump(), "context_usage": ctx_usage})
            except (InterruptedError, asyncio.CancelledError):
                yield _sse("stopped", {"partial": "".join(emitted).strip()})
            finally:
                end_request(x_request_id, token)

        return StreamingResponse(_gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    return router
