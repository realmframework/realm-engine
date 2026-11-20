"""Three reproducible in-process retrieval diagnostics against the active index."""

from collections.abc import Callable
from pathlib import Path
from time import perf_counter

from core.contracts import KnowledgeChunk, SearchQuery, SearchResult

OOD_QUERY = "quantum_bananas_xyz_999"


def benchmark(chunks: list[KnowledgeChunk], base: Path, search: Callable[..., list[SearchResult]]) -> dict[str, object]:
    sample = chunks[0] if chunks else None
    query = sample.title if sample else OOD_QUERY
    results: list[SearchResult] = []
    latencies: dict[str, float] = {}
    verified: list[bool] = []
    for mode in ("lexical", "hybrid"):
        request = SearchQuery(query=query, retrieval_mode=mode, top_k=3)
        started = perf_counter()
        hits = search(request, chunks, query_embedding=sample.embedding if sample and mode == "hybrid" else None)
        latencies[mode] = round((perf_counter() - started) * 1000, 4)
        results.extend(hits)
        verified.append(bool(sample and hits and hits[0].chunk.id == sample.id))
    unique = {r.chunk.id: r.chunk for r in results}
    traceable = sum(bool(c.doc_id and " — " in c.title and c.title.split(" — ", 1)[1].strip() and Path(c.file_path).is_file() and Path(c.file_path).resolve().is_relative_to(base.resolve()) and c.doc_id == Path(c.file_path).resolve().relative_to(base.resolve()).with_suffix("").as_posix()) for c in unique.values())
    coverage = round(100 * traceable / len(unique), 2) if unique else 0.0
    out_of_domain = search(SearchQuery(query=OOD_QUERY, retrieval_mode="hybrid"), chunks)
    passed = bool(sample and all(verified) and coverage == 100 and not out_of_domain)
    return {"status": "PASS" if passed else "NO DATA" if not sample else "WARN", "latency_ms": round(sum(latencies.values()), 4), "latency_breakdown_ms": latencies, "top_chunk_verified": all(verified) if sample else None, "recall_at_1": float(sum(verified) / 2) if sample else None, "provenance_coverage": coverage, "retrieved_sources": len(unique), "traceable_sources": traceable, "hallucination_refusal_gate": not out_of_domain, "is_knowledge_gap": not out_of_domain, "out_of_domain_query": OOD_QUERY, "active_retrieval_tier": "hybrid_local" if any(c.embedding for c in chunks) else "lexical_zero_gpu", "generation_evaluated": False, "ood_mode": "lexical fallback; no embedding or model call"}
