"""Archive boundaries reject the whole restore before any guide is written."""

import io
import json
import stat
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from features.ui import backup_archive, chat_store, workspace


def archive_bytes(entries: dict[str, str | bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in entries.items():
            archive.writestr(name.replace("\x00", "_"), value)
    return buffer.getvalue().replace(b"nul_.md", b"nul\x00.md")


@pytest.mark.parametrize("name", ["../escape.md", "a/../../escape.md", "/absolute.md", "C:/drive.md", "a\\escape.md", "a/./b.md", "a//b.md", "../../ignored.txt", "../outside/", "nul\x00.md"])
def test_unsafe_member_rejects_even_ignored_files_and_directories(area_client: TestClient, tmp_path: Path, name: str) -> None:
    response = area_client.post("/api/backup/import", files={"file": ("backup.zip", archive_bytes({"safe.md": "# Safe\n## Body\nKeep", name: "bad"}), "application/zip")})
    assert response.status_code == 400 and not (tmp_path / "knowledge_base/safe.md").exists()


def test_archive_symlinks_and_duplicate_case_names_rejected(area_client: TestClient) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        info = zipfile.ZipInfo("alias.md")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(info, "../other.md")
    assert area_client.post("/api/backup/import", files={"file": ("backup.zip", buffer.getvalue())}).status_code == 400
    assert area_client.post("/api/backup/import", files={"file": ("backup.zip", archive_bytes({"A.md": "one", "a.md": "two"}))}).status_code == 400


def test_existing_content_and_outside_alias_are_preserved(area_client: TestClient, tmp_path: Path) -> None:
    original = (tmp_path / "knowledge_base/shared.md").read_bytes()
    raw = archive_bytes({"new.md": "# New", "shared.md": "# Different"})
    assert area_client.post("/api/backup/import", files={"file": ("backup.zip", raw)}).status_code == 409
    assert not (tmp_path / "knowledge_base/new.md").exists()
    assert (tmp_path / "knowledge_base/shared.md").read_bytes() == original
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "knowledge_base/alias").symlink_to(outside, target_is_directory=True)
    raw = archive_bytes({"alias/escape.md": "# Escape"})
    assert area_client.post("/api/backup/import", files={"file": ("backup.zip", raw)}).status_code == 400
    assert list(outside.iterdir()) == []


def test_expanded_archive_and_transport_are_bounded(area_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(backup_archive, "MAX_FILE_BYTES", 100)
    response = area_client.post("/api/backup/import", files={"file": ("backup.zip", archive_bytes({"large.md": "x" * 101}))})
    assert response.status_code == 413
    assert area_client.post("/api/backup/import", content=b"tiny", headers={"content-length": str(500 * 1024 * 1024)}).status_code == 413
    assert area_client.post("/api/backup/import", files={"file": ("broken.zip", b"invalid")}).status_code == 400


def test_export_restore_chats_settings_and_empty_folders(area_client: TestClient, tmp_path: Path) -> None:
    assert area_client.post("/api/workspace/create", json={"name": "medical", "template": "care"}).status_code == 200
    area_client.post("/api/upload", json={"filename": "care.md", "subfolder": "daily_notes", "content": "# Care\n## Notes\nSynthetic care marker."})
    area_client.post("/api/chats/saved/turn", json={"query": "care", "ask_tutor": False, "subfolder": "daily_notes"})
    response = area_client.get("/api/backup/export")
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert {"care_plans/", "protocols/", "daily_notes/care.md"} <= set(archive.namelist())
        assert json.loads(archive.read("workspace.json"))["strict_local_only"] is True
        assert len(json.loads(archive.read("chats.json"))) == 1
    area_client.post("/api/workspace/create", json={"name": "recovered", "template": "blank"})
    result = area_client.post("/api/backup/import", files={"file": ("restore.zip", response.content)})
    assert result.status_code == 200 and result.json()["restored_files"] == 1
    assert result.json()["config"]["knowledge_dir"] == "recovered"
    assert (tmp_path / "recovered/protocols").is_dir()
    chat = area_client.get("/api/chats/saved").json()
    assert chat["area"] == "recovered" and chat["subfolder"] == "daily_notes"
    assert chat["turns"][0]["results"][0]["chunk"]["file_path"].startswith(str(tmp_path / "recovered"))
    assert area_client.post("/api/backup/import", files={"file": ("repeat.zip", response.content)}).status_code == 200
    assert len(chat_store.load_chats(chat_store.area_chat_path("recovered"))) == 1
    assert workspace.load_workspace_config().knowledge_dir == "recovered"


def test_member_limit_is_checked_before_zipfile_allocation(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi import HTTPException

    raw = archive_bytes({"a.md": "a", "b.md": "b", "c.md": "c"})
    monkeypatch.setattr(backup_archive, "MAX_MEMBERS", 2)
    monkeypatch.setattr(backup_archive.zipfile, "ZipFile", lambda *_a: pytest.fail("Archive should be rejected before parsing all entries"))
    with pytest.raises(HTTPException) as error:
        backup_archive.read_archive(raw)
    assert error.value.status_code == 413


def test_bad_crc_cannot_partially_write_guides(area_client: TestClient, tmp_path: Path) -> None:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("first.md", "# First")
        archive.writestr("bad.md", "unique corruption marker")
    raw = output.getvalue().replace(b"unique corruption marker", b"broken corruption marker")
    assert area_client.post("/api/backup/import", files={"file": ("backup.zip", raw)}).status_code == 400
    assert not (tmp_path / "knowledge_base/first.md").exists()


def test_workspace_backup_export_contains_nested_guides(area_client: TestClient) -> None:
    area_client.post("/api/upload", json={"filename": "nested.md", "subfolder": "a/b", "content": "# Nested\n## Body\nArchive marker."})
    response = area_client.get("/api/backup/export")
    assert response.status_code == 200 and response.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert {"shared.md", "a/b/nested.md", "workspace.json", "chats.json"} <= set(archive.namelist())
        assert b"Archive marker" in archive.read("a/b/nested.md")


@pytest.mark.parametrize("name,status", [("nested/restored.md", 200), ("../escape.md", 400)])
def test_workspace_backup_import_and_zip_slip_rejection(area_client: TestClient, tmp_path: Path, name: str, status: int) -> None:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(name, "# Restored\n## Body\nArchive marker.")
    response = area_client.post("/api/backup/import", files={"file": ("backup.zip", output.getvalue(), "application/zip")})
    assert response.status_code == status
    if status == 200:
        assert response.json()["restored_files"] == 1
        assert (tmp_path / "knowledge_base/nested/restored.md").exists()
        assert area_client.get("/api/search?q=Archive&retrieval_mode=lexical").json()["results"]
    else:
        assert not (tmp_path / "escape.md").exists()
