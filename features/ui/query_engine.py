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
    eco = bool(policy and policy.eco_mode)
    routed = route(payload.query, history=history[-2:] if eco else history, top_k=payload.top_k, retrieval_mode=payload.retrieval_mode, rrf_k=payload.rrf_k)
    routed_k = min(int(str(routed["top_k"])), 3) if eco else int(str(routed["top_k"]))
    if eco:
        routed = {**routed, "top_k": routed_k, "label": f"{routed['label']} · Eco"}
    query = workspace.build_search_query(str(routed["routed_query"]), payload.tag or payload.tag_filter, routed_k, str(routed["retrieval_mode"]), int(str(routed["rrf_k"])))
    query = query.model_copy(update={"doc_id": payload.doc_id, "subfolder": payload.subfolder})
    muted = {m.strip() for m in payload.muted_doc_ids if m.strip()}
    pinned = {p.strip() for p in payload.pinned_doc_ids if p.strip()}
    candidates = [
        chunk
        for chunk in chunks
        if matches_scope(chunk, query.doc_id, query.subfolder)
        and (not payload.ask_tutor or not is_navigation(chunk))
        and chunk.doc_id not in muted
    ]
    vector = embed(query.query, provider=payload.provider or "ollama", api_key=payload.api_key) if query.retrieval_mode != "lexical" and any(bool(c.embedding) for c in candidates) else None
    local_results = search(query, candidates, query_embedding=vector)
    if pinned:
        pin_existing = [r for r in local_results if r.chunk.doc_id in pinned]
        other = [r for r in local_results if r.chunk.doc_id not in pinned]
        seen = {r.chunk.id for r in local_results}
        pin_missing = [SearchResult(chunk=c, score=999.0) for c in candidates if c.doc_id in pinned and c.id not in seen]
        local_results = [*pin_existing, *pin_missing, *other][: query.top_k]
    web_results = search_web_context(query.query, policy) if (policy is not None and payload.use_web_search) else []
    stripped = [r.model_copy(update={"chunk": r.chunk.model_copy(update={"embedding": None})}) if r.chunk.embedding is not None else r for r in (*local_results, *web_results)]
    return query, stripped, routed


def answer(payload: ChatTurnRequest, results: list[SearchResult], history: list[tuple[str, str]], tutor: Callable[..., TutorResponse], policy: WorkspaceConfig) -> TutorResponse | None:
    if not payload.ask_tutor:
        return None
    if not results:
        return TutorResponse(answer="No matching source passages were found in this scope. I cannot provide a grounded answer; try another question or scope.", cited_titles=[], knowledge_gap_detected=True, recommended_topics=[])
    config = workspace.build_tutor_config(payload.provider, payload.model, payload.api_key, payload.temperature)
    updates: dict[str, object] = {"daily_cloud_request_limit": policy.daily_cloud_request_limit, "daily_budget_usd_limit": policy.daily_budget_usd_limit, "response_language": policy.language}
    if policy.eco_mode:
        updates["reasoning_effort"] = "low"
        history = history[-2:]
    config = config.model_copy(update=updates)
    return tutor(payload.query, results, config, history=history, temperature=payload.temperature)
