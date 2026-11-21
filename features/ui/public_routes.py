"""Stateless, read-only public API routes for websites (REALM_MODE=public)."""

import os
from collections.abc import Callable
from urllib.parse import urlparse

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from core import contracts
from core.net_security import parse_ip
from core.scope import is_navigation, matches_scope, resolve_chunk_url
from features.ui.graph_data import area_graph
from features.ui.public_rate_limit import QuotaChecker
from features.ui.starter_prompts import build_starter_prompts
from features.ui.workspace import group_chunks_into_guides


def safe_public_url(raw: str) -> str:
    """Allow only http(s) or safe root-relative URLs on public API responses."""
    cleaned = raw.strip()
    if not cleaned or any(ord(c) < 32 for c in cleaned):
        return ""
    if cleaned.startswith("/") and not cleaned.startswith("//"):
        return cleaned
    parsed = urlparse(cleaned)
    return cleaned if parsed.scheme in {"http", "https"} and parsed.netloc else ""

def _is_trusted_proxy_peer(peer: str) -> bool:
    if peer == "testclient" and os.environ.get("PYTEST_CURRENT_TEST"):
        return True
    if peer in {p.strip() for p in os.environ.get("REALM_PUBLIC_TRUSTED_PROXIES", "").split(",") if p.strip()}:
        return True
    ip = parse_ip(peer)
    return bool(ip and (ip.is_loopback or ip.is_private))

def _client_ip(request: Request, trust_proxy: bool, trusted_hops: int = 1) -> str:
    peer = request.client.host if request.client else "unknown"
    if trust_proxy and _is_trusted_proxy_peer(peer) and (forwarded := request.headers.get("x-forwarded-for")):
        parts = [item.strip() for item in forwarded.split(",") if item.strip()]
        if parts:
            return parts[max(0, len(parts) - max(1, trusted_hops))]
    return peer

def _filter_area_chunks(chunks: list[contracts.KnowledgeChunk], area: str | None, selected: list[str] | None = None) -> list[contracts.KnowledgeChunk]:
    allowed = {item.strip() for item in (selected or []) if item.strip()}
    if area and area.strip():
        allowed.add(area.strip())
    return [c for c in chunks if c.area in allowed] if allowed else chunks

def _serialize_results(results: list[contracts.SearchResult]) -> list[dict[str, object]]:
    return [{"score": round(r.score, 4), "url": safe_public_url(r.chunk.url), "chunk": r.chunk.model_dump(exclude={"embedding", "file_path"})} for r in results]

def _citation_links(cited_titles: list[str], results: list[contracts.SearchResult]) -> list[dict[str, str]]:
    by_title, links, seen = {r.chunk.title: r.chunk for r in results}, [], set()
    for title in cited_titles:
        if title in seen:
            continue
        seen.add(title)
        chunk = by_title.get(title) or next((r.chunk for r in results if r.chunk.title.startswith(title) or title in r.chunk.title), None)
        links.append({"title": title, "url": safe_public_url(chunk.url) if chunk else "", "area": chunk.area if chunk else "", "doc_id": chunk.doc_id if chunk else ""})
    return links

