"""Server-Sent Events (SSE) live token + thinking streaming route for vault & Free Chat."""

import asyncio
import inspect
import json
import re
from collections.abc import AsyncIterator, Callable
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse

from core import context_meter, contracts, model_routing
from core.agent_personas import active_persona_prompt
from core.agent_presets import AgentPersona
from core.cancellation import begin_request, check_cancelled, end_request
from core.format_presets import OutputFormat
from core.output_formats import build_format_instruction, get_format
from core.web_search import search_web_context
from features.ui import chat_store, query_engine, selection, workspace
from features.ui.areas import area_identity
from features.ui.privacy import require_local

StreamTutorFn = Callable[..., AsyncIterator[object]]
_THINK_RE = re.compile(r"<think>([\s\S]*?)</think>", re.IGNORECASE)


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

def _cited(results: list[contracts.SearchResult]) -> list[str]:
    return list(dict.fromkeys(r.chunk.title for r in results[:5] if r.chunk.title))

def build_router(config: Callable[[], contracts.WorkspaceConfig], index: Callable[[], list[contracts.KnowledgeChunk]], route: Callable[..., dict[str, object]], search: Callable[..., list[contracts.SearchResult]], embed: Callable[..., list[float]], stream_tutor: StreamTutorFn) -> APIRouter:
    router = APIRouter()
    rich_stream = bool({"free_chat", "persona_instruction"} & set(inspect.signature(stream_tutor).parameters))

    @router.post("/api/chats/{chat_id}/turn/stream")
    async def append_stream(chat_id: str, payload: contracts.ChatTurnRequest, request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key"), x_request_id: str | None = Header(default=None, alias="x-request-id")) -> StreamingResponse:
        def _prepare() -> tuple[contracts.WorkspaceConfig, bool, str, list[str], list[contracts.KnowledgeChunk], Path, dict[str, str], contracts.ChatSession | None, contracts.ChatTurnRequest, OutputFormat | None, AgentPersona, str, str, str, str | None, bool, str]:
            with workspace.STATE_LOCK:
                active = config()
                require_local(active, payload.provider, payload.model)
                is_free = bool(payload.free_chat)
                if not is_free:
                    workspace.require_area(request, active)
                    if not active.active_dirs:
                        raise HTTPException(status_code=400, detail="Create or link a workspace first, or use Free Chat.")
                area = chat_store.FREE_CHAT_AREA if is_free else active.knowledge_dir
                dirs = [chat_store.FREE_CHAT_AREA] if is_free else active.active_dirs
                chunks, path = ([] if is_free else list(index())), chat_store.area_chat_path(area)
                identities = {} if is_free else {name: area_identity(name, workspace.REPO_ROOT) for name in active.active_dirs}
                existing = chat_store.get_chat_session(chat_id, path)
                if not is_free and existing and not selection.chat_matches(existing, active):
                    raise HTTPException(status_code=404, detail="Chat does not belong to this area")
                eff = payload
                if not is_free and existing:
                    if {"subfolder", "doc_id"}.intersection(payload.model_fields_set) and (payload.subfolder, payload.doc_id) != (existing.subfolder, existing.doc_id):
                        raise HTTPException(status_code=409, detail="Conversation scope is locked. Start a new chat to change it.")
                    eff = eff.model_copy(update={"subfolder": existing.subfolder, "doc_id": existing.doc_id})
                eff = eff.model_copy(update={"api_key": x_api_key or eff.api_key})
                fmt = get_format(workspace.REPO_ROOT, eff.format_id)
                agent, persona_instr = active_persona_prompt(workspace.REPO_ROOT, eff.agent_id or active.active_agent, active.agent_name)
                eff_prov, eff_model, eff_key, is_pinned, model_notice = model_routing.resolve_agent_model(agent, active, eff.provider, eff.model, eff.api_key)
                require_local(active, eff_prov, eff_model)
                return active, is_free, area, dirs, chunks, path, identities, existing, eff, fmt, agent, persona_instr, eff_prov, eff_model, eff_key, is_pinned, model_notice

        active, is_free, area, dirs, chunks, path, identities, existing, payload, fmt, agent, persona_instr, eff_prov, eff_model, eff_key, is_pinned, model_notice = await asyncio.to_thread(_prepare)
        summary, history, notes = context_meter.active_history_for_session(existing)
        history = model_routing.trim_history_for_model(history[-2:] if active.eco_mode else history, eff_prov, eff_model, summary)
        fmt_instr = "\n\n".join(p for p in (build_format_instruction(fmt) if fmt else "", payload.instruction_prefix.strip()) if p)
        p_tokens = context_meter.approx_tokens(persona_instr)

        async def _generate() -> AsyncIterator[str]:
            token = begin_request(x_request_id)
            emitted, thought, meta = [], [], {}
            try:
                if is_free:
                    query = workspace.build_search_query(payload.query, None, payload.top_k, "lexical", payload.rrf_k)
                    results = await asyncio.to_thread(search_web_context, payload.query, active) if payload.use_web_search else []
                    routed: dict[str, object] = {"label": "Free Chat (No Vault)", "intent": "free_chat", "routed_query": payload.query, "top_k": payload.top_k, "retrieval_mode": "lexical", "rrf_k": payload.rrf_k}
                else:
                    query, results, routed = await asyncio.to_thread(query_engine.retrieve, payload, chunks, history, route, search, embed, active)
                check_cancelled()
                yield _sse("retrieval", {"results": [r.model_dump() for r in results], "router_decision": routed, "rag_config": {"retrieval_mode": query.retrieval_mode, "top_k": query.top_k, "rrf_k": query.rrf_k, "temperature": payload.temperature, "router_label": routed["label"]}})
                if not payload.ask_tutor:
                    response: contracts.TutorResponse | None = None
                elif not is_free and not results and not notes:
                    msg = "No matching source passages were found in this scope. I cannot provide a grounded answer; try another question, attach a note, or switch to Free Chat."
                    yield _sse("token", {"delta": msg})
                    response = contracts.TutorResponse(answer=msg, cited_titles=[], knowledge_gap_detected=True, recommended_topics=[])
                else:
                    await asyncio.to_thread(model_routing.maybe_unload_previous_ollama, eff_prov, eff_model or "qwen3:8b")
                    t_cfg = workspace.build_tutor_config(eff_prov, eff_model or None, eff_key, payload.temperature).model_copy(update={"daily_cloud_request_limit": active.daily_cloud_request_limit, "daily_budget_usd_limit": active.daily_budget_usd_limit, "response_language": active.language, **({"reasoning_effort": "low"} if active.eco_mode else {})})
                    stream_it = stream_tutor(payload.query, results, t_cfg, history=history, temperature=payload.temperature, request_id=x_request_id, compacted_summary=summary, attached_notes=notes, format_instruction=fmt_instr, free_chat=is_free, persona_instruction=persona_instr) if rich_stream else stream_tutor(payload.query, results, t_cfg, history=history, temperature=payload.temperature, request_id=x_request_id)
                    async for item in stream_it:
                        if await request.is_disconnected():
                            raise InterruptedError("Generation stopped by user.")
                        check_cancelled()
                        if isinstance(item, dict):
                            et = item.get("type")
                            if et == "thinking" and item.get("delta"):
                                thought.append(str(item["delta"]))
                                yield _sse("thinking", {"delta": str(item["delta"])})
                            elif et == "token" and item.get("delta"):
                                emitted.append(str(item["delta"]))
                                yield _sse("token", {"delta": str(item["delta"])})
                            elif et == "meta":
                                meta = dict(item)
                            elif et == "error":
                                yield _sse("error", {"detail": str(item.get("detail") or "AI generation failed.")})
                                return
                        elif item:
                            emitted.append(str(item))
                            yield _sse("token", {"delta": str(item)})
                    raw_answer = "".join(emitted).strip()
                    if inline_thoughts := [m.group(1).strip() for m in _THINK_RE.finditer(raw_answer) if m.group(1).strip()]:
                        thought.append(("\n\n" if thought else "") + "\n\n".join(inline_thoughts))
                        raw_answer = _THINK_RE.sub("", raw_answer).strip()
                    response = contracts.TutorResponse(answer=raw_answer or "No answer was generated.", cited_titles=_cited(results), knowledge_gap_detected=not is_free and not results and not notes, recommended_topics=[])
                check_cancelled()
                meta = {**meta, "provider": eff_prov, "model": str(meta.get("model") or eff_model), "pinned_agent_model": is_pinned, **({"notice": model_notice} if model_notice else {})}
                turn = contracts.ChatTurn(query=payload.query, tag=payload.tag, ask_tutor=payload.ask_tutor, tutor=response, results=results, created_at=chat_store.utc_now_iso(), top_k=query.top_k, retrieval_mode=query.retrieval_mode, rrf_k=query.rrf_k, temperature=payload.temperature, subfolder=payload.subfolder, doc_id=payload.doc_id, thinking="".join(thought).strip(), telemetry=meta, format_name=fmt.name if fmt else "", agent_id=agent.id, agent_name=agent.name)

                def _commit() -> tuple[contracts.ChatSession | None, str]:
                    with workspace.STATE_LOCK:
                        check_cancelled()
                        if not is_free and not selection.identities_unchanged(workspace.REPO_ROOT, identities):
                            return None, "Knowledge area was deleted while the answer was being prepared"
                        latest = chat_store.get_chat_session(chat_id, path)
                        if existing is not None and latest is None:
                            return None, "Chat session was deleted or moved while the answer was being prepared."
                        if not is_free and latest and (not selection.chat_matches(latest, active) or (latest.subfolder, latest.doc_id) != (payload.subfolder, payload.doc_id)):
                            return None, "Conversation scope changed during this request. Start a new chat."
                        return chat_store.append_chat_turn(chat_id, turn, path, area, dirs), ""
                session, err = await asyncio.to_thread(_commit)
                if session is None:
                    yield _sse("error", {"detail": err})
                    return
                ctx_usage = await asyncio.to_thread(context_meter.compute_context_usage, session, eff_prov, eff_model or "qwen3:8b", persona_tokens=p_tokens)
                yield _sse("telemetry", {**meta, "context_usage": ctx_usage})
                yield _sse("done", {**session.model_dump(), "router_decision": routed, "context_usage": ctx_usage, **({"notice": model_notice} if model_notice else {})})
            except (InterruptedError, asyncio.CancelledError):
                yield _sse("stopped", {"partial": "".join(emitted).strip()})
            finally:
                end_request(x_request_id, token)
        return StreamingResponse(_generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
    return router
