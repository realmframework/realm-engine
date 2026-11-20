"""Backup metadata cannot weaken policy; failed restores preserve original state."""

import io
import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from features.ui import app as ui_app
from features.ui import backup_apply, chat_store, workspace


def make_zip(entries: dict[str, object]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, value in entries.items():
            archive.writestr(name, value if isinstance(value, str) else json.dumps(value))
    return output.getvalue()


def test_restore_keeps_local_policy_budget_and_active_area(area_client: TestClient) -> None:
    area_client.post("/api/workspace", json={"daily_cloud_request_limit": 2, "daily_budget_usd_limit": 0.1})
    payload: dict[str, object] = {"workspace.json": {"knowledge_dir": "foreign", "strict_local_only": False, "anonymize_uploads": False, "run_mode": "cloud", "daily_cloud_request_limit": 9999, "daily_budget_usd_limit": 9999, "app_title": "Recovered title", "api_key": "must-not-persist"}}
    raw = make_zip(payload)
    result = area_client.post("/api/backup/import", files={"file": ("backup.zip", raw)})
    assert result.status_code == 200
    cfg = result.json()["config"]
    assert cfg["knowledge_dir"] == "knowledge_base" and cfg["strict_local_only"] is True and cfg["run_mode"] == "local"
    assert cfg["daily_cloud_request_limit"] == 2 and cfg["daily_budget_usd_limit"] == 0.1
    assert cfg["anonymize_uploads"] is True
    assert cfg["app_title"] == "Recovered title" and "api_key" not in cfg
    assert "must-not-persist" not in workspace.WORKSPACE_FILE.read_text()


@pytest.mark.parametrize("metadata", [{"chats.json": {}}, {"workspace.json": {"daily_cloud_request_limit": -1}}, {"chats.json": [{"chat_id": "incomplete"}]}])
def test_invalid_metadata_cannot_partially_restore_guides(area_client: TestClient, tmp_path: Path, metadata: dict[str, object]) -> None:
    raw = make_zip({"new.md": "# New\n## Body\nNew text.", **metadata})
    assert area_client.post("/api/backup/import", files={"file": ("backup.zip", raw)}).status_code == 400
    assert not (tmp_path / "knowledge_base/new.md").exists()


def test_reindex_failure_rolls_back_files_chats_and_config(area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    area_client.post("/api/workspace", json={"app_title": "Preserved"})
    area_client.post("/api/chats/saved/turn", json={"query": "Default", "ask_tutor": False})
    before = {path: path.read_bytes() for path in [workspace.WORKSPACE_FILE, chat_store.CHATS_FILE, tmp_path / "knowledge_base/index.json"]}
    raw = make_zip({"deep/new.md": "# New\n## Body\nNew text."})
    activate = ui_app.activate_workspace

    def fail_once(config: object) -> dict[str, object]:
        monkeypatch.setattr(ui_app, "ingest_directory", ingest)
        raise OSError("Synthetic disk failure")

    ingest = ui_app.ingest_directory
    monkeypatch.setattr(ui_app, "ingest_directory", fail_once)
    result = area_client.post("/api/backup/import", files={"file": ("backup.zip", raw)})
    assert result.status_code == 400
    assert not (tmp_path / "knowledge_base/deep").exists()
    assert all(path.read_bytes() == contents for path, contents in before.items())
    assert ui_app.WORKSPACE_CONFIG.app_title == "Preserved" and activate is ui_app.activate_workspace


def test_corrupt_existing_chats_and_storage_aliases_are_not_overwritten(area_client: TestClient, tmp_path: Path) -> None:
    chat_store.CHATS_FILE.write_text("invalid")
    assert area_client.get("/api/backup/export").status_code == 400
    raw = make_zip({"new.md": "# New"})
    assert area_client.post("/api/backup/import", files={"file": ("backup.zip", raw)}).status_code == 400
    assert chat_store.CHATS_FILE.read_text() == "invalid" and not (tmp_path / "knowledge_base/new.md").exists()
    chat_store.CHATS_FILE.unlink()
    target = tmp_path / "private.json"
    target.write_text("[]")
    chat_store.CHATS_FILE.symlink_to(target)
    assert area_client.post("/api/backup/import", files={"file": ("backup.zip", raw)}).status_code == 400
    assert target.read_text() == "[]"


def test_stale_area_headers_and_failed_file_creation(area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw = make_zip({"new.md": "# New"})
    stale = {"x-knowledge-area": "another"}
    assert area_client.get("/api/backup/export", headers=stale).status_code == 409
    assert area_client.post("/api/backup/import", files={"file": ("backup.zip", raw)}, headers=stale).status_code == 409
    original = backup_apply.chat_store.save_chats
    monkeypatch.setattr(backup_apply.chat_store, "save_chats", lambda *_args: (_ for _ in ()).throw(OSError("disk full")))
    assert area_client.post("/api/backup/import", files={"file": ("backup.zip", raw)}).status_code == 400
    assert not (tmp_path / "knowledge_base/new.md").exists()
    monkeypatch.setattr(backup_apply.chat_store, "save_chats", original)
