"""Tests for code/config file support, file rename/duplicate, and subfolder rename routes."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def test_code_file_indexing_ignore_rules_and_raw_edit(area_client: TestClient, tmp_path: Path) -> None:
    kb = tmp_path / "knowledge_base"
    (kb / "src").mkdir(parents=True, exist_ok=True)
    (kb / "src/server.js").write_text("export function startServer() {\n  return 'alpha_port_9090';\n}\n", encoding="utf-8")
    (kb / "src/server.md").write_text("# Server Notes\n\n## Overview\nDocs for server.\n", encoding="utf-8")
    (kb / "src/app.py").write_text("def compute_delta(x: int) -> int:\n    return x + 42\n", encoding="utf-8")
    (kb / "config.yml").write_text("service:\n  mode: local\n", encoding="utf-8")
    # Ignored artifacts & secrets MUST never be indexed
    (kb / "node_modules/pkg").mkdir(parents=True, exist_ok=True)
    (kb / "node_modules/pkg/index.js").write_text("console.log('ignored_dep_token');\n", encoding="utf-8")
    (kb / "package-lock.json").write_text('{"lockfileVersion": 3, "secret": "ignored_lock_token"}\n', encoding="utf-8")
    (kb / ".env").write_text("API_KEY=super_secret_env_token\n", encoding="utf-8")
    (kb / "id_rsa.pem").write_text("PRIVATE_KEY_TOKEN\n", encoding="utf-8")

    sync = area_client.post("/api/workspace/sync-folder")
    assert sync.status_code == 200
    assert all("node_modules" not in str(sf.get("path", "")) for sf in sync.json().get("subfolders", []))
    guides = area_client.get("/api/guides").json()
    ids = {g["doc_id"] for g in guides}
    assert {"src/server", "src/server__js", "src/app", "config"}.issubset(ids)
    assert all("node_modules" not in g["doc_id"] and "package-lock" not in g["doc_id"] for g in guides)
    for blocked in ("ignored_dep_token", "ignored_lock_token", "super_secret_env_token", "PRIVATE_KEY_TOKEN"):
        hits = area_client.get(f"/api/search?q={blocked}&retrieval_mode=lexical").json()["results"]
        assert not hits

    raw = area_client.get("/api/guides/src/server__js/raw")
    assert raw.status_code == 200
    assert raw.json()["language"] == "javascript"
    assert "alpha_port_9090" in raw.json()["raw_markdown"]

    saved = area_client.put("/api/guides/src/server__js/raw", json={"content": "export const PORT = 8088; // updated_code_token\n"})
    assert saved.status_code == 200
    hits = area_client.get("/api/search?q=updated_code_token&retrieval_mode=lexical").json()["results"]
    assert hits and any("updated_code_token" in h["chunk"]["content"] for h in hits)


def test_rename_duplicate_file_and_rename_subfolder(area_client: TestClient, tmp_path: Path) -> None:
    kb = tmp_path / "knowledge_base"
    (kb / "docs").mkdir(parents=True, exist_ok=True)
    (kb / "docs/alpha.md").write_text("# Alpha\n\n## Body\nOriginal alpha note.\n", encoding="utf-8")
    (kb / "docs/other.md").write_text("# Other\n\n## Body\nCollision target.\n", encoding="utf-8")
    assert area_client.post("/api/workspace/sync-folder").status_code == 200

    # Duplicate creates alpha-copy.md then alpha-copy-2.md
    dup1 = area_client.post("/api/guides/docs/alpha/duplicate")
    assert dup1.status_code == 200 and dup1.json()["filename"] == "alpha-copy.md"
    dup2 = area_client.post("/api/guides/docs/alpha/duplicate")
    assert dup2.status_code == 200 and dup2.json()["filename"] == "alpha-copy-2.md"
    assert (kb / "docs/alpha-copy.md").is_file() and (kb / "docs/alpha-copy-2.md").is_file()

    # Rename file (omitting extension preserves .md) + collision returns 409
    assert area_client.post("/api/guides/docs/alpha/rename", json={"new_name": "other.md"}).status_code == 409
    ren = area_client.post("/api/guides/docs/alpha/rename", json={"new_name": "beta"})
    assert ren.status_code == 200 and ren.json()["filename"] == "beta.md" and ren.json()["doc_id"] == "docs/beta"
    assert (kb / "docs/beta.md").is_file() and not (kb / "docs/alpha.md").exists()

    # Rename subfolder + root 403 + collision 409
    (kb / "archive").mkdir(exist_ok=True)
    assert area_client.post("/api/subfolders/rename", json={"path": "", "new_name": "root"}).status_code == 403
    assert area_client.post("/api/subfolders/rename", json={"path": "docs", "new_name": "archive"}).status_code == 409
    fren = area_client.post("/api/subfolders/rename", json={"path": "docs", "new_name": "handbook"})
    assert fren.status_code == 200 and fren.json()["new_path"] == "handbook"
    assert (kb / "handbook/beta.md").is_file() and not (kb / "docs").exists()


def test_linked_vault_blocks_code_edit_rename_duplicate_and_folder_rename(area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from features.ui import area_routes

    ext_dir = tmp_path.parent / f"{tmp_path.name}_ext_repo"
    (ext_dir / "src").mkdir(parents=True, exist_ok=True)
    (ext_dir / "src/main.py").write_text("print('linked_py')\n", encoding="utf-8")
    monkeypatch.setattr(area_routes, "pick_native_folder", lambda _p="": ext_dir)
    link = area_client.post("/api/workspace/link-folder", json={})
    assert link.status_code == 200
    assert area_client.get("/api/guides/src/main/raw").status_code == 200
    assert area_client.put("/api/guides/src/main/raw", json={"content": "print('nope')\n"}).status_code == 403
    assert area_client.post("/api/guides/src/main/rename", json={"new_name": "hacked.py"}).status_code == 403
    assert area_client.post("/api/guides/src/main/duplicate").status_code == 403
    assert area_client.post("/api/subfolders/rename", json={"path": "src", "new_name": "lib"}).status_code == 403


def test_code_upload_backup_restore_and_file_watcher(area_client: TestClient, tmp_path: Path) -> None:
    from core.file_watcher import scan_directory_mtimes

    up = area_client.post("/api/upload", json={"filename": "worker.py", "content": "def run():\n    return 'py_upload_ok'\n"})
    assert up.status_code == 200
    assert (tmp_path / "knowledge_base/worker.py").is_file()
    mtimes = scan_directory_mtimes(tmp_path / "knowledge_base")
    assert mtimes is not None and "worker.py" in mtimes
    # Export backup ZIP includes worker.py and restores cleanly into a fresh workspace
    zbytes = area_client.get("/api/backup/export").content
    assert area_client.post("/api/workspace", json={"knowledge_dir": "restored_code"}).status_code == 200
    restored = area_client.post("/api/backup/import", files={"file": ("backup.zip", zbytes, "application/zip")})
    assert restored.status_code == 200
    assert (tmp_path / "restored_code/worker.py").is_file()
