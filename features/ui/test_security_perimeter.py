"""Regression tests for Batch 1: Security & Privacy Perimeter hardening."""

import io
import json
import zipfile
from pathlib import Path

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from core import model_routing, web_clipper, web_search
from core.agent_presets import AgentPersona
from core.contracts import WorkspaceConfig
from features.ui import app as ui_app
from features.ui import audio_routes, power_routes
from features.ui.public_rate_limit import create_memory_limiter


def test_local_dns_rebinding_csrf_and_default_body_limits(area_client: TestClient) -> None:
    assert area_client.get("/api/workspace", headers={"host": "evil.example:8000"}).status_code == 403
    assert area_client.post("/api/agents", json={"name": "Bad"}, headers={"host": "evil.example:8000"}).status_code == 403
    assert area_client.post("/api/agents", json={"name": "Bad"}, headers={"sec-fetch-site": "cross-site"}).status_code == 403
    assert area_client.post("/api/agents", json={"name": "Bad"}, headers={"origin": "https://evil.example"}).status_code == 403
    assert area_client.post("/api/agents", json={"name": "Bad"}, headers={"origin": "null"}).status_code == 403
    assert area_client.post("/api/agents", content='{"name":"Bad"}', headers={"content-type": "text/plain"}).status_code == 415
    assert area_client.post("/api/agents", content=b"x", headers={"content-length": str(3 * 1024 * 1024), "content-type": "application/json"}).status_code == 413
    ok = area_client.get("/api/workspace", headers={"host": "127.0.0.1:8000"})
    assert ok.status_code == 200


