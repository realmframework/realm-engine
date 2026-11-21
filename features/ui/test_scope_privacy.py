"""Scope/history boundaries, enforced cloud admission and synthetic audit mutations."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.contracts import SearchResult, TutorResponse
from features.ui import app as ui_app
from features.ui.compliance_eval import benchmark


def test_scope_is_persisted_and_cannot_broaden_history(area_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []

    def tutor(*args: object, **kwargs: object) -> TutorResponse:
        calls.append(kwargs.get("history"))
        return TutorResponse(answer="Scoped answer", cited_titles=[], knowledge_gap_detected=False, recommended_topics=[])

    monkeypatch.setattr(ui_app, "run_tutor", tutor)
    first = area_client.post("/api/chats/locked/turn", json={"query": "Default", "doc_id": "shared"})
    assert first.status_code == 200 and first.json()["doc_id"] == "shared"
    assert calls == [[]]
    assert area_client.get("/api/chats/locked").json()["doc_id"] == "shared"
    second = area_client.post("/api/chats/locked/turn", json={"query": "Default"})
    assert second.status_code == 200 and second.json()["doc_id"] == "shared"
    for change in ({"doc_id": None}, {"subfolder": "other"}, {"doc_id": "elsewhere"}):
        assert area_client.post("/api/chats/locked/turn", json={"query": "marker", **change}).status_code == 409
    assert len(area_client.get("/api/chats/locked").json()["turns"]) == 2
    area_client.post("/api/guides/shared/move", json={"subfolder": "moved"})
    stale = area_client.post("/api/chats/locked/turn", json={"query": "Default"}).json()
    assert stale["turns"][-1]["results"] == [] and stale["turns"][-1]["tutor"]["knowledge_gap_detected"]
    assert len(calls) == 2


def test_navigation_is_browsable_but_topic_guides_supply_answer_evidence(
    area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = tmp_path / "knowledge_base" / "rag"
    folder.mkdir()
    (folder / "reading.md").write_text("# Retrieval Reading Guide\nTags: navigation\n\n## Overview\nA map of retrieval topics.\n", encoding="utf-8")
    (folder / "recall.md").write_text("# Candidate Recall\nTags: rag\n\n## Overview\nMeasure retrieval before reranking.\n", encoding="utf-8")
    calls: list[list[str]] = []

    def tutor(_query: str, results: list[SearchResult], *args: object, **kwargs: object) -> TutorResponse:
        calls.append([result.chunk.doc_id for result in results])
        return TutorResponse(answer="Topic answer", cited_titles=[], knowledge_gap_detected=False, recommended_topics=[])

    monkeypatch.setattr(ui_app, "run_tutor", tutor)
    guides = area_client.get("/api/guides").json()
    assert any(guide["doc_id"] == "rag/reading" for guide in guides)
    search = {"q": "retrieval", "subfolder": "rag", "top_k": 1, "retrieval_mode": "lexical"}
    lookup = area_client.get("/api/search", params=search)
    assert lookup.status_code == 200
    assert lookup.json()["results"][0]["chunk"]["doc_id"] == "rag/reading"
    answer = area_client.get("/api/search", params={**search, "ask_tutor": True})
    assert answer.status_code == 200
    assert answer.json()["tutor"]["answer"] == "Topic answer"

    chat = {"query": "retrieval", "subfolder": "rag", "retrieval_mode": "lexical"}
    assert area_client.post("/api/chats/topic/turn", json=chat).status_code == 200
    scoped = area_client.post("/api/chats/navigation/turn", json={**chat, "doc_id": "rag/reading"})
    assert scoped.status_code == 200
    turn = scoped.json()["turns"][0]
    assert turn["results"] == [] and turn["tutor"]["knowledge_gap_detected"]
    assert calls == [["rag/recall"], ["rag/recall"]]


@pytest.mark.parametrize("provider", ["openai", "gemini", "kimi", "deepseek", "anthropic", "xai", "mistral"])
def test_local_lock_rejects_before_external_calls(area_client: TestClient, monkeypatch: pytest.MonkeyPatch, provider: str) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        pytest.fail("Cloud/model callback must not be invoked")

    monkeypatch.setattr(ui_app, "run_tutor", forbidden)
    monkeypatch.setattr(ui_app, "list_provider_models", forbidden)
    assert area_client.get("/api/workspace").json()["config"]["strict_local_only"] is True
    for route in ("/api/models", "/api/search"):
        assert area_client.get(route, params={"provider": provider, "q": "Default", "api_key": "synthetic-key", "ask_tutor": True}).status_code == 403
    assert area_client.post("/api/chats/cloud/turn", json={"query": "Default", "provider": provider, "api_key": "synthetic-key"}).status_code == 403
    assert area_client.get("/api/chats").json() == []


def test_local_lock_covers_cloud_tagged_models_and_audio(area_client: TestClient) -> None:
    assert area_client.post("/api/chats/cloud/turn", json={"query": "Default", "model": "gpt-oss:120b-cloud"}).status_code == 403
    for model in ("openai:tts-1", "elevenlabs:tts", "phonon:cloud"):
        assert area_client.post("/api/audio/speak", json={"text": "Synthetic", "model": model, "api_key": "synthetic-key"}).status_code == 403
    assert area_client.post("/api/workspace", json={"strict_local_only": False}).json()["config"]["strict_local_only"] is False
    assert area_client.post("/api/workspace", json={"strict_local_only": True}).json()["config"]["strict_local_only"] is True


def test_explicit_cloud_opt_in_is_supported(area_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ui_app, "run_tutor", lambda *_a, **_kw: TutorResponse(answer="Mock cloud answer", cited_titles=[], knowledge_gap_detected=False, recommended_topics=[]))
    assert area_client.post("/api/workspace", json={"strict_local_only": False}).status_code == 200
    response = area_client.post("/api/chats/opt-in/turn", json={"query": "Default", "provider": "openai"})
    assert response.status_code == 200 and response.json()["turns"][0]["tutor"]["answer"] == "Mock cloud answer"


def test_audit_is_read_only_and_scrub_is_area_local(area_client: TestClient, tmp_path: Path) -> None:
    raw = "# Care\nTags: care\n\n## Treatment\n14.03.1938 A123456789 90402 Nürnberg Hauptstraße 12 care@example.invalid [REDACTED_NAME]."
    patient = tmp_path / "knowledge_base/patient.md"
    patient.write_text(raw, encoding="utf-8")
    outside = tmp_path / "other"
    outside.mkdir()
    (outside / "patient.md").write_text(raw, encoding="utf-8")
    (tmp_path / "knowledge_base/alias.md").symlink_to(outside / "patient.md")
    area_client.post("/api/workspace", json={"knowledge_dir": "knowledge_base"})
    report = area_client.post("/api/compliance/audit").json()
    assert report["clean_vault"] is False and report["unredacted_warnings"] == 5
    assert report["counts_by_type"]["NAME"] == 1 and report["audit_external_bytes_sent"] == 0
    assert report["benchmark"]["generation_evaluated"] is False
    assert patient.read_text(encoding="utf-8") == raw
    assert area_client.post("/api/compliance/scrub", json={"confirm": False}).status_code == 400
    assert area_client.post("/api/compliance/scrub", content='confirm=true', headers={"content-type": "application/x-www-form-urlencoded"}).status_code == 422
    scrubbed = area_client.post("/api/compliance/scrub", json={"confirm": True}).json()
    assert scrubbed["clean_vault"] and scrubbed["redacted_now"] == 5
    assert scrubbed["counts_by_type"]["DOB"] == 1 and scrubbed["counts_by_type"]["ADDRESS"] == 1
    assert "14.03.1938" not in patient.read_text(encoding="utf-8") and "[REDACTED_HEALTH_ID]" in patient.read_text(encoding="utf-8")
    assert (outside / "patient.md").read_text(encoding="utf-8") == raw
    assert "[REDACTED_DOB]" in next(g for g in area_client.get("/api/guides").json() if g["doc_id"] == "patient")["sections"][0]["content"]
    assert area_client.post("/api/compliance/audit").json()["unredacted_warnings"] == 0
    stale = {"x-knowledge-area": "other"}
    for route in ("/api/compliance/audit", "/api/compliance/scrub"):
        assert area_client.post(route, headers=stale, json={"confirm": True}).status_code == 409


def test_audit_does_not_pass_empty_or_unreadable_vault(area_client: TestClient, tmp_path: Path) -> None:
    area_client.post("/api/workspace", json={"knowledge_dir": "empty"})
    report = area_client.post("/api/compliance/audit").json()
    assert report["benchmark"]["status"] == "NO DATA" and report["benchmark"]["provenance_coverage"] == 0
    (tmp_path / "empty/bad.MD").write_bytes(b"\xff")
    report = area_client.post("/api/compliance/audit").json()
    assert report["scan_errors"] == 1 and report["clean_vault"] is False


def test_provenance_and_ood_failures_are_visible(area_client: TestClient, tmp_path: Path) -> None:
    area_client.get("/api/guides")
    chunks = [c.model_copy(update={"doc_id": ""}) for c in ui_app.INDEX]
    report = benchmark(chunks, tmp_path / "knowledge_base", ui_app.hybrid_search)
    assert report["status"] == "WARN" and report["provenance_coverage"] == 0
    chunks = [c.model_copy(update={"content": "quantum_bananas_xyz_999"}) for c in ui_app.INDEX]
    assert benchmark(chunks, tmp_path / "knowledge_base", ui_app.hybrid_search)["hallucination_refusal_gate"] is False
