"""Knowledge-area isolation, stale requests, path safety and deletion boundaries."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest
from fastapi.testclient import TestClient

from core.contracts import TutorResponse
from features.ui import app as ui_app


def test_switching_areas_isolates_guides_search_topics_and_chats(area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    histories: list[object] = []

    def tutor(*args: object, **kwargs: object) -> TutorResponse:
        histories.append(kwargs.get("history"))
        return TutorResponse(answer="Synthetic answer", cited_titles=[], knowledge_gap_detected=False, recommended_topics=[])

    monkeypatch.setattr(ui_app, "run_tutor", tutor)
    first = area_client.post("/api/chats/same-id/turn", json={"query": "Default marker", "ask_tutor": True})
    assert first.status_code == 200 and first.json()["area"] == "knowledge_base"
    empty = area_client.post("/api/workspace", json={"knowledge_dir": "kitchen_recipes"}).json()
    assert empty["doc_count"] == 0 and empty["tags"] == []
    assert {a["name"] for a in empty["areas"]} == {"knowledge_base", "kitchen_recipes"}
    assert area_client.get("/api/chats").json() == []
    assert area_client.get("/api/chats/same-id").status_code == 404
    assert area_client.delete("/api/chats/same-id").json()["deleted"] is False
    assert area_client.post("/api/upload", json={"filename": "recipe.md", "content": "# Recipe\nTags: kitchen\n\n## Ingredients\nKitchen-only saffron marker."}).status_code == 200
    assert area_client.get("/api/search?q=Default&retrieval_mode=lexical").json()["results"] == []
    assert area_client.get("/api/guides").json()[0]["title"] == "Recipe"
    second = area_client.post("/api/chats/same-id/turn", json={"query": "Saffron", "ask_tutor": True})
    assert second.status_code == 200 and len(second.json()["turns"]) == 1 and histories == [[], []]
    assert (tmp_path / "chats.json").is_file() and (tmp_path / "kitchen_recipes/chats.json").is_file()
    assert area_client.post("/api/workspace", json={"knowledge_dir": "knowledge_base"}).status_code == 200
    assert area_client.get("/api/chats/same-id").json()["turns"][0]["query"] == "Default marker"
    assert area_client.get("/api/guides?tag=kitchen").json() == []
    assert area_client.get("/api/workspace").json()["tags"] == [{"name": "base", "count": 1}]


def test_stale_area_headers_deny_reads_and_mutations(area_client: TestClient) -> None:
    assert area_client.post("/api/workspace", json={"knowledge_dir": "bank_debts"}).status_code == 200
    headers = {"x-knowledge-area": "knowledge_base"}
    for route in ("/api/chats", "/api/chats/old", "/api/guides", "/api/search?q=marker", "/api/graph", "/api/workspace"):
        assert area_client.get(route, headers=headers).status_code == 409
    assert area_client.post("/api/upload", json={"filename": "wrong.txt", "content": "Never store"}, headers=headers).status_code == 409
    assert area_client.post("/api/chats/old/turn", json={"query": "Never append", "ask_tutor": False}, headers=headers).status_code == 409
    assert area_client.delete("/api/guides/shared", headers=headers).status_code == 409
    assert area_client.delete("/api/chats/old", headers=headers).status_code == 409
    assert area_client.post("/api/anonymize/preview", json={"doc_id": "shared"}, headers=headers).status_code == 409


def test_in_flight_answer_stays_in_its_original_area(area_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    entered, release = Event(), Event()

    def tutor(*args: object, **kwargs: object) -> TutorResponse:
        entered.set()
        assert release.wait(5)
        return TutorResponse(answer="Default-area answer", cited_titles=[], knowledge_gap_detected=False, recommended_topics=[])

    monkeypatch.setattr(ui_app, "run_tutor", tutor)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(area_client.post, "/api/chats/pending/turn", json={"query": "Default marker", "ask_tutor": True})
        try:
            assert entered.wait(5)
            assert area_client.post("/api/workspace", json={"knowledge_dir": "kids_homework"}).status_code == 200
        finally:
            release.set()
        assert pending.result(timeout=5).json()["area"] == "knowledge_base"
    assert area_client.get("/api/chats").json() == []
    assert area_client.post("/api/workspace", json={"knowledge_dir": "knowledge_base"}).status_code == 200
    assert area_client.get("/api/chats/pending").json()["turns"][0]["tutor"]["answer"] == "Default-area answer"


def test_area_deletion_protects_source_unmanaged_and_aliases(area_client: TestClient, tmp_path: Path) -> None:
    (tmp_path / "core").mkdir()
    sentinel = tmp_path / "core/source.py"
    sentinel.write_text("preserved", encoding="utf-8")
    (tmp_path / "unmanaged").mkdir()
    (tmp_path / "unmanaged/note.md").write_text("# Unmanaged\n", encoding="utf-8")
    (tmp_path / "alias").symlink_to(tmp_path / "knowledge_base", target_is_directory=True)
    for name in ("core", "alias", "../outside", ".git", "knowledge_base/nested"):
        assert area_client.post("/api/workspace", json={"knowledge_dir": name}).status_code == 400
    for blocked in ("core", "alias", "unmanaged"):
        assert area_client.delete(f"/api/workspace/{blocked}").status_code == 400
    assert sentinel.read_text() == "preserved" and (tmp_path / "unmanaged/note.md").is_file()
    assert area_client.post("/api/workspace", json={"knowledge_dir": "custom_area"}).status_code == 200
    assert area_client.post("/api/chats/local/turn", json={"query": "Hello", "ask_tutor": False}).status_code == 200
    response = area_client.delete("/api/workspace/custom_area")
    assert response.status_code == 200 and response.json()["config"]["knowledge_dir"] == "knowledge_base"
    assert not (tmp_path / "custom_area").exists() and (tmp_path / "knowledge_base/shared.md").is_file()
    assert "custom_area" not in response.json()["available_dirs"]


def test_deleting_knowledge_base_and_zero_workspace_free_chat(area_client: TestClient, tmp_path: Path) -> None:
    assert area_client.post("/api/chats/default/turn", json={"query": "Hi", "ask_tutor": False}).status_code == 200
    assert area_client.post("/api/workspace", json={"knowledge_dir": "my_notes"}).status_code == 200
    assert area_client.post("/api/workspace", json={"knowledge_dir": "knowledge_base"}).status_code == 200
    deleted_kb = area_client.delete("/api/workspace/knowledge_base")
    assert deleted_kb.status_code == 200 and deleted_kb.json()["config"]["knowledge_dir"] == "my_notes"
    assert not (tmp_path / "knowledge_base").exists() and not (tmp_path / "chats.json").exists()
    assert "knowledge_base" not in deleted_kb.json()["available_dirs"]
    empty = area_client.delete("/api/workspace/my_notes")
    assert empty.status_code == 200 and empty.json()["config"]["knowledge_dir"] == "" and empty.json()["config"]["active_dirs"] == []
    assert empty.json()["areas"] == [] and empty.json()["doc_count"] == 0
    assert area_client.get("/api/guides").json() == [] and area_client.get("/api/graph").json()["nodes"] == []
    assert area_client.get("/api/chats").status_code == 200
    assert area_client.get("/api/backup/export").status_code == 400 and area_client.post("/api/compliance/audit").status_code == 400
    reset = area_client.post("/api/workspace/reset-defaults")
    assert reset.status_code == 200 and reset.json()["config"]["knowledge_dir"] == "" and not (tmp_path / "knowledge_base").exists()


def test_guide_alias_cannot_read_or_mutate_another_area(area_client: TestClient, tmp_path: Path) -> None:
    original = (tmp_path / "knowledge_base/shared.md").read_bytes()
    assert area_client.post("/api/workspace", json={"knowledge_dir": "custom_area"}).status_code == 200
    (tmp_path / "custom_area/shared.md").symlink_to(tmp_path / "knowledge_base/shared.md")
    assert area_client.get("/api/guides").json() == []
    assert area_client.delete("/api/guides/shared").status_code == 404
    assert area_client.post("/api/anonymize/preview", json={"doc_id": "shared"}).status_code == 404
    assert area_client.post("/api/upload", json={"filename": "shared.md", "content": "Never overwrite"}).status_code == 400
    assert (tmp_path / "knowledge_base/shared.md").read_bytes() == original


def test_deleted_and_recreated_area_does_not_restore_a_pending_chat(area_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    entered, release = Event(), Event()

    def tutor(*args: object, **kwargs: object) -> TutorResponse:
        entered.set()
        assert release.wait(5)
        return TutorResponse(answer="Old vault content", cited_titles=[], knowledge_gap_detected=False, recommended_topics=[])

    monkeypatch.setattr(ui_app, "run_tutor", tutor)
    assert area_client.post("/api/workspace", json={"knowledge_dir": "temporary_area"}).status_code == 200
    assert area_client.post("/api/upload", json={"filename": "old.md", "content": "# Old question\nTags: base\n\n## Overview\nOld question marker."}).status_code == 200
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(area_client.post, "/api/chats/pending/turn", json={"query": "Old question", "ask_tutor": True})
        try:
            assert entered.wait(5)
            assert area_client.delete("/api/workspace/temporary_area").status_code == 200
            assert area_client.post("/api/workspace", json={"knowledge_dir": "temporary_area"}).status_code == 200
        finally:
            release.set()
        assert pending.result(timeout=5).status_code == 409
    assert area_client.get("/api/chats").json() == []
