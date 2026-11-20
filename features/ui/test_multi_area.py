"""Combined reads retain source identities and bounded single-area write destinations."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from features.ui import app as ui_app
from features.ui import workspace


def select_two(client: TestClient, root: Path) -> None:
    other = root / "devops"
    (other / "nested").mkdir(parents=True)
    (other / "shared.md").write_text("# Shared Guide\nTags: devops\n\n## Overview\nDevops universe marker contact test@example.invalid.")
    (other / "nested/guide.md").write_text("# Nested\n## Nested\nDevops universe marker.")
    assert client.post("/api/workspace", json={"active_dirs": ["knowledge_base", "devops"]}).status_code == 200


@pytest.mark.parametrize("dirs,status", [([], 422), ([123], 422), (None, 422), ("knowledge_base", 422), (["../outside"], 400), (["features"], 400), (["new_valid", "../escape"], 400)])
def test_invalid_selection_keeps_previous_config(area_client: TestClient, tmp_path: Path, dirs: object, status: int) -> None:
    response = area_client.post("/api/workspace", json={"active_dirs": dirs})
    assert response.status_code == status
    assert area_client.get("/api/workspace").json()["config"]["active_dirs"] == ["knowledge_base"]
    assert not (tmp_path / "new_valid").exists()


def test_selected_alias_and_index_alias_are_rejected(area_client: TestClient, tmp_path: Path) -> None:
    (tmp_path / "alias").symlink_to(tmp_path / "knowledge_base", target_is_directory=True)
    assert area_client.post("/api/workspace", json={"active_dirs": ["knowledge_base", "alias"]}).status_code == 400
    second = tmp_path / "second"
    second.mkdir()
    cache = tmp_path / "outside.json"
    cache.write_text("[]")
    (second / "index.json").symlink_to(cache)
    assert area_client.post("/api/workspace", json={"active_dirs": ["knowledge_base", "second"]}).status_code == 400
    assert cache.read_text() == "[]"


def test_combined_upload_preview_moves_and_local_caches(area_client: TestClient, tmp_path: Path) -> None:
    select_two(area_client, tmp_path)
    uploaded = area_client.post("/api/upload", files={"file": ("new.md", b"# New\n## Body\nSecondary marker.")}, data={"area": "devops", "subfolder": "new/path"})
    assert uploaded.status_code == 200 and uploaded.json()["doc_count"] == 4
    assert (tmp_path / "devops/new/path/new.md").exists() and not (tmp_path / "knowledge_base/new").exists()
    assert area_client.post("/api/upload", json={"filename": "bad.md", "content": "bad", "area": "outside"}).status_code == 400
    assert area_client.post("/api/upload", json={"filename": "primary.md", "content": "# Primary\n## Body\nPrimary marker"}).status_code == 200
    assert (tmp_path / "knowledge_base/primary.md").exists()
    report = area_client.post("/api/anonymize/preview", json={"doc_id": "devops::shared"})
    assert report.status_code == 200 and report.json()["counts_by_type"]["EMAIL"] == 1
    assert area_client.post("/api/guides/devops::shared/anonymize").status_code == 200
    moved = area_client.post("/api/guides/devops::shared/move", json={"subfolder": "devops/new/path"})
    assert moved.status_code == 200 and moved.json()["guide"]["doc_id"] == "devops::new/path/shared"
    assert area_client.post("/api/guides/devops::new/path/shared/move", json={"subfolder": "knowledge_base"}).status_code == 400
    assert area_client.delete("/api/guides/devops::new/path/shared").status_code == 200
    for name in ("knowledge_base", "devops"):
        cached = json.loads((tmp_path / name / "index.json").read_text())
        assert all("::" not in chunk["doc_id"] and chunk["area"] == "" for chunk in cached["chunks"])
    assert area_client.post("/api/workspace", json={"knowledge_dir": "devops"}).json()["config"]["active_dirs"] == ["devops"]
    assert all("::" not in guide["doc_id"] for guide in area_client.get("/api/guides").json())


def test_combined_subfolder_scope_and_selection_header(area_client: TestClient, tmp_path: Path) -> None:
    select_two(area_client, tmp_path)
    created = area_client.post("/api/subfolders", json={"name": "devops/nested/deeper"})
    assert created.status_code == 200 and (tmp_path / "devops/nested/deeper").is_dir()
    hits = area_client.get("/api/search", params={"q": "universe", "subfolder": "devops", "retrieval_mode": "lexical"}).json()["results"]
    assert hits and all(hit["chunk"]["area"] == "devops" for hit in hits)
    assert area_client.delete("/api/subfolders", params={"path": "knowledge_base"}).status_code == 403
    stale = {"x-knowledge-area": "knowledge_base", "x-knowledge-selection": "knowledge_base"}
    assert area_client.get("/api/search?q=marker", headers=stale).status_code == 409
    assert area_client.post("/api/upload", headers=stale, json={"filename": "bad.md", "content": "bad"}).status_code == 409
    assert area_client.delete("/api/guides/outside::shared").status_code == 404
    assert area_client.delete("/api/subfolders", params={"path": "devops/nested"}).status_code == 200
    assert (tmp_path / "devops/shared.md").exists()


def test_combined_graph_and_deletion_retain_remaining_selection(area_client: TestClient, tmp_path: Path) -> None:
    select_two(area_client, tmp_path)
    graph = area_client.get("/api/graph?all_areas=false").json()
    assert {node["area"] for node in graph["nodes"]} == {"knowledge_base", "devops"}
    assert area_client.delete("/api/workspace/devops").json()["config"]["active_dirs"] == ["knowledge_base"]
    assert not (tmp_path / "devops").exists()
    assert len(area_client.get("/api/guides").json()) == 1
    saved = workspace.load_workspace_config()
    assert saved.knowledge_dir == saved.active_dirs[0] == "knowledge_base"


@pytest.mark.parametrize("mode", ["hybrid", "vector"])
def test_combined_dense_retrieval_uses_both_areas(area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    select_two(area_client, tmp_path)
    monkeypatch.setattr(ui_app, "INDEX", [c.model_copy(update={"embedding": [1.0, 0.0]}) for c in ui_app.INDEX])
    monkeypatch.setattr(ui_app, "embed_text", lambda *_args, **_kwargs: [1.0, 0.0])
    response = area_client.get("/api/search", params={"q": "universe marker", "retrieval_mode": mode, "top_k": 10})
    assert response.status_code == 200
    assert {hit["chunk"]["area"] for hit in response.json()["results"]} == {"knowledge_base", "devops"}
    assert response.json()["active_dirs"] == ["knowledge_base", "devops"]


def test_cached_selection_rejects_replaced_area_alias(area_client: TestClient, tmp_path: Path) -> None:
    select_two(area_client, tmp_path)
    (tmp_path / "devops").rename(tmp_path / "retained")
    (tmp_path / "devops").symlink_to(tmp_path / "knowledge_base", target_is_directory=True)
    for route in ("/api/workspace", "/api/guides", "/api/search?q=marker"):
        assert area_client.get(route).status_code == 400
