"""Physical subfolder organization remains isolated inside each top-level vault."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def test_nested_guides_keep_distinct_ids_and_one_area_index(area_client: TestClient) -> None:
    for folder in ("", "architecture", "knowledge_base_2/deep"):
        response = area_client.post("/api/upload", json={"filename": "same.md", "subfolder": folder, "content": f"# {folder or 'Root'}\nTags: architecture\n\n## Scope\nUnified search marker."})
        assert response.status_code == 200
    guides = area_client.get("/api/guides").json()
    ids = {g["doc_id"] for g in guides}
    assert {"same", "architecture/same", "knowledge_base_2/deep/same"} <= ids
    assert {g["subfolder"] for g in guides} >= {"", "architecture", "knowledge_base_2/deep"}
    workspace = area_client.get("/api/workspace").json()
    assert workspace["available_dirs"] == ["knowledge_base"] and workspace["doc_count"] == 4
    results = area_client.get("/api/search?q=Unified&retrieval_mode=lexical").json()["results"]
    assert len({r["chunk"]["id"] for r in results}) == 3
    nodes = area_client.get("/api/graph?all_areas=false").json()["nodes"]
    assert {n["doc_id"] for n in nodes if n["type"] == "doc"} == ids


def test_create_move_preview_anonymize_and_delete_nested_guide(area_client: TestClient, tmp_path: Path) -> None:
    assert area_client.post("/api/subfolders", json={"name": "architecture/backend"}).status_code == 200
    assert (tmp_path / "knowledge_base/architecture/backend").is_dir()
    response = area_client.post("/api/guides/shared/move", json={"subfolder": "architecture/backend"})
    assert response.status_code == 200 and response.json()["doc_id"] == "architecture/backend/shared"
    assert not (tmp_path / "knowledge_base/shared.md").exists()
    assert area_client.post("/api/anonymize/preview", json={"doc_id": "architecture/backend/shared"}).status_code == 200
    assert area_client.post("/api/guides/architecture%2Fbackend%2Fshared/anonymize").status_code == 200
    assert area_client.delete("/api/guides/architecture%2Fbackend%2Fshared").status_code == 200
    assert area_client.get("/api/guides").json() == []
    folders = area_client.get("/api/subfolders").json()["subfolders"]
    assert {f["path"] for f in folders} == {"", "architecture", "architecture/backend"}


@pytest.mark.parametrize("path", ["../test", "/tmp/escape", "a/../../test", "a\\b", ".private", "a//b", 42])
def test_subfolder_paths_cannot_escape_the_area(area_client: TestClient, path: object) -> None:
    assert area_client.post("/api/subfolders", json={"name": path}).status_code == 400
    assert area_client.post("/api/upload", json={"filename": "safe.md", "content": "# Safe\n## Body\nContent", "subfolder": path}).status_code == 400


def test_move_preserves_both_files_on_conflict_and_rejects_stale_area(area_client: TestClient, tmp_path: Path) -> None:
    assert area_client.post("/api/upload", json={"filename": "shared.md", "subfolder": "target", "content": "# Other\n## Body\nOther guide."}).status_code == 200
    source = tmp_path / "knowledge_base/shared.md"
    original = source.read_bytes()
    assert area_client.post("/api/guides/shared/move", json={"subfolder": "target"}).status_code == 409
    assert source.read_bytes() == original
    assert area_client.post("/api/subfolders", json={"name": "wrong"}, headers={"x-knowledge-area": "other"}).status_code == 409
    assert area_client.post("/api/guides/shared/move", json={"subfolder": "target"}, headers={"x-knowledge-area": "other"}).status_code == 409


def test_symlink_subfolders_are_neither_listed_nor_writable(area_client: TestClient, tmp_path: Path) -> None:
    outside = tmp_path / "other"
    outside.mkdir()
    (tmp_path / "knowledge_base/alias").symlink_to(outside, target_is_directory=True)
    assert "alias" not in {f["path"] for f in area_client.get("/api/subfolders").json()["subfolders"]}
    assert area_client.post("/api/subfolders", json={"name": "alias/nested"}).status_code == 400
    assert area_client.post("/api/upload", json={"filename": "guide.md", "content": "# Safe\n## Body\nContent", "subfolder": "alias"}).status_code == 400
    assert list(outside.iterdir()) == []


def test_move_guide_to_new_nested_subfolder_and_back(area_client: TestClient, tmp_path: Path) -> None:
    original = tmp_path / "knowledge_base/shared.md"
    content = original.read_bytes()
    moved = area_client.post("/api/guides/shared/move", json={"subfolder": "architecture/backend"})
    assert moved.status_code == 200 and moved.json()["doc_id"] == "architecture/backend/shared"
    guide = moved.json()["guide"]
    assert guide["subfolder"] == "architecture/backend" and guide["title"] == "Shared Guide"
    nested = tmp_path / "knowledge_base/architecture/backend/shared.md"
    assert nested.read_bytes() == content and not original.exists()
    assert len(area_client.get("/api/guides").json()) == 1
    returned = area_client.post("/api/guides/architecture%2Fbackend%2Fshared/move", json={"subfolder": ""})
    assert returned.status_code == 200 and returned.json()["guide"]["subfolder"] == ""
    assert returned.json()["guide"]["doc_id"] == "shared"
    assert original.read_bytes() == content and not nested.exists()
    assert area_client.get("/api/search?q=universe&retrieval_mode=lexical").json()["results"][0]["chunk"]["doc_id"] == "shared"


def test_recursive_folder_creation_prefix_search_and_deletion(area_client: TestClient, tmp_path: Path) -> None:
    for folder in ("a", "a/b", "a/b/c"):
        assert area_client.post("/api/subfolders", json={"name": folder}).status_code == 200
    assert (tmp_path / "knowledge_base/a/b/c").is_dir()
    for folder in ("a/b/c", "aa"):
        upload = area_client.post("/api/upload", json={"filename": "guide.md", "subfolder": folder, "content": "# Nested\nTags: base\n\n## Scope\nDefault recursive marker."})
        assert upload.status_code == 200
    folders = area_client.get("/api/subfolders").json()["subfolders"]
    assert {"a", "a/b", "a/b/c"} <= {f["path"] for f in folders}
    search = area_client.get("/api/search", params={"q": "Default", "subfolder": "a", "retrieval_mode": "lexical"})
    assert search.status_code == 200 and {r["chunk"]["doc_id"] for r in search.json()["results"]} == {"a/b/c/guide"}
    chat = area_client.post("/api/chats/recursive/turn", json={"query": "Default", "subfolder": "a", "ask_tutor": False})
    assert chat.status_code == 200 and {r["chunk"]["doc_id"] for r in chat.json()["turns"][0]["results"]} == {"a/b/c/guide"}
    deleted = area_client.delete("/api/subfolders", params={"path": "a/b"})
    assert deleted.status_code == 200 and deleted.json()["deleted"] == "a/b"
    assert not (tmp_path / "knowledge_base/a/b").exists() and (tmp_path / "knowledge_base/a").is_dir()
    assert (tmp_path / "knowledge_base/aa/guide.md").is_file() and (tmp_path / "knowledge_base/shared.md").is_file()
    assert area_client.get("/api/search", params={"q": "Default", "subfolder": "a"}).json()["results"] == []
