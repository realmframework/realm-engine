"""Integration tests for Format Studio, Free Chat, mid-chat attachments, Context Compaction & PDF export."""

from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from features.ui import app as ui_app


def test_formats_api_and_millennium_themes_ui(area_client: TestClient) -> None:
    listed = area_client.get("/api/formats")
    assert listed.status_code == 200
    fmt_ids = {f["id"] for f in listed.json()["formats"]}
    for expected in ("ireb_srs", "lisbeth_dossier", "blomkvist_article", "milton_security", "erika_brief", "annika_legal", "plague_postmortem", "palmgren_review"):
        assert expected in fmt_ids

    saved = area_client.post(
        "/api/formats",
        json={"name": "Quick 4W", "sections": "When\nWho\nWhat\nHow Much", "category": "Custom", "instructions": "Keep concise."},
    )
    assert saved.status_code == 200 and saved.json()["format"]["id"] == "quick_4w"
    assert area_client.delete("/api/formats/ireb_srs").status_code == 400
    assert area_client.delete("/api/formats/quick_4w").json()["deleted"] is True

    html = area_client.get("/").text
    for marker in (
        '"Milton"', '"Dragon"', '"Hacker"', '"Stieg"', '"Annika"', '"Palmgren"',
        'id="format-studio-modal"', 'id="clear-areas-btn"', 'id="sidebar-formats-btn"',
        'id="upload-mode-chat-btn"', 'id="inspector-toggle-btn"', 'id="inspector-sidebar"',
        "Link Local Folder", "Answer in Format", "Answer Formats", "runCompactContext", "runFormatSynthesis", "exportFullChatPdf",
    ):
        assert marker in html
    assert "Open Folder as Vault" not in html and "inspector-attach-file-btn" not in html and "escapeHtml(loadCopy)" not in html


def test_free_chat_mid_chat_attach_thinking_compact_synthesize_and_pdf(
    area_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_stream_messages(*_args: object, **_kwargs: object) -> AsyncIterator[dict[str, object]]:
        yield {"type": "thinking", "delta": "Analyzing user notes and requirements..."}
        yield {"type": "token", "delta": "## 1. Context & Scope\nGrounded synthesis from chat notes."}
        yield {"type": "meta", "provider": "ollama", "model": "qwen3:8b", "prompt_tokens": 180, "completion_tokens": 42, "thinking_tokens": 12, "duration_ms": 210, "tokens_per_sec": 200.0}

    monkeypatch.setattr("features.tutor_agent.streaming.stream_messages_events", fake_stream_messages)
    # Re-create app routers using monkeypatched stream fn via existing client routes:
    # 1) Attach file directly into a Free Chat before or during conversation
    att = area_client.post(
        "/api/chats/free-req-1/attach",
        files=[("files", ("notes.txt", b"Client wants GDPR export by Q3 with 5k EUR budget.", "text/plain"))],
        data={"free_chat": "true"},
    )
    assert att.status_code == 200
    assert att.json()["attached_notes"][0]["name"] == "notes.txt"

    # 2) Free Chat streaming turn works WITHOUT any vault match and captures thinking + telemetry
    async def fake_stream_tutor(*_args: object, free_chat: bool = False, **_kwargs: object) -> AsyncIterator[dict[str, object]]:
        assert free_chat is True
        yield {"type": "thinking", "delta": "Checking "}
        yield {"type": "thinking", "delta": "budget constraint."}
        yield {"type": "token", "delta": "Budget is 5k EUR for Q3 GDPR export."}
        yield {"type": "meta", "provider": "ollama", "model": "qwen3:8b", "prompt_tokens": 120, "completion_tokens": 25, "thinking_tokens": 8, "duration_ms": 150, "tokens_per_sec": 166.7}

    monkeypatch.setattr(ui_app, "stream_tutor_events", fake_stream_tutor)
    monkeypatch.setattr(ui_app, "stream_messages_events", fake_stream_messages)

    # Test via fresh local app wired to patched streams
    fresh_client = TestClient(ui_app._build_local_app())
    stream_res = fresh_client.post(
        "/api/chats/free-req-1/turn/stream",
        json={"query": "Summarize the client notes", "free_chat": True, "ask_tutor": True},
    )
    assert stream_res.status_code == 200
    assert "event: thinking" in stream_res.text and "event: telemetry" in stream_res.text and "event: done" in stream_res.text
    assert any(c["chat_id"] == "free-req-1" for c in fresh_client.get("/api/chats?free_chat=true").json())

    # 3) On-demand Format Synthesis appends a formatted Blueprint turn
    synth = fresh_client.post(
        "/api/chats/free-req-1/synthesize",
        json={"format_id": "ireb_srs", "extra_instruction": "Focus on GDPR", "free_chat": True},
    )
    assert synth.status_code == 200 and "event: done" in synth.text
    session = fresh_client.get("/api/chats/free-req-1?free_chat=true").json()
    assert session["turns"][0]["thinking"] == "Checking budget constraint."
    assert len(session["turns"]) == 2 and session["turns"][1]["format_name"] == "Requirements Spec (IEEE / IREB SRS)"

    # 4) Context Meter, Compress Context & Clear Context
    ctx = fresh_client.get("/api/chats/free-req-1/context?free_chat=true")
    assert ctx.status_code == 200 and ctx.json()["context_usage"]["turns_in_context"] == 2
    comp = fresh_client.post("/api/chats/free-req-1/compact", json={"free_chat": True})
    assert comp.status_code == 200 and comp.json()["context_usage"]["is_compacted"] is True
    cleared = fresh_client.post("/api/chats/free-req-1/clear-context", json={"free_chat": True})
    assert cleared.status_code == 200 and cleared.json()["context_usage"]["turns_in_context"] == 0

    # 5) PDF export for single synthesized turn AND full chat
    single_pdf = fresh_client.post("/api/export/pdf", json={"chat_id": "free-req-1", "turn_index": 1, "free_chat": True})
    assert single_pdf.status_code == 200 and single_pdf.headers["content-type"] == "application/pdf" and single_pdf.content.startswith(b"%PDF-")
    chat_pdf = fresh_client.post("/api/export/pdf", json={"chat_id": "free-req-1", "free_chat": True})
    assert chat_pdf.status_code == 200 and chat_pdf.content.startswith(b"%PDF-")

    # 6) Attach a Vault mid-chat migrates the open Free Chat cleanly into knowledge_base
    migrated = fresh_client.post("/api/chats/free-req-1/attach-vault", json={"area": "knowledge_base"})
    assert migrated.status_code == 200 and migrated.json()["area"] == "knowledge_base"
    assert fresh_client.get("/api/chats/free-req-1").status_code == 200
