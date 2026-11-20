"""Folder deletion stays within its active vault, including mixed files and aliases."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from features.ui import folder_routes


@pytest.mark.parametrize("path", [".", "..", "a/../b", "/tmp", ".private", "a//b", "a\\b", "shared.md", "missing", "a\x00b"])
def test_delete_rejects_invalid_folder_paths(area_client: TestClient, tmp_path: Path, path: str) -> None:
    assert area_client.delete("/api/subfolders", params={"path": path}).status_code == 400
    assert (tmp_path / "knowledge_base/shared.md").is_file()


def test_root_and_stale_area_are_protected(area_client: TestClient, tmp_path: Path) -> None:
    assert area_client.delete("/api/subfolders").status_code == 422
    assert area_client.delete("/api/subfolders", params={"path": ""}).status_code == 403
    assert area_client.post("/api/subfolders", json={"name": "empty"}).status_code == 200
    assert area_client.delete("/api/subfolders?path=empty", headers={"x-knowledge-area": "other"}).status_code == 409
    assert (tmp_path / "knowledge_base/empty").is_dir()
    result = area_client.delete("/api/subfolders?path=empty")
    assert result.status_code == 200 and result.json()["doc_count"] == 1
    assert not (tmp_path / "knowledge_base/empty").exists()


def test_deleting_alias_cannot_follow_it_outside_the_area(area_client: TestClient, tmp_path: Path) -> None:
    outside = tmp_path / "other"
    outside.mkdir()
    sentinel = outside / "preserve.txt"
    sentinel.write_text("Synthetic sentinel")
    base = tmp_path / "knowledge_base"
    (base / "alias").symlink_to(outside, target_is_directory=True)
    for path in ("alias", "alias/nested"):
        assert area_client.delete("/api/subfolders", params={"path": path}).status_code == 400
    assert area_client.post("/api/subfolders", json={"name": "safe/deep"}).status_code == 200
    (base / "safe/deep/link").symlink_to(outside, target_is_directory=True)
    (base / "safe/original.bin").write_bytes(b"synthetic original")
    assert area_client.delete("/api/subfolders?path=safe").status_code == 200
    assert not (base / "safe").exists() and sentinel.read_text() == "Synthetic sentinel"


def test_folder_creation_has_no_artificial_total_path_depth_limit(area_client: TestClient, tmp_path: Path) -> None:
    path = "/".join(f"level_{i:02d}" for i in range(35))
    assert len(path) > 255
    result = area_client.post("/api/subfolders", json={"name": path})
    assert result.status_code == 200 and result.json()["created"] == path
    assert (tmp_path / "knowledge_base" / path).is_dir()
    assert area_client.delete("/api/subfolders?path=level_00").status_code == 200


def test_failed_partial_delete_refreshes_the_index(area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert area_client.post("/api/upload", json={"filename": "guide.md", "subfolder": "partial", "content": "# Partial\nTags: base\n\n## Scope\nPartial marker."}).status_code == 200

    def interrupted(path: Path) -> None:
        (path / "guide.md").unlink()
        raise PermissionError("Synthetic interruption")

    monkeypatch.setattr(folder_routes.shutil, "rmtree", interrupted)
    response = area_client.delete("/api/subfolders?path=partial")
    assert response.status_code == 400 and "remaining files" in response.json()["detail"]
    assert {g["doc_id"] for g in area_client.get("/api/guides").json()} == {"shared"}
