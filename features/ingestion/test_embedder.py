"""Local, incremental batch, and cloud embedding regression tests."""

import httpx
import pytest

from core.contracts import KnowledgeChunk
from features.ingestion.embedder import (
    embed_chunk,
    embed_text,
    hydrate_embeddings,
    reset_ollama_status,
)


def test_embed_chunk_populates_embedding(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_post(url: str, json: dict[str, object]) -> httpx.Response:
        calls.append((url, json))
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2, 0.3]]})

    monkeypatch.setattr(httpx, "post", fake_post)
    chunk = embed_chunk(KnowledgeChunk(id="chunk-001", title="Hybrid Search", file_path="knowledge/folder/hybrid.md", doc_id="folder/hybrid", subfolder="folder", content="BM25 and dense embeddings combined.", tags=["rag"]))
    assert len(calls) == 1
    assert calls[0][0] == "http://127.0.0.1:11434/api/embed"
    assert calls[0][1] == {"model": "nomic-embed-text:v1.5", "input": "BM25 and dense embeddings combined.", "keep_alive": "30s"}
    assert chunk.embedding == [0.1, 0.2, 0.3]
    assert chunk.doc_id == "folder/hybrid" and chunk.subfolder == "folder"


def test_embed_text_fast_fallback_when_ollama_offline_and_cloud_support(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_ollama_status()
    offline_calls = 0

    def failing_post(url: str, json: dict[str, object], timeout: float = 1.5) -> httpx.Response:
        nonlocal offline_calls
        offline_calls += 1
        raise httpx.ConnectError("Ollama offline")

    monkeypatch.setattr(httpx, "post", failing_post)
    assert embed_text("First chunk") == [] and embed_text("Second chunk") == []
    assert offline_calls == 1

    urls: list[str] = []

    def cloud_post(url: str, json: dict[str, object], headers: dict[str, str], timeout: float = 5.0) -> httpx.Response:
        urls.append(url)
        return httpx.Response(200, json={"data": [{"embedding": [0.4, 0.5, 0.6]}]})

    monkeypatch.setattr(httpx, "post", cloud_post)
    assert embed_text("Cloud text", provider="openai", api_key="sk-test") == [0.4, 0.5, 0.6]
    assert embed_text("Gemini text", provider="gemini", api_key="gem-test") == [0.4, 0.5, 0.6]
    assert urls[-1] == "https://generativelanguage.googleapis.com/v1beta/openai/embeddings"


def test_hydrate_embeddings_reuses_cache_and_batches_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_ollama_status()
    cached = [KnowledgeChunk(id="a-0", title="A", file_path="a.md", content="Unchanged text", tags=["rag"], embedding=[0.9, 0.1])]
    fresh = [
        KnowledgeChunk(id="a-0", title="A", file_path="a.md", content="Unchanged text", tags=["rag"]),
        KnowledgeChunk(id="b-0", title="B", file_path="b.md", content="Brand new text", tags=["rag"]),
    ]
    batched: list[object] = []

    def fake_post(url: str, json: dict[str, object], timeout: float = 15.0) -> httpx.Response:
        batched.append(json["input"])
        return httpx.Response(200, json={"embeddings": [[0.2, 0.8]]})

    monkeypatch.setattr(httpx, "post", fake_post)
    hydrated = hydrate_embeddings(fresh, cached, embed_missing=True)
    assert hydrated[0].embedding == [0.9, 0.1]
    assert hydrated[1].embedding == [0.2, 0.8]
    assert batched == ["B\nBrand new text"]
