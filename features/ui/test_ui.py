"""Unit tests for the AI Engineering web UI composition root."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.contracts import WorkspaceConfig
from features.tutor_agent.service import build_tutor_messages, clean_tutor_answer
from features.ui import app as ui_app
from features.ui import chat_store, workspace
from features.ui.app import app

client = TestClient(app)


def test_markdown_citations_chunks_header_and_rag_modal_in_ui() -> None:
    response = client.get("/")
    assert response.status_code == 200
    for expected in (
        "formatMarkdown", "source passages", "How the RAG Pipeline Works", "RAG &amp; Search",
        "Reset Sliders to Default", 'id="settings-panel-rag"', '<dialog id="onboarding-modal" closedby="any"',
        '<dialog id="upload-modal" closedby="any"', "Add Documents", "Anonymize personal names, emails, IBANs &amp; phones (GDPR)",
        "Extracts text into a Markdown guide inside your active Library folder.", "Upload &amp; Index", "<span>Graph View</span>",
        "knowledge-graph-canvas", "graph-filter-input", "Reset View", "▶ Test", "Auto-Router: Deep Synthesis", "Alfie",
        "OpenAI TTS (tts-1 — Alloy / Nova / Echo)", "ElevenLabs TTS", "Disabled (Hide Voice Controls)",
        "Voice Output (Phonon TTS)", 'id="tts-model"', 'id="tts-voice"', "Anonymize (GDPR)", "guide-delete-btn",
        "Local execution — data stays on this device", "Tutor Synthesis vs. Raw Search Only", 'placeholder="Ask anything..."',
        'id="mic-btn"', "data-speak-turn", "mode: hybrid · top-k: 5 · temp: 0.2", "upload-dropzone",
        "Reciprocal Rank Fusion (RRF)", "<span>Library</span>", "<span>Settings</span>",
        "Privacy &amp; GDPR Audit", "More ideas", 'id="settings-tabs"',
        '<dialog id="settings-modal" closedby="any"', "showModal()", "startViewTransition", "scrollIntoViewAsync", "<search ",
    ):
        assert expected in response.text
    for forbidden in ("📚", "🎛", "🛡️", "🔒", "✨", "Workspace &amp; Keys", 'id="ask-toggle"', "upload-tags-input", "speechSynthesis", "Grub the Ogre", chr(0x1F4C1)):
        assert forbidden not in response.text
    assert clean_tutor_answer("Answer body.\n\n**Sources:**\n- Doc 1") == "Answer body."


def test_multi_turn_chats_and_rag_studio_params(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(chat_store, "CHATS_FILE", tmp_path / "chats.json")
    s_res = client.get("/api/search?q=hybrid+search&top_k=2&retrieval_mode=lexical&rrf_k=40&temperature=0.6").json()
    assert 0 < len(s_res["results"]) <= 2 and s_res["rag_config"]["top_k"] == 2
    turn1 = client.post("/api/chats/test-chat-1/turn", json={"query": "What is BM25?", "ask_tutor": True, "top_k": 2, "retrieval_mode": "hybrid", "rrf_k": 45, "temperature": 0.4})
    assert turn1.status_code == 200 and 0 < len(turn1.json()["turns"][0]["results"]) <= 2
    turn2 = client.post("/api/chats/test-chat-1/turn", json={"query": "How does RRF combine it?", "ask_tutor": True})
    assert turn2.status_code == 200 and len(turn2.json()["turns"]) == 2
    assert len(client.get("/api/chats").json()) == 1 and client.delete("/api/chats/test-chat-1").json()["deleted"] is True
    assert "Recent Conversation History:" in build_tutor_messages("Follow-up?", [], history=[("First?", "First answer.")])[1]["content"]


@pytest.mark.parametrize(("filename", "tag", "query", "sections"), [
    ("agent_skills.md", "context-engineering", "YAML Frontmatter Discovery", ["Overview", "YAML Frontmatter Discovery", "Progressive Loading", "Boundaries"]),
    ("privacy_rag.md", "governance", "Filename Sanitization", ["Overview", "Filename Sanitization", "Local Execution", "Voice Pipeline"]),
])
def test_phase_five_guides_index_and_search(tmp_path: Path, filename: str, tag: str, query: str, sections: list[str], monkeypatch: pytest.MonkeyPatch) -> None:
    from features.ingestion.parser import parse_markdown_file

    guide_file = tmp_path / filename
    body = f"# Synthetic Guide\nTags: {tag}\n\n" + "\n\n".join(f"## {sec}\nDetailed notes on {sec}." for sec in sections)
    guide_file.write_text(body, encoding="utf-8")
    chunks = parse_markdown_file(guide_file)
    assert len(chunks) == 4 and all(c.content.strip() and tag in c.tags for c in chunks)
    monkeypatch.setattr(ui_app, "INDEX", chunks)
    response = client.get("/api/guides", params={"tag": tag})
    assert response.status_code == 200
    guide = response.json()[0]
    assert len(guide["sections"]) == 4 and guide["file_path"] == chunks[0].file_path
    result = client.get("/api/search", params={"q": query, "retrieval_mode": "lexical"})
    assert result.status_code == 200 and result.json()["results"][0]["chunk"]["id"] == chunks[1].id


@pytest.mark.parametrize("anonymize", [False, True])
def test_chat_study_notes_save_in_active_library(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, anonymize: bool) -> None:
    monkeypatch.setattr(workspace, "resolve_safe_knowledge_dir", lambda *_a, **_kw: tmp_path)
    monkeypatch.setattr(ui_app, "WORKSPACE_CONFIG", WorkspaceConfig(knowledge_dir="study", anonymize_uploads=anonymize))
    monkeypatch.setattr(ui_app, "INDEX", [])
    content = "# Conversation\nTags: study-notes\n\n## Turn 1\n### User Question\nHow does retrieval work?\n\n### AI Tutor Answer\nGrounded answer.\n\n### Source Citations\n1. Guide — Section\n"
    content += "\nContact learner@example.invalid\n"
    response = client.post("/api/upload", json={"filename": "conversation-study-notes-unique.md", "content": content, "tags": "study-notes"})
    assert response.status_code == 200 and response.json()["doc_count"] == 1
    saved = (tmp_path / "conversation-study-notes-unique.md").read_text(encoding="utf-8")
    assert saved == (content.replace("learner@example.invalid", "[REDACTED_EMAIL]") if anonymize else content)
    assert response.json()["redacted_count"] == int(anonymize)
    guide = client.get("/api/guides?tag=study-notes").json()[0]
    assert guide["title"] == "Conversation" and "Grounded answer." in guide["sections"][0]["content"]
    assert client.get("/api/workspace").json()["doc_count"] == 1
    assert client.get("/api/search?q=Grounded&retrieval_mode=lexical").json()["results"]
    assert client.get("/api/chats/missing-session").status_code == 404


def test_scoped_api_and_live_compliance_audit(area_client: TestClient) -> None:
    uploaded = area_client.post("/api/upload", json={"filename": "care.md", "subfolder": "care/nested", "content": "# Care\nTags: care\n\n## Treatment\nDefault universe marker."})
    assert uploaded.status_code == 200
    for scope in ({"doc_id": "care/nested/care"}, {"subfolder": "care"}):
        response = area_client.get("/api/search", params={"q": "Default", "retrieval_mode": "lexical", **scope})
        assert response.status_code == 200
        assert {r["chunk"]["doc_id"] for r in response.json()["results"]} == {"care/nested/care"}
        chat = area_client.post("/api/chats/scoped/turn", json={"query": "Default", "ask_tutor": False, **scope})
        if chat.status_code == 409:
            assert area_client.delete("/api/chats/scoped").status_code == 200
            chat = area_client.post("/api/chats/scoped/turn", json={"query": "Default", "ask_tutor": False, **scope})
        assert chat.status_code == 200 and {r["chunk"]["doc_id"] for r in chat.json()["turns"][0]["results"]} == {"care/nested/care"}
    report = area_client.post("/api/compliance/audit")
    assert report.status_code == 200 and report.headers["cache-control"] == "no-store"
    assert report.json()["area"] == "knowledge_base" and report.json()["files_scanned"] == 2
    assert report.json()["benchmark"]["provenance_coverage"] == 100
    assert report.json()["benchmark"]["hallucination_refusal_gate"] is True


def test_budget_meter_reset_and_hardware_advice(area_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    report = area_client.get("/api/budget")
    assert report.status_code == 200 and report.headers["cache-control"] == "no-store"
    assert report.json()["cloud_requests_today"] == 0 and report.json()["daily_cloud_request_limit"] == 50
    assert ui_app.budget.check_and_record_budget("openai") is None
    assert area_client.get("/api/budget").json()["cloud_requests_today"] == 1
    assert area_client.post("/api/budget/reset", json={"confirm": True}).json()["cloud_requests_today"] == 0
    monkeypatch.setattr(workspace, "probe_system_status", lambda _: {"ollama_models": []})
    status = area_client.get("/api/system-status").json()
    assert type(status["ram_gb"]) is int and status["ram_gb"] >= 0 and status["ram_tier_advice"]



def test_selected_areas_merge_guides_search_and_chat(area_client: TestClient, tmp_path: Path) -> None:
    second = tmp_path / "devops_engineering"
    second.mkdir()
    (second / "shared.md").write_text("# DevOps Guide\nTags: devops\n\n## Deployment\nDevOps universe marker.\n")
    response = area_client.post("/api/workspace", json={"active_dirs": ["knowledge_base", "devops_engineering"]})
    assert response.status_code == 200
    data = response.json()
    assert data["config"]["knowledge_dir"] == data["config"]["active_dirs"][0] == "knowledge_base"
    assert data["doc_count"] == 2 and {a["doc_count"] for a in data["areas"]} == {1}
    guides = area_client.get("/api/guides").json()
    assert {g["area"] for g in guides} == {"knowledge_base", "devops_engineering"}
    assert len({g["doc_id"] for g in guides}) == 2
    assert {g["subfolder"] for g in guides} == {"knowledge_base", "devops_engineering"}
    hits = area_client.get("/api/search", params={"q": "universe marker", "retrieval_mode": "lexical", "top_k": 10}).json()["results"]
    assert {r["chunk"]["area"] for r in hits} == {"knowledge_base", "devops_engineering"}
    turn = area_client.post("/api/chats/combined/turn", json={"query": "universe marker", "retrieval_mode": "lexical", "top_k": 10, "ask_tutor": False}).json()
    assert {r["chunk"]["area"] for r in turn["turns"][0]["results"]} == {"knowledge_base", "devops_engineering"}
    assert turn["active_dirs"] == ["knowledge_base", "devops_engineering"]
