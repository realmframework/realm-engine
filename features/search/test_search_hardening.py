"""Regression tests for hybrid RRF ranking, NaN safety, and router precision (Batch 3)."""

from core.contracts import KnowledgeChunk, SearchQuery
from features.search.router import route_query_intent
from features.search.service import cosine_similarity, hybrid_search


def test_hybrid_rrf_does_not_rank_zero_lexical_chunk_above_top_lexical_match() -> None:
    chunks = [
        KnowledgeChunk(id="aaa_irrelevant", title="Cooking", content="Pasta recipe.", tags=[], file_path="a.md", embedding=[0.2, 0.98]),
        KnowledgeChunk(id="zzz_exact", title="Kubernetes Ingress", content="Kubernetes ingress controller guide.", tags=["k8s"], file_path="z.md", embedding=[0.1, 0.99]),
    ]
    res = hybrid_search(SearchQuery(query="Kubernetes ingress", top_k=2, retrieval_mode="hybrid"), chunks, query_embedding=[0.0, 1.0])
    assert res[0].chunk.id == "zzz_exact"


def test_cosine_similarity_rejects_nan_and_inf() -> None:
    assert cosine_similarity([float("nan"), 1.0], [1.0, 1.0]) == 0.0
    assert cosine_similarity([float("inf"), 1.0], [1.0, 1.0]) == 0.0


def test_router_slash_terms_and_deep_synthesis() -> None:
    decision = route_query_intent("Compare CI/CD architecture tradeoffs versus manual deployment")
    assert decision["intent"] == "deep_synthesis"
    path_decision = route_query_intent("Check /etc/nginx configuration")
    assert path_decision["intent"] == "exact_lookup"
