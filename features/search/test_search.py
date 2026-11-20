"""Unit tests for the hybrid search service."""

from pathlib import Path

import pytest

from core.contracts import KnowledgeChunk, SearchQuery
from core.db import load_chunks, save_chunks
from features.search.router import route_query_intent
from features.search.service import cosine_similarity, hybrid_search, keyword_score


def make_chunk(
    title: str = "Hybrid Search",
    tags: list[str] | None = None,
    content: str = "BM25 and dense retrieval",
    embedding: list[float] | None = None,
) -> KnowledgeChunk:
    return KnowledgeChunk(
        id="chunk-001",
        title=title,
        file_path="knowledge/hybrid.md",
        content=content,
        tags=["rag"] if tags is None else tags,
        embedding=[0.9, 0.1] if embedding is None else embedding,
    )


def test_save_and_load_chunks(tmp_path: Path) -> None:
    chunks = [make_chunk()]
    db_file = tmp_path / "chunks.json"
    save_chunks(chunks, db_file)
    loaded = load_chunks(db_file)
    assert len(loaded) == 1
    assert loaded[0].id == "chunk-001"
    assert loaded[0].title == "Hybrid Search"
    assert loaded[0].tags == ["rag"]


def test_load_chunks_missing_file_returns_empty(tmp_path: Path) -> None:
    assert load_chunks(tmp_path / "missing.json") == []


def test_cosine_similarity() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert cosine_similarity([1.0], [1.0, 2.0]) == 0.0
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0


def test_keyword_score_rewards_title_and_tag_matches() -> None:
    chunk = make_chunk(title="Hybrid Search", tags=["hybrid", "retrieval"])
    assert keyword_score("hybrid retrieval", chunk) > keyword_score("dense", chunk)


def test_hybrid_search_filters_by_tag() -> None:
    tagged = make_chunk(title="Hybrid Search", tags=["rag"])
    other = KnowledgeChunk(
        id="chunk-002",
        title="Hybrid Security",
        file_path="knowledge/security.md",
        content="hybrid threat detection",
        tags=["security"],
    )
    results = hybrid_search(SearchQuery(query="hybrid", top_k=5, tag_filter="RAG"), [tagged, other])
    assert [result.chunk.id for result in results] == ["chunk-001"]


def test_hybrid_search_tag_only_returns_matching_chunks() -> None:
    tagged = make_chunk(title="Hybrid Search", tags=["rag"])
    other = KnowledgeChunk(
        id="chunk-002",
        title="Hybrid Security",
        file_path="knowledge/security.md",
        content="hybrid threat detection",
        tags=["security"],
    )
    results = hybrid_search(SearchQuery(query="", top_k=5, tag_filter="RAG"), [tagged, other])
    assert len(results) == 1
    assert results[0].chunk.id == "chunk-001"
    assert results[0].score == 1.0


def test_hybrid_search_empty_query_without_tag_returns_empty() -> None:
    assert hybrid_search(SearchQuery(query="", top_k=5), [make_chunk()]) == []


def test_hybrid_search_keyword_only_ranks_by_score() -> None:
    strong = make_chunk(title="Hybrid Search", content="BM25 and dense retrieval")
    weak = KnowledgeChunk(
        id="chunk-002",
        title="Unrelated Notes",
        file_path="knowledge/notes.md",
        content="nothing relevant here",
        tags=["notes"],
    )
    results = hybrid_search(SearchQuery(query="hybrid retrieval", top_k=5), [weak, strong])
    assert len(results) == 1
    assert results[0].chunk.id == "chunk-001"


def test_hybrid_search_combines_keyword_and_vector_scores() -> None:
    chunk = make_chunk(title="Hybrid Search", content="BM25 and dense retrieval", embedding=[0.8, 0.2])
    results = hybrid_search(SearchQuery(query="hybrid search", top_k=5), [chunk], query_embedding=[0.9, 0.1])
    assert len(results) == 1
    assert results[0].score > keyword_score("hybrid search", chunk)


