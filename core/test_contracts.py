"""Unit tests for the shared AI Engineering data contracts."""

import pytest
from pydantic import ValidationError

from core.contracts import (
    KnowledgeChunk,
    PublicAskRequest,
    SearchQuery,
    SearchResult,
    TutorConfig,
    TutorResponse,
)


def make_chunk() -> KnowledgeChunk:
    """Build a fully populated, valid knowledge chunk."""
    return KnowledgeChunk(
        id="chunk-001",
        title="Hybrid Search",
        file_path="knowledge/hybrid.md",
        content="BM25 and vector search combined.",
        tags=["retrieval", "search"],
        embedding=[0.12, 0.98, 0.04],
    )


def test_knowledge_chunk_valid_creation() -> None:
    chunk = KnowledgeChunk(
        id="chunk-001",
        title="Hybrid Search",
        file_path="knowledge/hybrid.md",
        content="BM25 and vector search combined.",
        tags=["retrieval", "search"],
        embedding=[0.12, 0.98, 0.04],
    )
    assert chunk.id == "chunk-001"
    assert chunk.title == "Hybrid Search"
    assert chunk.file_path == "knowledge/hybrid.md"
    assert chunk.content == "BM25 and vector search combined."
    assert chunk.tags == ["retrieval", "search"]
    assert chunk.embedding is not None
    assert chunk.embedding[0] == pytest.approx(0.12)


def test_knowledge_chunk_embedding_defaults_to_none() -> None:
    chunk = KnowledgeChunk(
        id="chunk-002", title="Vectors", file_path="knowledge/vectors.md", content="x", tags=[]
    )
    assert chunk.embedding is None


def test_search_query_valid_creation_with_defaults() -> None:
    query = SearchQuery(query="hybrid search")
    assert query.query == "hybrid search"
    assert query.top_k == 5
    assert query.tag_filter is None


def test_search_query_valid_creation_with_overrides() -> None:
    query = SearchQuery(query="hybrid search", top_k=12, tag_filter="retrieval")
    assert query.top_k == 12
    assert query.tag_filter == "retrieval"


def test_search_query_allows_empty_query_with_tag_filter() -> None:
    query = SearchQuery(query="", tag_filter="retrieval")
    assert query.query == ""
    assert query.tag_filter == "retrieval"


def test_search_query_allows_empty_query_without_tag() -> None:
    query = SearchQuery(query="")
    assert query.query == ""


def test_search_query_rejects_top_k_above_maximum() -> None:
    with pytest.raises(ValidationError):
        SearchQuery.model_validate({"query": "hybrid search", "top_k": 21})


def test_search_query_rejects_top_k_below_minimum() -> None:
    with pytest.raises(ValidationError):
        SearchQuery.model_validate({"query": "hybrid search", "top_k": 0})


def test_search_result_valid_creation() -> None:
    result = SearchResult(chunk=make_chunk(), score=0.87)
    assert result.chunk.id == "chunk-001"
    assert result.score == pytest.approx(0.87)


def test_search_result_rejects_invalid_score_type() -> None:
    with pytest.raises(ValidationError):
        SearchResult.model_validate({"chunk": make_chunk(), "score": "high"})


def test_tutor_response_valid_creation() -> None:
    response = TutorResponse(
        answer="Use hybrid search to combine BM25 and vector recall.",
        cited_titles=["Hybrid Search"],
        knowledge_gap_detected=False,
        recommended_topics=["reranking"],
    )
    assert response.answer.startswith("Use hybrid")
    assert response.cited_titles == ["Hybrid Search"]
    assert response.knowledge_gap_detected is False
    assert response.recommended_topics == ["reranking"]


def test_tutor_response_rejects_missing_required_fields() -> None:
    with pytest.raises(ValidationError):
        TutorResponse.model_validate({})


def test_tutor_config_defaults_to_local_ollama() -> None:
    config = TutorConfig()
    assert config.provider == "ollama"
    assert config.model == "qwen3:8b"
    assert config.api_key is None


def test_tutor_config_accepts_explicit_provider_credentials() -> None:
    config = TutorConfig(provider="kimi", model="kimi-k3.1-pro", api_key="secret-key", reasoning_effort="low")
    assert config.provider == "kimi"
    assert config.model == "kimi-k3.1-pro"
    assert config.api_key == "secret-key"
    assert config.reasoning_effort == "low"


def test_tutor_config_rejects_unknown_provider() -> None:
    with pytest.raises(ValidationError):
        TutorConfig.model_validate({"provider": "not-a-real-provider"})


def test_public_ask_request_enforces_bounds() -> None:
    req = PublicAskRequest(query="How does RRF work?", area="ai-engineering", top_k=5)
    assert req.query == "How does RRF work?" and req.top_k == 5
    with pytest.raises(ValidationError):
        PublicAskRequest(query="x" * 501)
    with pytest.raises(ValidationError):
        PublicAskRequest(query="ok", top_k=9)