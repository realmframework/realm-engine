"""Stateless, read-only public API routes for websites (REALM_MODE=public)."""

from collections.abc import Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from core.contracts import (
    KnowledgeArea,
    KnowledgeChunk,
    PublicAskRequest,
    SearchQuery,
    SearchResult,
    TutorConfig,
    TutorResponse,
)
from core.scope import is_navigation, matches_scope, resolve_chunk_url
from features.ui.graph_data import area_graph
from features.ui.public_rate_limit import QuotaChecker
from features.ui.starter_prompts import build_starter_prompts
from features.ui.workspace import group_chunks_into_guides


def _client_ip(request: Request, trust_proxy: bool) -> str:
    if trust_proxy and (forwarded := request.headers.get("x-forwarded-for")):
        first = forwarded.split(",", 1)[0].strip()
        if first:
            return first
    return request.client.host if request.client else "unknown"


def _filter_area_chunks(chunks: list[KnowledgeChunk], area: str | None, selected: list[str] | None = None) -> list[KnowledgeChunk]:
    allowed = {item.strip() for item in (selected or []) if item.strip()}
    if area and area.strip():
        allowed.add(area.strip())
    return [c for c in chunks if c.area in allowed] if allowed else chunks


def _serialize_results(results: list[SearchResult]) -> list[dict[str, object]]:
    return [{"score": round(r.score, 4), "url": r.chunk.url, "chunk": r.chunk.model_dump(exclude={"embedding"})} for r in results]


def _citation_links(cited_titles: list[str], results: list[SearchResult]) -> list[dict[str, str]]:
    by_title = {r.chunk.title: r.chunk for r in results}
    links: list[dict[str, str]] = []
    seen: set[str] = set()
    for title in cited_titles:
        if title in seen:
            continue
        seen.add(title)
        chunk = by_title.get(title) or next((r.chunk for r in results if r.chunk.title.startswith(title) or title in r.chunk.title), None)
        links.append({"title": title, "url": chunk.url if chunk else "", "area": chunk.area if chunk else "", "doc_id": chunk.doc_id if chunk else ""})
    return links