def test_gemini_embeddings_briefing_cloud_and_model_routing_privacy(area_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    area_client.get("/api/guides")
    monkeypatch.setattr(ui_app, "INDEX", [c.model_copy(update={"embedding": [1.0, 0.0]}) for c in ui_app.INDEX])
    called: list[str] = []
    monkeypatch.setattr(ui_app, "embed_text", lambda *a, **kw: called.append("embed") or [1.0, 0.0])
    monkeypatch.setattr(ui_app, "WORKSPACE_CONFIG", WorkspaceConfig(strict_local_only=False, daily_cloud_request_limit=0))
    assert area_client.get("/api/search", params={"q": "Default", "provider": "gemini", "model": "gemini-3.8-flash"}).status_code == 429
    assert called == []

    monkeypatch.setattr(ui_app, "WORKSPACE_CONFIG", WorkspaceConfig(strict_local_only=True, daily_cloud_request_limit=50))
    assert area_client.post("/api/audio/briefing", json={"model": "phonon:cloud"}).status_code == 403
    unpinned = AgentPersona(id="saga", name="Saga")
    with pytest.raises(HTTPException) as exc:
        model_routing.resolve_agent_model(unpinned, WorkspaceConfig(strict_local_only=True), "openai", "gpt-4o-mini", None)
    assert exc.value.status_code == 403


def test_web_clipper_non_global_ips_streaming_cap_and_dangling_symlink(area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for bad in ("http://100.64.0.1/", "http://100.100.100.200/latest", "http://[::ffff:100.64.0.1]/", "http://user:pass@example.com/"):
        with pytest.raises(ValueError):
            web_clipper.validate_clip_url(bad, resolve_dns=False)

    seen: list[tuple[str, str, object]] = []

    class _FakeResp:
        is_redirect, status_code, headers = False, 200, {"content-type": "text/html"}
        def iter_bytes(self):
            yield b"a" * (web_clipper.MAX_CLIP_BYTES // 2 + 1)
            yield b"b" * (web_clipper.MAX_CLIP_BYTES // 2 + 1)
        def close(self) -> None:
            return None

    def fake_send(self: httpx.Client, req: httpx.Request, stream: bool = False) -> _FakeResp:
        seen.append((str(req.url), req.headers.get("host", ""), req.extensions.get("sni_hostname")))
        return _FakeResp()

    with monkeypatch.context() as mp:
        mp.setattr(web_clipper.socket, "getaddrinfo", lambda *_a, **_kw: [(2, 1, 6, "", ("93.184.216.34", 443))])
        mp.setattr(httpx.Client, "send", fake_send)
        with pytest.raises(ValueError, match="2 MB"):
            web_clipper.clip_url_to_markdown("https://example.org/huge")
    assert seen == [("https://93.184.216.34/huge", "example.org", "example.org")]

    outside = tmp_path / "escaped.md"
    (tmp_path / "knowledge_base" / "clipped_guide.md").symlink_to(outside)
    assert area_client.post("/api/workspace", json={"strict_local_only": False}).status_code == 200
    monkeypatch.setattr(power_routes, "clip_url_to_markdown", lambda url: ("Clipped Guide", "# Clipped Guide\n\nBody\n"))
    res = area_client.post("/api/guides/clip-url", json={"url": "https://example.org/post"})
    assert res.status_code == 200 and not outside.exists()


def test_backup_preserves_security_policy_and_scrubs_export(area_client: TestClient) -> None:
    assert area_client.post("/api/workspace", json={"strict_local_only": False, "excluded_subfolders": {"knowledge_base": ["private"], "other": ["secret"]}, "searxng_url": "http://127.0.0.1:8080", "enable_local_api": True}).status_code == 200
    exp = area_client.get("/api/backup/export")
    assert exp.status_code == 200
    with zipfile.ZipFile(io.BytesIO(exp.content)) as zf:
        exported_ws = json.loads(zf.read("workspace.json"))
    assert "other" not in exported_ws["excluded_subfolders"] and exported_ws["searxng_url"] == "" and exported_ws["enable_local_api"] is False

    assert area_client.post("/api/workspace", json={"strict_local_only": False, "enable_local_api": False, "web_search_enabled": False, "excluded_subfolders": {"knowledge_base": ["private"]}}).status_code == 200
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("workspace.json", json.dumps({"knowledge_dir": "knowledge_base", "active_dirs": ["knowledge_base"], "enable_local_api": True, "web_search_enabled": True, "web_search_provider": "searxng", "searxng_url": "https://evil.example", "excluded_subfolders": {}}))
        zf.writestr("imported.md", "# Imported\n## Body\nSafe note.\n")
    res = area_client.post("/api/backup/import", files={"file": ("b.zip", buf.getvalue(), "application/zip")})
    assert res.status_code == 200
    cfg = res.json()["config"]
    assert cfg["enable_local_api"] is False and cfg["web_search_enabled"] is False and cfg["searxng_url"] == ""
    assert cfg["excluded_subfolders"] == {"knowledge_base": ["private"]}


def test_public_api_xff_embedding_quota_file_path_and_url_sanitization(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vault = tmp_path / "guides"
    vault.mkdir()
    (vault / "guide.md").write_text("---\ntitle: Guide\nurl: javascript:alert(1)\n---\n\n## Intro\nHybrid search works.\n", encoding="utf-8")
    monkeypatch.setenv("REALM_PUBLIC_AREAS", "guides")
    monkeypatch.setenv("REALM_PUBLIC_EMBED_PROVIDER", "openai")
    monkeypatch.setenv("REALM_PUBLIC_TRUST_PROXY", "1")
    embed_calls: list[str] = []
    monkeypatch.setattr(ui_app, "embed_text", lambda *a, **kw: embed_calls.append("embed") or [1.0, 0.0])
    limiter = create_memory_limiter(ip_rpm=1, ip_daily=5, global_daily=10, global_usd=1.0)
    app = ui_app.build_public_app(data_dir=tmp_path, quota_check=limiter)
    client = TestClient(app)

    # Oversized body blocked at ASGI guard
    assert client.post("/api/public/ask", content=b"{}", headers={"content-length": str(100 * 1024), "content-type": "application/json"}).status_code == 413
    # file_path stripped and javascript: URL sanitized
    sr = client.get("/api/public/search", params={"q": "Hybrid search"}).json()
    assert sr["results"] and "file_path" not in sr["results"][0]["chunk"] and sr["results"][0]["url"] == ""
    # Rightmost XFF hop prevents spoofing leftmost IP
    r1 = client.post("/api/public/ask", json={"query": "Hybrid search"}, headers={"x-forwarded-for": "1.1.1.1, 203.0.113.5"})
    r2 = client.post("/api/public/ask", json={"query": "Hybrid search"}, headers={"x-forwarded-for": "2.2.2.2, 203.0.113.5"})
    assert r1.status_code == 200 and r2.headers.get("x-realm-fallback") == "quota_limit"


def test_searxng_metadata_block_local_api_token_and_audio_error_sanitization(area_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    bad_meta = WorkspaceConfig(strict_local_only=False, web_search_enabled=True, web_search_provider="searxng", searxng_url="http://169.254.169.254/latest")
    bad_cred = WorkspaceConfig(strict_local_only=False, web_search_enabled=True, web_search_provider="searxng", searxng_url="http://u:p@127.0.0.1:8080")
    assert web_search.search_web_context("test", bad_meta) == [] and web_search.search_web_context("test", bad_cred) == []

    assert area_client.post("/api/workspace/appearance", json={"enable_local_api": True}).status_code == 200
    monkeypatch.setenv("REALM_LOCAL_API_TOKEN", "secret-local-token")
    assert area_client.get("/v1/models").status_code == 401
    assert area_client.get("/v1/models", headers={"authorization": "Bearer wrong"}).status_code == 401
    assert area_client.get("/v1/models", headers={"authorization": "Bearer secret-local-token"}).status_code == 200

    assert area_client.post("/api/workspace", json={"strict_local_only": False}).status_code == 200
    monkeypatch.setattr(audio_routes.httpx, "post", lambda *a, **kw: httpx.Response(401, text="Incorrect API key provided: sk-leaked-prefix"))
    res = area_client.post("/api/audio/speak", json={"text": "Hello", "model": "openai:tts-1", "api_key": "sk-test"})
    assert res.status_code == 401 and "sk-leaked-prefix" not in res.json()["detail"]