def test_retrieval_modes_with_empty_embeddings_and_custom_top_k() -> None:
    c1 = KnowledgeChunk(id="c1", title="BM25 Search", file_path="a.md", content="lexical search ranking", tags=["rag"], embedding=[])
    c2 = KnowledgeChunk(id="c2", title="RRF Fusion", file_path="b.md", content="lexical and vector search", tags=["rag"], embedding=[])
    c3 = KnowledgeChunk(id="c3", title="Dense Vectors", file_path="c.md", content="embedding search index", tags=["rag"], embedding=[])
    lex = hybrid_search(SearchQuery(query="search", top_k=2, retrieval_mode="lexical"), [c1, c2, c3], query_embedding=[])
    hyb = hybrid_search(SearchQuery(query="search", top_k=2, retrieval_mode="hybrid", rrf_k=40), [c1, c2, c3], query_embedding=[])
    vec_fallback = hybrid_search(SearchQuery(query="search", top_k=2, retrieval_mode="vector"), [c1, c2, c3], query_embedding=[])
    assert len(lex) == 2 and lex[0].chunk.id == "c1"
    assert len(hyb) == 2 and hyb[0].chunk.id == "c1"
    assert len(vec_fallback) == 2 and vec_fallback[0].chunk.id == "c1"


def test_route_query_intent_exact_deep_and_followup() -> None:
    exact = route_query_intent("test_vertical_slice_isolation --strict")
    assert exact["intent"] == "exact_lookup" and exact["rrf_k"] == 30 and exact["label"] == "Auto-Router: Exact Lookup"
    deep = route_query_intent("Compare BM25 lexical search and dense vector embeddings in RAG architecture")
    assert deep["intent"] == "deep_synthesis" and deep["top_k"] == 7 and deep["label"] == "Auto-Router: Deep Synthesis"
    followup = route_query_intent("How does RRF combine it?", history=[("What is BM25 lexical search?", "BM25 is keyword scoring.")])
    assert followup["intent"] == "contextual_followup" and "BM25" in str(followup["routed_query"])
    assert followup["label"] == "Auto-Router: Contextual Follow-up"


@pytest.mark.parametrize("mode", ["lexical", "vector", "hybrid"])
def test_scope_is_applied_before_ranking(mode: str) -> None:
    chunks = [make_chunk(content="retrieval " * (100 - i)).model_copy(update={"id": str(i), "doc_id": doc, "subfolder": folder}) for i, (doc, folder) in enumerate([
        ("outside", ""), ("careful/other", "careful"), ("care/guide", "care"), ("care/nested/guide", "care/nested"),
    ])]
    for scope, expected in [({"doc_id": "care/guide"}, {"care/guide"}), ({"subfolder": "care"}, {"care/guide", "care/nested/guide"}), ({"subfolder": ""}, {"outside"}), ({"doc_id": "missing"}, set())]:
        request = SearchQuery.model_validate({"query": "retrieval", "retrieval_mode": mode, "top_k": 15, **scope})
        hits = hybrid_search(request, chunks, query_embedding=[0.9, 0.1])
        assert {r.chunk.doc_id for r in hits} == expected
    assert hybrid_search(SearchQuery(query="retrieval", subfolder="care", doc_id="outside"), chunks) == []
    assert hybrid_search(SearchQuery(query="retrieval", doc_id="hybrid"), [make_chunk()]) == []


def test_bm25_strips_punctuation_and_ranks_rare_terms_higher() -> None:
    c_rare = make_chunk(title="Guide", tags=["ai"], content="System architecture using pgvector.").model_copy(update={"id": "rare"})
    c_common = make_chunk(title="Guide", tags=["ai"], content="System overview and general system notes.").model_copy(update={"id": "common"})
    c_extra = make_chunk(title="Guide", tags=["ai"], content="Another system design note.").model_copy(update={"id": "extra"})
    hits = hybrid_search(SearchQuery(query="What is pgvector?", retrieval_mode="lexical"), [c_common, c_extra, c_rare])
    assert [hit.chunk.id for hit in hits] == ["rare"]
