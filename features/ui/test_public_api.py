"""End-to-end tests for REALM_MODE=public headless read-only API, URLs, and quota guards."""

import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from features.ui import app as ui_app
from features.ui.public_rate_limit import create_memory_limiter, hash_client_ip


def _seed_public_vaults(tmp_path: Path) -> Path:
    docs_dir = tmp_path / "my_docs" / "retrieval"
    docs_dir.mkdir(parents=True)
    (tmp_path / "my_docs" / "00-start-here.md").write_text(
        "# Reading Guide\nTags: navigation\n\n## Chapters\nStart with hybrid search.\n", encoding="utf-8"
    )
    (docs_dir / "hybrid-search.md").write_text(
        "---\ntitle: Hybrid Search & Reranking\ndescription: Combine BM25 and dense vectors.\n"
        "tags: [rag, bm25, rrf]\n---\n\n## Reciprocal Rank Fusion\nRRF fuses lexical and vector rankings cleanly.\n",
        encoding="utf-8",
    )
    guides_dir = tmp_path / "guides"
    guides_dir.mkdir()
    (guides_dir / "overview.md").write_text(
        "---\ntitle: Engine Overview\ndescription: Local-first knowledge architecture.\n"
        "tags: [overview, architecture]\nurl: /docs/guides/overview\n---\n\n## Core Design\nVertical slices stay isolated.\n",
        encoding="utf-8",
    )
    return tmp_path


def test_public_mode_mounts_only_readonly_routes_and_returns_canonical_urls(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _seed_public_vaults(tmp_path)
    monkeypatch.setenv("REALM_PUBLIC_AREAS", "my_docs,guides")
    monkeypatch.setenv("REALM_PUBLIC_PROVIDER", "kimi")
    monkeypatch.setenv("REALM_PUBLIC_MODEL", "kimi-k3.1-pro")
    monkeypatch.setenv("REALM_PUBLIC_URL_TEMPLATE", "/docs/{area}/{doc_id}")
    monkeypatch.setenv("REALM_PUBLIC_ORIGINS", "https://docs.example.com")
    client = TestClient(ui_app.build_public_app(data_dir=root))

    for blocked_method, blocked_path in (
        ("GET", "/"), ("GET", "/api/workspace"), ("POST", "/api/upload"), ("GET", "/api/chats"),
        ("GET", "/api/backup/export"), ("POST", "/api/compliance/scrub"), ("POST", "/api/system/pull-model"),
        ("POST", "/api/audio/transcribe"), ("GET", "/api/models"), ("GET", "/api/keys/status"), ("POST", "/api/keys"),
    ):
        assert client.request(blocked_method, blocked_path).status_code == 404

    health = client.get("/api/public/health")
    assert health.status_code == 200 and health.headers["x-content-type-options"] == "nosniff"
    assert health.headers["x-frame-options"] == "DENY"
    assert health.json()["areas"] == ["my_docs", "guides"] and health.json()["model"] == "kimi-k3.1-pro"

    meta = client.get("/api/public/meta").json()
    assert meta["doc_count"] == 3 and {a["name"] for a in meta["areas"]} == {"my_docs", "guides"}
    hybrid = next(g for g in meta["guides"] if g["doc_id"] == "retrieval/hybrid-search")
    assert hybrid["url"] == "/docs/my_docs/retrieval/hybrid-search"
    assert hybrid["description"] == "Combine BM25 and dense vectors."

    search = client.get("/api/public/search", params={"q": "How does RRF work?", "area": "my_docs"}).json()
    assert search["results"] and search["results"][0]["url"] == "/docs/my_docs/retrieval/hybrid-search#reciprocal-rank-fusion"
    assert "embedding" not in search["results"][0]["chunk"]

    graph = client.get("/api/public/graph").json()
    doc_nodes = [n for n in graph["nodes"] if n["type"] == "doc"]
    assert any(n.get("url") == "/docs/guides/overview" for n in doc_nodes)


def test_public_ask_enforces_locked_provider_citations_and_quota_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _seed_public_vaults(tmp_path)
    monkeypatch.setenv("REALM_PUBLIC_AREAS", "my_docs,guides")
    monkeypatch.setenv("REALM_PUBLIC_PROVIDER", "kimi")
    monkeypatch.setenv("REALM_PUBLIC_MODEL", "kimi-k3.1-pro")
    monkeypatch.setenv("REALM_PUBLIC_URL_TEMPLATE", "/docs/{area}/{doc_id}")
    monkeypatch.setenv("MOONSHOT_API_KEY", "server-kimi-key")
    limiter = create_memory_limiter(ip_rpm=1, ip_daily=5, global_daily=10, global_usd=1.0)
    client = TestClient(ui_app.build_public_app(data_dir=root, quota_check=limiter))

    dispatched: list[dict[str, object]] = []

    def fake_post(url: str, json: dict[str, object], headers: dict[str, str] | None = None, timeout: float = 30.0) -> httpx.Response:
        dispatched.append({"url": url, "body": json, "headers": headers})
        payload = {"answer": "RRF fuses BM25 and vector ranks.", "cited_titles": ["Hybrid Search & Reranking — Reciprocal Rank Fusion"], "knowledge_gap_detected": False, "recommended_topics": ["bm25"]}
        return httpx.Response(200, json={"choices": [{"message": {"content": json_dumps(payload)}}]}, request=httpx.Request("POST", url))

    json_dumps = json.dumps
    monkeypatch.setattr(httpx, "post", fake_post)

    first = client.post("/api/public/ask", json={"query": "How does RRF work?", "area": "my_docs"}, headers={"x-forwarded-for": "203.0.113.5"})
    assert first.status_code == 200
    body = first.json()
    assert body["fallback_mode"] is None and body["tutor"]["answer"].startswith("RRF fuses")
    assert body["citations"][0]["url"] == "/docs/my_docs/retrieval/hybrid-search#reciprocal-rank-fusion"
    assert len(dispatched) == 1 and dispatched[0]["url"] == "https://api.moonshot.ai/v1/chat/completions"

    second = client.post("/api/public/ask", json={"query": "How does RRF work?", "area": "my_docs"}, headers={"x-forwarded-for": "203.0.113.5"})
    assert second.status_code == 200 and second.headers["x-realm-fallback"] == "quota_limit"
    assert second.json()["fallback_mode"] == "search_only" and second.json()["tutor"] is None and len(second.json()["results"]) >= 1
    assert len(dispatched) == 1

    gap = client.post("/api/public/ask", json={"query": "Chapters", "area": "my_docs"}, headers={"x-forwarded-for": "203.0.113.9"})
    assert gap.status_code == 200 and gap.json()["tutor"]["knowledge_gap_detected"] is True and len(dispatched) == 1


def test_memory_limiter_hashes_ip_and_enforces_daily_and_usd_caps() -> None:
    hashed = hash_client_ip("198.51.100.7", salt="salt-a")
    assert "198.51.100.7" not in hashed and hashed == hash_client_ip("198.51.100.7", salt="salt-a")
    limiter = create_memory_limiter(ip_rpm=5, ip_daily=2, global_daily=5, global_usd=0.05)
    assert limiter("198.51.100.7", 0.02) is None
    assert limiter("198.51.100.7", 0.02) is None
    assert "Daily visitor limit" in str(limiter("198.51.100.7", 0.005))
    assert "Daily public AI budget" in str(limiter("198.51.100.8", 0.02))
