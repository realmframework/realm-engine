"""Tests for Phase 6: Audio Briefing, Retrieval X-Ray, Web Clipper, Local OpenAI API, CLI & MCP."""

import io
import json
import wave
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.audio_briefing import stitch_wav_segments
from core.cli_commands import run_cli_ask
from core.mcp_bridge import handle_mcp_request
from core.web_clipper import html_to_clean_markdown, validate_clip_url
from features.ui import power_routes


def _make_tiny_wav(frames: int = 800) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x01\x00" * frames)
    return buf.getvalue()


def test_audio_briefing_wav_stitching_and_route(area_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    seg = _make_tiny_wav(400)
    stitched = stitch_wav_segments([seg, seg], pause_ms=100)
    assert stitched.startswith(b"RIFF") and len(stitched) > len(seg) * 2

    monkeypatch.setattr(power_routes, "_speak_local_phonon", lambda _t, _v, _m="phonon:latest": (seg, "audio/wav"))
    res = area_client.post("/api/audio/briefing", json={"mode": "duo", "host_a": "Blomkvist", "host_b": "Lisbeth"})
    assert res.status_code == 200
    body = res.json()
    assert body["synthesized"] is True and body["audio_base64"] and "**Blomkvist:**" in body["transcript"]


def test_retrieval_xray_pin_and_mute_overrides(area_client: TestClient) -> None:
    assert area_client.post("/api/guides/create", json={"title": "Alpha Zero", "content": "## Details\nKubernetes deployment guide for alpha."}).status_code == 200
    assert area_client.post("/api/guides/create", json={"title": "Beta Notes", "content": "## Details\nKubernetes deployment guide for beta."}).status_code == 200
    res = area_client.post("/api/search/xray", json={"query": "Kubernetes deployment", "top_k": 5})
    assert res.status_code == 200 and len(res.json()["rows"]) >= 2
    assert res.json()["rows"][0]["bm25_rank"] == 1
    muted = area_client.post("/api/search/xray", json={"query": "Kubernetes deployment", "muted_doc_ids": ["alpha_zero"], "pinned_doc_ids": ["beta_notes"]})
    doc_ids = [r["doc_id"] for r in muted.json()["rows"]]
    assert "alpha_zero" not in doc_ids and doc_ids[0] == "beta_notes"


def test_web_clipper_ssrf_guard_local_lock_and_conversion(area_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    for bad in ("file:///etc/passwd", "http://127.0.0.1:8000/secret", "http://localhost/admin", "http://169.254.169.254/latest", "http://10.0.0.1/internal"):
        with pytest.raises(ValueError):
            validate_clip_url(bad, resolve_dns=False)
    title, md = html_to_clean_markdown("<html><head><title>Clean Article</title></head><body><nav>Skip me</nav><h1>Heading</h1><p>Useful offline insight.</p><script>alert(1)</script></body></html>", "https://example.org/post")
    assert title == "Clean Article" and "Useful offline insight." in md and "alert(1)" not in md and "Skip me" not in md

    # Blocked while strict local-only lock is ON
    assert area_client.post("/api/guides/clip-url", json={"url": "https://example.org/post"}).status_code == 403
    assert area_client.post("/api/workspace", json={"strict_local_only": False}).status_code == 200
    monkeypatch.setattr(power_routes, "clip_url_to_markdown", lambda url: ("Clipped Guide", f"---\ntitle: Clipped Guide\n---\n\n# Clipped Guide\n\nClipped from {url}\n"))
    clipped = area_client.post("/api/guides/clip-url", json={"url": "https://example.org/post"})
    assert clipped.status_code == 200 and clipped.json()["doc_id"] == "clipped_guide"


def test_opt_in_openai_local_api_cli_and_mcp_bridge(area_client: TestClient, tmp_path: Path) -> None:
    # Disabled by default
    assert area_client.get("/v1/models").status_code == 403
    assert area_client.post("/v1/chat/completions", json={"model": "realm/saga", "messages": [{"role": "user", "content": "shared"}]}).status_code == 403
    assert area_client.post("/api/workspace/appearance", json={"enable_local_api": True}).status_code == 200
    models = area_client.get("/v1/models")
    assert models.status_code == 200 and any(m["id"] == "realm/saga" for m in models.json()["data"])
    comp = area_client.post("/v1/chat/completions", json={"model": "realm/lisbeth", "messages": [{"role": "user", "content": "Default marker"}]})
    assert comp.status_code == 200 and "[Lisbeth]" in comp.json()["choices"][0]["message"]["content"]

    # CLI ask + MCP JSON-RPC bridge
    cli_out = run_cli_ask(tmp_path, "Default marker", area="knowledge_base")
    assert "REALM Search (knowledge_base)" in cli_out
    init_resp = handle_mcp_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"}, tmp_path)
    init_res = init_resp.get("result") if init_resp else None
    assert isinstance(init_res, dict) and init_res["serverInfo"]["name"] == "realm-engine"
    tools_resp = handle_mcp_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, tmp_path)
    tools_res = tools_resp.get("result") if tools_resp else None
    assert isinstance(tools_res, dict) and len(tools_res["tools"]) == 4
    call_resp = handle_mcp_request({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "realm_search", "arguments": {"query": "Default marker", "area": "knowledge_base"}}}, tmp_path)
    call_res = call_resp.get("result") if call_resp else None
    assert isinstance(call_res, dict) and len(json.loads(call_res["content"][0]["text"])) >= 1
    html = area_client.get("/").text
    for marker in ('id="briefing-modal" closedby="any"', 'id="voice-loop-toggle"', 'id="local-api-toggle"', 'id="clip-url-input"'):
        assert marker in html
