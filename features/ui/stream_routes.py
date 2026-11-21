"""Server-Sent Events (SSE) live token + thinking streaming route for vault & Free Chat."""

import asyncio
import inspect
import json
import re
from collections.abc import AsyncIterator, Callable

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse

from core.cancellation import begin_request, check_cancelled, end_request
from core.context_meter import active_history_for_session, compute_context_usage
from core.contracts import (
    ChatTurn,
    ChatTurnRequest,
    KnowledgeChunk,
    SearchResult,
    TutorResponse,
    WorkspaceConfig,
)
from core.output_formats import build_format_instruction, get_format
from core.web_search import search_web_context
from features.ui import chat_store, query_engine, selection, workspace
from features.ui.areas import area_identity
from features.ui.privacy import require_local

StreamTutorFn = Callable[..., AsyncIterator[object]]
_THINK_RE = re.compile(r"<think>([\s\S]*?)</think>", re.IGNORECASE)


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _cited(results: list[SearchResult]) -> list[str]:
    return list(dict.fromkeys(r.chunk.title for r in results[:5] if r.chunk.title))


def build_router(config: Callable[[], WorkspaceConfig], index: Callable[[], list[KnowledgeChunk]], route: Callable[..., dict[str, object]], search: Callable[..., list[SearchResult]], embed: Callable[..., list[float]], stream_tutor: StreamTutorFn) -> APIRouter:
    router = APIRouter()
    rich_stream = "free_chat" in inspect.signature(stream_tutor).parameters

    @router.post("/api/chats/{chat_id}/turn/stream")
    async def append_stream(chat_id: str, payload: ChatTurnRequest, request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key"), x_request_id: str | None = Header(default=None, alias="x-request-id")) -> StreamingResponse:
        with workspace.STATE_LOCK:
            active = config()
            require_local(active, payload.provider, payload.model)
            is_free = bool(payload.free_chat)
            if not is_free:
                workspace.require_area(request, active)
            area = chat_store.FREE_CHAT_AREA if is_free else active.knowledge_dir
            dirs = [chat_store.FREE_CHAT_AREA] if is_free else active.active_dirs
            chunks = [] if is_free else list(index())
            path = chat_store.area_chat_path(area)
            identities = {} if is_free else {name: area_identity(name, workspace.REPO_ROOT) for name in active.active_dirs}
            existing = chat_store.get_chat_session(chat_id, path)
            if not is_free and existing and not selection.chat_matches(existing, active):
                raise HTTPException(status_code=404, detail="Chat does not belong to this area")
            if not is_free and existing:
                if {"subfolder", "doc_id"}.intersection(payload.model_fields_set) and (payload.subfolder, payload.doc_id) != (existing.subfolder, existing.doc_id):
                    raise HTTPException(status_code=409, detail="Conversation scope is locked. Start a new chat to change it.")
                payload = payload.model_copy(update={"subfolder": existing.subfolder, "doc_id": existing.doc_id})
            payload = payload.model_copy(update={"api_key": x_api_key or payload.api_key})
            fmt = get_format(workspace.REPO_ROOT, payload.format_id)
        summary, history, notes = active_history_for_session(existing)
        fmt_instr = build_format_instruction(fmt) if fmt else ""

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
                    response: TutorResponse | None = None
                elif not is_free and not results and not notes:
                    msg = "No matching source passages were found in this scope. I cannot provide a grounded answer; try another question, attach a note, or switch to Free Chat."
                    yield _sse("token", {"delta": msg})
                    response = TutorResponse(answer=msg, cited_titles=[], knowledge_gap_detected=True, recommended_topics=[])
                else:
                    t_cfg = workspace.build_tutor_config(payload.provider, payload.model, payload.api_key, payload.temperature).model_copy(update={"daily_cloud_request_limit": active.daily_cloud_request_limit, "daily_budget_usd_limit": active.daily_budget_usd_limit, "response_language": active.language})
                    stream_it = stream_tutor(payload.query, results, t_cfg, history=history, temperature=payload.temperature, request_id=x_request_id, compacted_summary=summary, attached_notes=notes, format_instruction=fmt_instr, free_chat=is_free) if rich_stream else stream_tutor(payload.query, results, t_cfg, history=history, temperature=payload.temperature, request_id=x_request_id)
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
                        elif item:
                            emitted.append(str(item))
                            yield _sse("token", {"delta": str(item)})
                    raw_answer = "".join(emitted).strip()
                    inline_thoughts = [m.group(1).strip() for m in _THINK_RE.finditer(raw_answer) if m.group(1).strip()]
                    if inline_thoughts:
                        if thought:
                            thought.append("\n\n")
                        thought.append("\n\n".join(inline_thoughts))
                        raw_answer = _THINK_RE.sub("", raw_answer).strip()
                    response = TutorResponse(answer=raw_answer or "No answer was generated.", cited_titles=_cited(results), knowledge_gap_detected=not is_free and not results and not notes, recommended_topics=[])
                check_cancelled()
                turn = ChatTurn(query=payload.query, tag=payload.tag, ask_tutor=payload.ask_tutor, tutor=response, results=results, created_at=chat_store.utc_now_iso(), top_k=query.top_k, retrieval_mode=query.retrieval_mode, rrf_k=query.rrf_k, temperature=payload.temperature, subfolder=payload.subfolder, doc_id=payload.doc_id, thinking="".join(thought).strip(), telemetry=meta, format_name=fmt.name if fmt else "")
                with workspace.STATE_LOCK:
                    check_cancelled()
                    if not is_free and not selection.identities_unchanged(workspace.REPO_ROOT, identities):
                        yield _sse("error", {"detail": "Knowledge area was deleted while the answer was being prepared"})
                        return
                    latest = chat_store.get_chat_session(chat_id, path)
                    if not is_free and latest and (not selection.chat_matches(latest, active) or (latest.subfolder, latest.doc_id) != (payload.subfolder, payload.doc_id)):
                        yield _sse("error", {"detail": "Conversation scope changed during this request. Start a new chat."})
                        return
                    session = chat_store.append_chat_turn(chat_id, turn, path, area, dirs)
                ctx_usage = compute_context_usage(session, payload.provider or "ollama", payload.model or "qwen3:8b")
                yield _sse("telemetry", {**meta, "context_usage": ctx_usage})
                yield _sse("done", {**session.model_dump(), "router_decision": routed, "context_usage": ctx_usage})
            except (InterruptedError, asyncio.CancelledError):
                yield _sse("stopped", {"partial": "".join(emitted).strip()})
            finally:
                end_request(x_request_id, token)

        return StreamingResponse(_generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    return router
