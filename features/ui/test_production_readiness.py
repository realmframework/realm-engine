"""Regression tests for P1/P2/P3/P5 HTTP perimeter, Public API, embeddings, diagnostics, and Quick Guide."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.contracts import (
    ChatSession,
    ChatTurn,
    ChatTurnRequest,
    KnowledgeChunk,
    SearchResult,
    WorkspaceConfig,
)
from core.version import APP_VERSION
from features.ui import (
    app as ui_app,
)
from features.ui import (
    backup_routes,
    chat_store,
    openai_local_routes,
    public_config,
    query_engine,
)
from features.ui.template import HTML_PAGE


def test_http_perimeter_headers_csrf_host_and_safe_422() -> None:
    client = TestClient(ui_app.app)
    res = client.get("/healthz")
    assert res.status_code == 200 and res.json()["version"] == APP_VERSION
    assert "default-src 'self'" in res.headers.get("content-security-policy", "")
    assert res.headers.get("cross-origin-resource-policy") == "same-origin"
    assert res.headers.get("cross-origin-opener-policy") == "same-origin"
    api = client.get("/api/diagnostics")
    assert api.status_code == 200 and api.headers.get("cache-control") == "no-store"
    assert client.get("/api/diagnostics", headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert client.post("/api/workspace", json={}, headers={"Sec-Fetch-Site": "same-site"}).status_code == 403
    assert client.post("/api/workspace", json={}, headers={"Referer": "https://evil.example/page"}).status_code == 403
    assert client.get("/healthz", headers={"Host": "evil.example:8000"}).status_code == 403
    bad = client.post("/api/workspace", json={"daily_cloud_request_limit": "not-an-int"})
    assert bad.status_code == 422
    assert all("input" not in err for err in bad.json().get("detail", []))


def test_diagnostics_endpoint_is_sanitized_and_includes_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-value-never-leak-99999")
    client = TestClient(ui_app.app)
    res = client.get("/api/diagnostics")
    assert res.status_code == 200
    assert res.json()["version"] == APP_VERSION
    assert "sk-secret-value" not in res.text


def test_public_mode_fail_closed_exclusions_and_safe_graph_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REALM_PUBLIC_AREAS", raising=False)
    area = tmp_path / "my_docs"
    (area / "Private").mkdir(parents=True)
    (area / "Private" / "secret.md").write_text("# Secret\nInternal only", encoding="utf-8")
    (area / "pub.md").write_text("# Public Guide\nSafe content", encoding="utf-8")
    (tmp_path / "workspace.json").write_text('{"excluded_subfolders": {"my_docs": ["private"]}}', encoding="utf-8")
    pub_empty, snap_empty = public_config.load_public_snapshot(tmp_path, [], "/docs/{area}/{doc_id}", lambda _d: [])
    assert pub_empty == [] and snap_empty == []
    monkeypatch.setenv("REALM_PUBLIC_AREAS", "my_docs")
    monkeypatch.setenv("REALM_PUBLIC_URL_TEMPLATE", "javascript:alert({doc_id})")
    client = TestClient(ui_app.build_public_app(data_dir=tmp_path))
    assert client.get("/healthz").json()["version"] == APP_VERSION
    meta = client.get("/api/public/meta").json()
    guide_ids = [g["doc_id"] for g in meta["guides"]]
    assert "pub" in guide_ids and all("secret" not in gid for gid in guide_ids)
    graph = client.get("/api/public/graph").json()
    assert all(not str(n.get("url", "")).lower().startswith("javascript:") for n in graph["nodes"])


def test_openai_local_routes_fail_closed_without_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    assert not openai_local_routes._is_loopback_client("")
    assert not openai_local_routes._is_loopback_client("203.0.113.10")
    assert not openai_local_routes._is_loopback_client("testclient")
    assert openai_local_routes._is_loopback_client("127.0.0.1")


def test_query_engine_chat_store_and_backup_strip_embeddings_and_host_paths(tmp_path: Path) -> None:
    chunk = KnowledgeChunk(
        id="c1",
        doc_id="sub/d1",
        title="Guide",
        content="Body text",
        tags=[],
        file_path="/Users/alice/private/sub/d1.md",
        embedding=[0.5] * 64,
    )
    sr = SearchResult(chunk=chunk, score=0.9)
    req = ChatTurnRequest(query="hello")
    cfg = WorkspaceConfig(app_title="T", knowledge_dir="kb")
    _, out, _ = query_engine.retrieve(
        req,
        [chunk],
        [],
        lambda q, **_k: {"routed_query": q, "top_k": 5, "retrieval_mode": "lexical", "rrf_k": 60, "label": "Direct"},
        lambda *_a, **_k: [sr],
        lambda *_a, **_k: [],
        policy=cfg,
    )
    assert out[0].chunk.embedding is None
    sess = ChatSession(
        chat_id="s1",
        title="Chat",
        area="kb",
        updated_at="2026-01-01T00:00:00Z",
        turns=[ChatTurn(query="hello", results=[sr], created_at="2026-01-01T00:00:00Z")],
    )
    chat_store.save_chats([sess], tmp_path / "chats.json")
    saved = (tmp_path / "chats.json").read_text(encoding="utf-8")
    assert "[0.5" not in saved
    dumped = backup_routes._portable_chat_dump(sess)
    turn0 = dumped["turns"][0]  # type: ignore[index]
    chunk0 = turn0["results"][0]["chunk"]
    assert chunk0["embedding"] is None and chunk0["file_path"] == "sub/d1.md"


def test_upgraded_four_tab_quick_guide_and_diagnostics_ui_markers() -> None:
    for marker in (
        'id="guide-modal"',
        'data-guide-tab="shortcuts"',
        'data-guide-tab="chat"',
        'data-guide-tab="library"',
        'data-guide-tab="privacy"',
        'id="settings-open-guide-btn"',
        'id="system-diagnostics-details"',
        'id="copy-diagnostics-btn"',
        "bindGuideUX",
    ):
        assert marker in HTML_PAGE