def build_router(
    published_areas: list[contracts.KnowledgeArea],
    chunks: list[contracts.KnowledgeChunk],
    settings: dict[str, object],
    route_intent: Callable[..., dict[str, object]],
    search_fn: Callable[..., list[contracts.SearchResult]],
    embed_fn: Callable[..., list[float]],
    tutor_fn: Callable[..., contracts.TutorResponse],
    estimate_fn: Callable[..., tuple[int, float]],
    quota_check: QuotaChecker,
) -> APIRouter:
    router, url_template = APIRouter(prefix="/api/public", tags=["public"]), str(settings.get("url_template", ""))
    trust_proxy, trusted_hops, embed_provider = bool(settings.get("trust_proxy", False)), max(1, int(str(settings.get("trusted_hops", 1)))), str(settings.get("embed_provider", ""))

    @router.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "mode": "public", "areas": [a.name for a in published_areas], "doc_count": sum(a.doc_count for a in published_areas), "chunk_count": len(chunks), "embeddings_active": any(bool(c.embedding) for c in chunks), "provider": settings["provider"], "model": settings["model"]}

    @router.get("/meta")
    def meta(area: str | None = None) -> dict[str, object]:
        scoped = _filter_area_chunks(chunks, area)
        guides, by_doc, tag_counts, catalog = group_chunks_into_guides(scoped), {(c.area, c.doc_id): c for c in scoped}, {}, []
        for guide in guides:
            raw_tags = guide.get("tags")
            tags = [str(t) for t in raw_tags] if isinstance(raw_tags, list) else []
            for tag in dict.fromkeys(tags):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            first = by_doc.get((str(guide.get("area", "")), str(guide.get("doc_id", ""))))
            doc_url = safe_public_url(resolve_chunk_url(first.model_copy(update={"title": str(guide.get("title", "")), "url": first.url.split("#", 1)[0]}), url_template)) if first else ""
            raw_sections = guide.get("sections")
            catalog.append({"area": guide.get("area", ""), "doc_id": guide.get("doc_id", ""), "subfolder": guide.get("subfolder", ""), "title": guide.get("title", ""), "description": first.description if first else "", "tags": tags, "url": doc_url, "section_count": len(raw_sections) if isinstance(raw_sections, list) else 0})
        sorted_tags = [{"name": n, "count": c} for n, c in sorted(tag_counts.items(), key=lambda pair: (-pair[1], pair[0]))]
        return {"areas": [a.model_dump() for a in published_areas], "tags": sorted_tags, "starter_prompts": build_starter_prompts(scoped, [str(t["name"]) for t in sorted_tags]), "guides": catalog, "doc_count": len(catalog), "embeddings_active": any(bool(c.embedding) for c in scoped)}

    @router.get("/search")
    def search(request: Request, q: str = Query(default="", max_length=500), area: str | None = None, tag: str | None = None, doc_id: str | None = None, subfolder: str | None = None, top_k: int = 5) -> dict[str, object]:
        routed = route_intent(q, top_k=max(1, min(10, top_k)), retrieval_mode="hybrid", rrf_k=60)
        scoped = [c for c in _filter_area_chunks(chunks, area) if matches_scope(c, doc_id, subfolder)]
        query = contracts.SearchQuery(query=str(routed["routed_query"]), tag_filter=tag, doc_id=doc_id, subfolder=subfolder, top_k=min(10, int(str(routed["top_k"]))), retrieval_mode="hybrid", rrf_k=int(str(routed["rrf_k"])))
        vec: list[float] | None = None
        if embed_provider and query.query.strip() and any(bool(c.embedding) for c in scoped) and (embed_provider == "ollama" or quota_check(_client_ip(request, trust_proxy, trusted_hops), estimate_fn(query.query)[1]) is None):
            vec = embed_fn(query.query, provider=embed_provider)
        results = search_fn(query, scoped, query_embedding=vec)
        return {"query": q, "area": area, "is_knowledge_gap": bool(q.strip() and not results), "results": _serialize_results(results), "rag_config": {"top_k": query.top_k, "rrf_k": query.rrf_k, "router_label": routed["label"], "intent": routed["intent"]}}

    @router.post("/ask")
    def ask(payload: contracts.PublicAskRequest, request: Request) -> JSONResponse:
        history = [(turn.query, turn.answer) for turn in payload.history[-3:]]
        routed = route_intent(payload.query, history=history, top_k=payload.top_k, retrieval_mode="hybrid", rrf_k=60)
        scoped = [c for c in _filter_area_chunks(chunks, payload.area, payload.areas) if matches_scope(c, payload.doc_id, payload.subfolder) and not is_navigation(c)]
        query = contracts.SearchQuery(query=str(routed["routed_query"]), tag_filter=payload.tag, doc_id=payload.doc_id, subfolder=payload.subfolder, top_k=min(8, int(str(routed["top_k"]))), retrieval_mode="hybrid", rrf_k=int(str(routed["rrf_k"])))
        client_ip, has_vecs = _client_ip(request, trust_proxy, trusted_hops), any(bool(c.embedding) for c in scoped)
        hist_text = "".join(q + a for q, a in history)
        quota_checked, vec = False, None
        if embed_provider and embed_provider != "ollama" and has_vecs:
            quota_checked = True
            combined_est = estimate_fn(query.query)[1] + estimate_fn(payload.query + hist_text + ("x" * 16000))[1]
            if denied := quota_check(client_ip, combined_est):
                results = search_fn(query, scoped, query_embedding=None)
                return JSONResponse({"query": payload.query, "fallback_mode": "search_only", "limit_notice": denied, "tutor": None, "citations": [], "results": _serialize_results(results), "rag_config": {"router_label": routed["label"], "intent": routed["intent"]}}, headers={"X-Realm-Fallback": "quota_limit", "Cache-Control": "no-store"})
            vec = embed_fn(query.query, provider=embed_provider)
        elif embed_provider == "ollama" and has_vecs:
            vec = embed_fn(query.query, provider=embed_provider)
        results = search_fn(query, scoped, query_embedding=vec)
        if not results:
            gap = contracts.TutorResponse(answer="No matching passages were found in the published knowledge base for this question.", cited_titles=[], knowledge_gap_detected=True, recommended_topics=[])
            return JSONResponse({"query": payload.query, "fallback_mode": None, "limit_notice": None, "tutor": gap.model_dump(), "citations": [], "results": [], "rag_config": {"router_label": routed["label"], "intent": routed["intent"]}})
        if not quota_checked and (denied := quota_check(client_ip, estimate_fn(payload.query + hist_text + "".join(r.chunk.content for r in results))[1])):
            return JSONResponse({"query": payload.query, "fallback_mode": "search_only", "limit_notice": denied, "tutor": None, "citations": [], "results": _serialize_results(results), "rag_config": {"router_label": routed["label"], "intent": routed["intent"]}}, headers={"X-Realm-Fallback": "quota_limit", "Cache-Control": "no-store"})
        tutor_cfg = contracts.TutorConfig.model_validate({"provider": settings["provider"], "model": settings["model"], "reasoning_effort": settings["reasoning_effort"], "daily_cloud_request_limit": int(str(settings["global_daily"])), "daily_budget_usd_limit": float(str(settings["global_usd"]))})
        answer = tutor_fn(payload.query, results, tutor_cfg, history=history)
        return JSONResponse({"query": payload.query, "fallback_mode": None, "limit_notice": None, "tutor": answer.model_dump(), "citations": _citation_links(answer.cited_titles, results), "results": _serialize_results(results), "rag_config": {"router_label": routed["label"], "intent": routed["intent"]}}, headers={"Cache-Control": "no-store"})

    @router.get("/graph")
    def graph(area: str | None = None) -> dict[str, object]:
        nodes, links = [], []
        for item in [a for a in published_areas if not area or a.name == area]:
            area_nodes, area_links = area_graph(item, [c for c in chunks if c.area == item.name], url_template=url_template)
            for node in area_nodes:
                if "url" in node:
                    node["url"] = safe_public_url(str(node["url"]))
            nodes.extend(area_nodes)
            links.extend(area_links)
        return {"nodes": nodes, "links": links, "areas": [a.model_dump() for a in published_areas if not area or a.name == area]}

    return router
