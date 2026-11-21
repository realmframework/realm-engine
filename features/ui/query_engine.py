"""Compose scoped retrieval and deterministic refusal before any answer generation."""

from collections.abc import Callable

from core.contracts import (
    ChatTurnRequest,
    KnowledgeChunk,
    SearchQuery,
    SearchResult,
    TutorResponse,
    WorkspaceConfig,
)
from core.scope import is_navigation, matches_scope
from core.web_search import search_web_context
from features.ui import workspace


def retrieve(payload: ChatTurnRequest, chunks: list[KnowledgeChunk], history: list[tuple[str, str]], route: Callable[..., dict[str, object]], search: Callable[..., list[SearchResult]], embed: Callable[..., list[float]], policy: WorkspaceConfig | None = None) -> tuple[SearchQuery, list[SearchResult], dict[str, object]]:
    routed = route(payload.query, history=history, top_k=payload.top_k, retrieval_mode=payload.retrieval_mode, rrf_k=payload.rrf_k)
    query = workspace.build_search_query(str(routed["routed_query"]), payload.tag or payload.tag_filter, int(str(routed["top_k"])), str(routed["retrieval_mode"]), int(str(routed["rrf_k"])))
    query = query.model_copy(update={"doc_id": payload.doc_id, "subfolder": payload.subfolder})
    candidates = [
        chunk
        for chunk in chunks
        if matches_scope(chunk, query.doc_id, query.subfolder) and (not payload.ask_tutor or not is_navigation(chunk))
    ]
    vector = embed(query.query, provider=payload.provider or "ollama", api_key=payload.api_key) if query.retrieval_mode != "lexical" and any(bool(c.embedding) for c in candidates) else None
    local_results = search(query, candidates, query_embedding=vector)
    web_results = search_web_context(query.query, policy) if (policy is not None and payload.use_web_search) else []
    return query, [*local_results, *web_results], routed


def answer(payload: ChatTurnRequest, results: list[SearchResult], history: list[tuple[str, str]], tutor: Callable[..., TutorResponse], policy: WorkspaceConfig) -> TutorResponse | None:
    if not payload.ask_tutor:
        return None
    if not results:
        return TutorResponse(answer="No matching source passages were found in this scope. I cannot provide a grounded answer; try another question or scope.", cited_titles=[], knowledge_gap_detected=True, recommended_topics=[])
    config = workspace.build_tutor_config(payload.provider, payload.model, payload.api_key, payload.temperature)
    config = config.model_copy(update={"daily_cloud_request_limit": policy.daily_cloud_request_limit, "daily_budget_usd_limit": policy.daily_budget_usd_limit, "response_language": policy.language})
    return tutor(payload.query, results, config, history=history, temperature=payload.temperature)