def build_router(
    published_areas: list[KnowledgeArea],
    chunks: list[KnowledgeChunk],
    settings: dict[str, object],
    route_intent: Callable[..., dict[str, object]],
    search_fn: Callable[..., list[SearchResult]],
    embed_fn: Callable[..., list[float]],
    tutor_fn: Callable[..., TutorResponse],
    estimate_fn: Callable[..., tuple[int, float]],
    quota_check: QuotaChecker,
) -> APIRouter:
    router = APIRouter(prefix="/api/public", tags=["public"])
    url_template = str(settings.get("url_template", ""))
    trust_proxy = bool(settings.get("trust_proxy", True))
    embed_provider = str(settings.get("embed_provider", ""))

    @router.get("/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "mode": "public",
            "areas": [a.name for a in published_areas],
            "doc_count": sum(a.doc_count for a in published_areas),
            "chunk_count": len(chunks),
            "embeddings_active": any(bool(c.embedding) for c in chunks),
            "provider": settings["provider"],
            "model": settings["model"],
        }

    @router.get("/meta")
    def meta(area: str | None = None) -> dict[str, object]:
        scoped = _filter_area_chunks(chunks, area)
        guides = group_chunks_into_guides(scoped)
        by_doc = {(c.area, c.doc_id): c for c in scoped}
        tag_counts: dict[str, int] = {}
        catalog: list[dict[str, object]] = []
        for guide in guides:
            raw_tags = guide.get("tags")
            tags = [str(t) for t in raw_tags] if isinstance(raw_tags, list) else []
            for tag in dict.fromkeys(tags):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            first = by_doc.get((str(guide.get("area", "")), str(guide.get("doc_id", ""))))
            doc_url = resolve_chunk_url(first.model_copy(update={"title": str(guide.get("title", "")), "url": first.url.split("#", 1)[0]}), url_template) if first else ""
            raw_sections = guide.get("sections")
            section_count = len(raw_sections) if isinstance(raw_sections, list) else 0
            catalog.append({"area": guide.get("area", ""), "doc_id": guide.get("doc_id", ""), "subfolder": guide.get("subfolder", ""), "title": guide.get("title", ""), "description": first.description if first else "", "tags": tags, "url": doc_url, "section_count": section_count})
        sorted_tags = [{"name": n, "count": c} for n, c in sorted(tag_counts.items(), key=lambda pair: (-pair[1], pair[0]))]
        return {"areas": [a.model_dump() for a in published_areas], "tags": sorted_tags, "starter_prompts": build_starter_prompts(scoped, [str(t["name"]) for t in sorted_tags]), "guides": catalog, "doc_count": len(catalog), "embeddings_active": any(bool(c.embedding) for c in scoped)}

    @router.get("/search")
    def search(q: str = "", area: str | None = None, tag: str | None = None, doc_id: str | None = None, subfolder: str | None = None, top_k: int = 5) -> dict[str, object]:
        bounded_k = max(1, min(10, top_k))
        routed = route_intent(q, top_k=bounded_k, retrieval_mode="hybrid", rrf_k=60)
        scoped = [c for c in _filter_area_chunks(chunks, area) if matches_scope(c, doc_id, subfolder)]
        query = SearchQuery(query=str(routed["routed_query"]), tag_filter=tag, doc_id=doc_id, subfolder=subfolder, top_k=min(10, int(str(routed["top_k"]))), retrieval_mode="hybrid", rrf_k=int(str(routed["rrf_k"])))
        vec = embed_fn(query.query, provider=embed_provider) if embed_provider and any(bool(c.embedding) for c in scoped) else None
        results = search_fn(query, scoped, query_embedding=vec)
        return {"query": q, "area": area, "is_knowledge_gap": bool(q.strip() and not results), "results": _serialize_results(results), "rag_config": {"top_k": query.top_k, "rrf_k": query.rrf_k, "router_label": routed["label"], "intent": routed["intent"]}}

    @router.post("/ask")
    def ask(payload: PublicAskRequest, request: Request) -> JSONResponse:
        history = [(turn.query, turn.answer) for turn in payload.history[-3:]]
        routed = route_intent(payload.query, history=history, top_k=payload.top_k, retrieval_mode="hybrid", rrf_k=60)
        scoped = [c for c in _filter_area_chunks(chunks, payload.area, payload.areas) if matches_scope(c, payload.doc_id, payload.subfolder) and not is_navigation(c)]
        query = SearchQuery(query=str(routed["routed_query"]), tag_filter=payload.tag, doc_id=payload.doc_id, subfolder=payload.subfolder, top_k=min(8, int(str(routed["top_k"]))), retrieval_mode="hybrid", rrf_k=int(str(routed["rrf_k"])))
        vec = embed_fn(query.query, provider=embed_provider) if embed_provider and any(bool(c.embedding) for c in scoped) else None
        results = search_fn(query, scoped, query_embedding=vec)
        if not results:
            gap = TutorResponse(answer="No matching passages were found in the published knowledge base for this question.", cited_titles=[], knowledge_gap_detected=True, recommended_topics=[])
            return JSONResponse({"query": payload.query, "fallback_mode": None, "limit_notice": None, "tutor": gap.model_dump(), "citations": [], "results": [], "rag_config": {"router_label": routed["label"], "intent": routed["intent"]}})
        _, est_cost = estimate_fn(payload.query + "".join(r.chunk.content for r in results))
        denied = quota_check(_client_ip(request, trust_proxy), est_cost)
        if denied:
            return JSONResponse({"query": payload.query, "fallback_mode": "search_only", "limit_notice": denied, "tutor": None, "citations": [], "results": _serialize_results(results), "rag_config": {"router_label": routed["label"], "intent": routed["intent"]}}, headers={"X-Realm-Fallback": "quota_limit", "Cache-Control": "no-store"})
        tutor_cfg = TutorConfig.model_validate({"provider": settings["provider"], "model": settings["model"], "reasoning_effort": settings["reasoning_effort"], "daily_cloud_request_limit": int(str(settings["global_daily"])), "daily_budget_usd_limit": float(str(settings["global_usd"]))})
        answer = tutor_fn(payload.query, results, tutor_cfg, history=history)
        return JSONResponse({"query": payload.query, "fallback_mode": None, "limit_notice": None, "tutor": answer.model_dump(), "citations": _citation_links(answer.cited_titles, results), "results": _serialize_results(results), "rag_config": {"router_label": routed["label"], "intent": routed["intent"]}}, headers={"Cache-Control": "no-store"})

    @router.get("/graph")
    def graph(area: str | None = None) -> dict[str, object]:
        selected = [a for a in published_areas if not area or a.name == area]
        nodes: list[dict[str, object]] = []
        links: list[dict[str, str]] = []
        for item in selected:
            area_nodes, area_links = area_graph(item, [c for c in chunks if c.area == item.name], url_template=url_template)
            nodes.extend(area_nodes)
            links.extend(area_links)
        return {"nodes": nodes, "links": links, "areas": [a.model_dump() for a in selected]}

    return router
