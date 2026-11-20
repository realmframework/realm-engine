"""Combined histories, source citations and pending answers stay bound to their selection."""

import io
import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.contracts import SearchResult, TutorResponse, WorkspaceConfig
from features.ui import app as ui_app


def two_areas(client: TestClient, root: Path) -> None:
    other = root / "second"
    other.mkdir()
    (other / "shared.md").write_text("# Shared Guide\n## Overview\nSecond universe marker.")
    assert client.post("/api/workspace", json={"active_dirs": ["knowledge_base", "second"]}).status_code == 200


def test_config_migrates_legacy_deduplicates_and_syncs_primary() -> None:
    assert WorkspaceConfig(knowledge_dir="study").active_dirs == ["study"]
    config = WorkspaceConfig(knowledge_dir="ignored", active_dirs=["second", "knowledge_base", "second"])
    assert config.knowledge_dir == "second" and config.active_dirs == ["second", "knowledge_base"]


def test_chat_selection_isolation_and_combined_citations(area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    two_areas(area_client, tmp_path)
    def grounded(_query: str, results: list[SearchResult], *_args: object, **_kwargs: object) -> TutorResponse:
        return TutorResponse(answer="Synthetic answer", cited_titles=[r.chunk.title for r in results], knowledge_gap_detected=False, recommended_topics=[])
    monkeypatch.setattr(ui_app, "run_tutor", grounded)
    reply = area_client.post("/api/chats/both/turn", json={"query": "universe marker", "retrieval_mode": "lexical"})
    assert reply.status_code == 200
    titles = reply.json()["turns"][0]["tutor"]["cited_titles"]
    assert any(t.startswith("second / ") for t in titles) and any(t.startswith("knowledge_base / ") for t in titles)
    assert len(area_client.get("/api/chats").json()) == 1
    assert area_client.post("/api/workspace", json={"knowledge_dir": "knowledge_base"}).status_code == 200
    assert area_client.get("/api/chats").json() == []
    assert area_client.get("/api/chats/both").status_code == 404
    assert area_client.post("/api/chats/both/turn", json={"query": "marker"}).status_code == 404
    assert area_client.delete("/api/chats/both").status_code == 404
    area_client.post("/api/workspace", json={"active_dirs": ["knowledge_base", "second"]})
    assert len(area_client.get("/api/chats/both").json()["turns"]) == 1
    assert area_client.get("/api/search", params={"q": "marker", "provider": "openai"}).status_code == 403
    assert area_client.delete("/api/chats/both").json()["deleted"] is True


def test_pending_answer_rejects_deleted_secondary_area(area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    two_areas(area_client, tmp_path)
    def delete_during_answer(*_args: object, **_kwargs: object) -> TutorResponse:
        assert area_client.delete("/api/workspace/second").status_code == 200
        return TutorResponse(answer="Stale", cited_titles=[], knowledge_gap_detected=False, recommended_topics=[])
    monkeypatch.setattr(ui_app, "run_tutor", delete_during_answer)
    result = area_client.post("/api/chats/pending/turn", json={"query": "universe marker", "retrieval_mode": "lexical"})
    assert result.status_code == 409 and area_client.get("/api/chats").json() == []


def test_primary_backup_does_not_export_other_selected_documents(area_client: TestClient, tmp_path: Path) -> None:
    two_areas(area_client, tmp_path)
    area_client.post("/api/chats/combined/turn", json={"query": "universe marker", "ask_tutor": False, "retrieval_mode": "lexical"})
    response = area_client.get("/api/backup/export")
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert json.loads(archive.read("workspace.json"))["active_dirs"] == ["knowledge_base"]
        assert json.loads(archive.read("chats.json")) == []
        assert b"Second" not in archive.read("shared.md")


def test_concurrent_chat_id_cannot_combine_different_selections(area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    two_areas(area_client, tmp_path)
    def competing_selection(*_args: object, **_kwargs: object) -> TutorResponse:
        assert area_client.post("/api/workspace", json={"knowledge_dir": "knowledge_base"}).status_code == 200
        inner = area_client.post("/api/chats/collision/turn", json={"query": "Default", "ask_tutor": False, "retrieval_mode": "lexical"})
        assert inner.status_code == 200
        return TutorResponse(answer="Stale combined", cited_titles=[], knowledge_gap_detected=False, recommended_topics=[])
    monkeypatch.setattr(ui_app, "run_tutor", competing_selection)
    response = area_client.post("/api/chats/collision/turn", json={"query": "universe marker", "retrieval_mode": "lexical"})
    assert response.status_code == 409
    saved = area_client.get("/api/chats/collision").json()
    assert saved["active_dirs"] == ["knowledge_base"] and len(saved["turns"]) == 1
    assert saved["turns"][0]["query"] == "Default"


def test_pending_answer_rejects_replaced_secondary_alias(area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    two_areas(area_client, tmp_path)
    def replace_during_answer(*_args: object, **_kwargs: object) -> TutorResponse:
        (tmp_path / "second").rename(tmp_path / "retained")
        (tmp_path / "second").symlink_to(tmp_path / "knowledge_base", target_is_directory=True)
        return TutorResponse(answer="Stale", cited_titles=[], knowledge_gap_detected=False, recommended_topics=[])
    monkeypatch.setattr(ui_app, "run_tutor", replace_during_answer)
    response = area_client.post("/api/chats/replaced/turn", json={"query": "universe marker", "retrieval_mode": "lexical"})
    assert response.status_code == 409
