"""Area and conversation-scope admission before retrieval, embeddings and tutoring."""

from collections.abc import Callable

from fastapi import APIRouter, Header, HTTPException, Request

from core import cancellation, context_meter, contracts, model_routing
from core.agent_personas import active_persona_prompt
from features.ui import chat_store, query_engine, selection, stream_routes, workspace
from features.ui.areas import area_identity
from features.ui.privacy import require_local


def build_router(
    config: Callable[[], contracts.WorkspaceConfig],
    index: Callable[[], list[contracts.KnowledgeChunk]],
    route: Callable[..., dict[str, object]],
    search: Callable[..., list[contracts.SearchResult]],
    embed: Callable[..., list[float]],
    tutor: Callable[..., contracts.TutorResponse],
    stream_tutor: stream_routes.StreamTutorFn | None = None,
) -> APIRouter:
    router = APIRouter()
    if stream_tutor is not None:
        router.include_router(stream_routes.build_router(config, index, route, search, embed, stream_tutor))

    @router.post("/api/requests/{request_id}/cancel")
    def cancel_active_request(request_id: str) -> dict[str, bool]:
        return {"cancelled": cancellation.cancel_request(request_id)}

    @router.get("/api/search")
    def search_api(request: Request, q: str = "", tag: str | None = None, ask_tutor: bool = False, use_web_search: bool = False, provider: str | None = None, model: str | None = None, top_k: int = 5, retrieval_mode: str = "hybrid", rrf_k: int = 60, temperature: float = 0.2, subfolder: str | None = None, doc_id: str | None = None, x_api_key: str | None = Header(default=None, alias="x-api-key"), x_request_id: str | None = Header(default=None, alias="x-request-id")) -> dict[str, object]:
        token = cancellation.begin_request(x_request_id)
        try:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                require_local(active, provider, model)
                chunks = list(index())
            bounded = workspace.build_search_query(q, tag, top_k, retrieval_mode, rrf_k)
            payload = contracts.ChatTurnRequest(query=q, tag=tag, ask_tutor=ask_tutor, use_web_search=use_web_search, provider=provider, model=model, api_key=x_api_key, top_k=bounded.top_k, retrieval_mode=bounded.retrieval_mode, rrf_k=bounded.rrf_k, temperature=max(0.0, min(1.0, temperature)), subfolder=subfolder, doc_id=doc_id)
            query, results, routed = query_engine.retrieve(payload, chunks, [], route, search, embed, active)
            cancellation.check_cancelled()
            response = query_engine.answer(payload, results, [], tutor, active)
            cancellation.check_cancelled()
            return {"area": active.knowledge_dir, "active_dirs": active.active_dirs, "doc_id": doc_id, "subfolder": subfolder, "is_knowledge_gap": bool(q.strip() and not results), "results": [r.model_dump() for r in results], "tutor": response.model_dump() if response else None, "rag_config": {"retrieval_mode": query.retrieval_mode, "top_k": query.top_k, "rrf_k": query.rrf_k, "temperature": payload.temperature, "router_label": routed["label"], "intent": routed["intent"]}}
        except InterruptedError as exc:
            raise HTTPException(status_code=499, detail=str(exc)) from exc
        finally:
            cancellation.end_request(x_request_id, token)

    @router.post("/api/chats/{chat_id}/turn")
    def append(chat_id: str, payload: contracts.ChatTurnRequest, request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key"), x_request_id: str | None = Header(default=None, alias="x-request-id")) -> dict[str, object]:
        token = cancellation.begin_request(x_request_id)
        try:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                require_local(active, payload.provider, payload.model)
                if not active.active_dirs:
                    raise HTTPException(status_code=400, detail="Create or link a workspace first, or use Free Chat.")
                area, chunks = active.knowledge_dir, list(index())
                path = chat_store.area_chat_path(area)
                identities = {name: area_identity(name, workspace.REPO_ROOT) for name in active.active_dirs}
                existing = chat_store.get_chat_session(chat_id, path)
                if existing and not selection.chat_matches(existing, active):
                    raise HTTPException(status_code=404, detail="Chat does not belong to this area")
                if existing:
                    if {"subfolder", "doc_id"}.intersection(payload.model_fields_set) and (payload.subfolder, payload.doc_id) != (existing.subfolder, existing.doc_id):
                        raise HTTPException(status_code=409, detail="Conversation scope is locked. Start a new chat to change it.")
                    payload = payload.model_copy(update={"subfolder": existing.subfolder, "doc_id": existing.doc_id})
                payload = payload.model_copy(update={"api_key": x_api_key or payload.api_key})
                agent, _ = active_persona_prompt(workspace.REPO_ROOT, payload.agent_id or active.active_agent, active.agent_name)
                eff_prov, eff_model, eff_key, is_pinned, model_notice = model_routing.resolve_agent_model(agent, active, payload.provider, payload.model, payload.api_key)
                require_local(active, eff_prov, eff_model)
            _, full_history, _ = context_meter.active_history_for_session(existing)
            history = full_history[-2:]
            query, results, routed = query_engine.retrieve(payload, chunks, history, route, search, embed, active)
            cancellation.check_cancelled()
            if payload.ask_tutor:
                model_routing.maybe_unload_previous_ollama(eff_prov, eff_model or "qwen3:8b")
            tutor_q = f"{payload.instruction_prefix.strip()}\n\n{payload.query}" if payload.instruction_prefix.strip() else payload.query
            tutor_payload = payload.model_copy(update={"query": tutor_q, "provider": eff_prov, "model": eff_model or None, "api_key": eff_key})
            response = query_engine.answer(tutor_payload, results, history, tutor, active)
            cancellation.check_cancelled()
            telemetry = {"provider": eff_prov, "model": eff_model, "pinned_agent_model": is_pinned, **({"notice": model_notice} if model_notice else {})}
            turn = contracts.ChatTurn(query=payload.query, tag=payload.tag, ask_tutor=payload.ask_tutor, tutor=response, results=results, created_at=chat_store.utc_now_iso(), top_k=query.top_k, retrieval_mode=query.retrieval_mode, rrf_k=query.rrf_k, temperature=payload.temperature, subfolder=payload.subfolder, doc_id=payload.doc_id, telemetry=telemetry, agent_id=agent.id, agent_name=agent.name)
            with workspace.STATE_LOCK:
                cancellation.check_cancelled()
                if not selection.identities_unchanged(workspace.REPO_ROOT, identities):
                    raise HTTPException(status_code=409, detail="Knowledge area was deleted while the answer was being prepared")
                latest = chat_store.get_chat_session(chat_id, path)
                if existing is not None and latest is None:
                    raise HTTPException(status_code=409, detail="Chat session was deleted or moved while the answer was being prepared")
                if latest and (not selection.chat_matches(latest, active) or (latest.subfolder, latest.doc_id) != (payload.subfolder, payload.doc_id)):
                    raise HTTPException(status_code=409, detail="Conversation scope changed during this request. Start a new chat.")
                return {**chat_store.append_chat_turn(chat_id, turn, path, area, active.active_dirs).model_dump(), "router_decision": routed}
        except InterruptedError as exc:
            raise HTTPException(status_code=499, detail=str(exc)) from exc
        finally:
            cancellation.end_request(x_request_id, token)

    return router
