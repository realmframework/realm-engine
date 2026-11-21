"""Area and conversation-scope admission before retrieval, embeddings and tutoring."""

from collections.abc import Callable

from fastapi import APIRouter, Header, HTTPException, Request

from core.cancellation import (
    begin_request,
    cancel_request,
    check_cancelled,
    end_request,
)
from core.contracts import (
    ChatTurn,
    ChatTurnRequest,
    KnowledgeChunk,
    SearchResult,
    TutorResponse,
    WorkspaceConfig,
)
from features.ui import chat_store, query_engine, selection, stream_routes, workspace
from features.ui.areas import area_identity
from features.ui.privacy import require_local


def build_router(
    config: Callable[[], WorkspaceConfig],
    index: Callable[[], list[KnowledgeChunk]],
    route: Callable[..., dict[str, object]],
    search: Callable[..., list[SearchResult]],
    embed: Callable[..., list[float]],
    tutor: Callable[..., TutorResponse],
    stream_tutor: stream_routes.StreamTutorFn | None = None,
) -> APIRouter:
    router = APIRouter()
    if stream_tutor is not None:
        router.include_router(stream_routes.build_router(config, index, route, search, embed, stream_tutor))

    @router.post("/api/requests/{request_id}/cancel")
    def cancel_active_request(request_id: str) -> dict[str, bool]:
        return {"cancelled": cancel_request(request_id)}

    @router.get("/api/search")
    def search_api(request: Request, q: str = "", tag: str | None = None, ask_tutor: bool = False, use_web_search: bool = False, provider: str | None = None, model: str | None = None, top_k: int = 5, retrieval_mode: str = "hybrid", rrf_k: int = 60, temperature: float = 0.2, subfolder: str | None = None, doc_id: str | None = None, x_api_key: str | None = Header(default=None, alias="x-api-key"), x_request_id: str | None = Header(default=None, alias="x-request-id")) -> dict[str, object]:
        token = begin_request(x_request_id)
        try:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                require_local(active, provider, model)
                chunks = list(index())
            bounded = workspace.build_search_query(q, tag, top_k, retrieval_mode, rrf_k)
            payload = ChatTurnRequest(query=q, tag=tag, ask_tutor=ask_tutor, use_web_search=use_web_search, provider=provider, model=model, api_key=x_api_key, top_k=bounded.top_k, retrieval_mode=bounded.retrieval_mode, rrf_k=bounded.rrf_k, temperature=max(0.0, min(1.0, temperature)), subfolder=subfolder, doc_id=doc_id)
            query, results, routed = query_engine.retrieve(payload, chunks, [], route, search, embed, active)
            check_cancelled()
            response = query_engine.answer(payload, results, [], tutor, active)
            check_cancelled()
            return {"area": active.knowledge_dir, "active_dirs": active.active_dirs, "doc_id": doc_id, "subfolder": subfolder, "is_knowledge_gap": bool(q.strip() and not results), "results": [r.model_dump() for r in results], "tutor": response.model_dump() if response else None, "rag_config": {"retrieval_mode": query.retrieval_mode, "top_k": query.top_k, "rrf_k": query.rrf_k, "temperature": payload.temperature, "router_label": routed["label"], "intent": routed["intent"]}}
        except InterruptedError as exc:
            raise HTTPException(status_code=499, detail=str(exc)) from exc
        finally:
            end_request(x_request_id, token)

    @router.post("/api/chats/{chat_id}/turn")
    def append(chat_id: str, payload: ChatTurnRequest, request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key"), x_request_id: str | None = Header(default=None, alias="x-request-id")) -> dict[str, object]:
        token = begin_request(x_request_id)
        try:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                require_local(active, payload.provider, payload.model)
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
            history = [(t.query, t.tutor.answer if t.tutor else "") for t in (existing.turns if existing else [])[-2:]]
            query, results, routed = query_engine.retrieve(payload, chunks, history, route, search, embed, active)
            check_cancelled()
            response = query_engine.answer(payload, results, history, tutor, active)
            check_cancelled()
            turn = ChatTurn(query=payload.query, tag=payload.tag, ask_tutor=payload.ask_tutor, tutor=response, results=results, created_at=chat_store.utc_now_iso(), top_k=query.top_k, retrieval_mode=query.retrieval_mode, rrf_k=query.rrf_k, temperature=payload.temperature, subfolder=payload.subfolder, doc_id=payload.doc_id)
            with workspace.STATE_LOCK:
                check_cancelled()
                if not selection.identities_unchanged(workspace.REPO_ROOT, identities):
                    raise HTTPException(status_code=409, detail="Knowledge area was deleted while the answer was being prepared")
                latest = chat_store.get_chat_session(chat_id, path)
                if latest and (not selection.chat_matches(latest, active) or (latest.subfolder, latest.doc_id) != (payload.subfolder, payload.doc_id)):
                    raise HTTPException(status_code=409, detail="Conversation scope changed during this request. Start a new chat.")
                return {**chat_store.append_chat_turn(chat_id, turn, path, area, active.active_dirs).model_dump(), "router_decision": routed}
        except InterruptedError as exc:
            raise HTTPException(status_code=499, detail=str(exc)) from exc
        finally:
            end_request(x_request_id, token)

    return router
