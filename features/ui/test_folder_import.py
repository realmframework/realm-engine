"""Tests for recursive folder upload, native folder import, Obsidian linked vaults, and modal polish."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from features.ui import area_routes, folder_routes, native_import_routes


def test_recursive_folder_upload_preserves_subfolders_and_skips_junk(area_client: TestClient, tmp_path: Path) -> None:
    res = area_client.post(
        "/api/upload",
        files=[
            ("files", (".DS_Store", b"\x00\x01\x02", "application/octet-stream")),
            ("files", ("notes.txt", b"Local hybrid search notes.", "text/plain")),
            ("files", ("metrics.csv", b"Name,Value\nLatency,12ms\n", "text/csv")),
            ("files", ("archive.bin", b"\xff\xfe", "application/octet-stream")),
        ],
        data={
            "relative_paths": [
                "Project Alpha/.DS_Store",
                "Project Alpha/Docs/notes.txt",
                "Project Alpha/Data (2026)/metrics.csv",
                "Project Alpha/archive.bin",
            ],
            "skip_unsupported": "true",
            "anonymize": "false",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["skipped_files"] == 2 and len(body["uploaded_files"]) == 2
    assert (tmp_path / "knowledge_base" / "Project Alpha" / "Docs" / "notes.md").is_file()
    assert any(p.name == "metrics.md" for p in (tmp_path / "knowledge_base" / "Project Alpha").rglob("*.md"))


def test_reveal_and_sync_folder_endpoints(area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    revealed: list[Path] = []
    monkeypatch.setattr(folder_routes, "_open_native_folder", lambda target: revealed.append(target))

    rev = area_client.post("/api/workspace/reveal-folder", json={"subfolder": ""})
    assert rev.status_code == 200 and rev.json()["revealed"] is True
    assert revealed == [tmp_path / "knowledge_base"]
    assert area_client.post("/api/workspace/reveal-folder", json={"subfolder": "../../etc"}).status_code == 400

    dropped = tmp_path / "knowledge_base" / "finder_drop" / "sub"
    dropped.mkdir(parents=True)
    (dropped / "dropped_note.md").write_text("# Dropped Note\n\n## Intro\nAdded in Finder.\n", encoding="utf-8")

    synced = area_client.post("/api/workspace/sync-folder")
    assert synced.status_code == 200
    assert any(f["path"] == "finder_drop/sub" for f in synced.json()["subfolders"])


def test_native_folder_import_preserves_tree_skips_hidden_and_handles_cancel(
    area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(native_import_routes, "pick_native_folder", lambda _prompt="": None)
    cancelled = area_client.post("/api/workspace/import-native-folder", json={})
    assert cancelled.status_code == 200 and cancelled.json()["cancelled"] is True

    external = tmp_path / "outside_src" / "Team Wiki"
    (external / ".git").mkdir(parents=True)
    (external / "Specs" / "2026").mkdir(parents=True)
    (external / ".git" / "config").write_text("hidden", encoding="utf-8")
    (external / ".DS_Store").write_bytes(b"\x00\x01")
    (external / "Specs" / "2026" / "plan.md").write_text("# Launch Plan\n\n## Goal\nShip clean.\n", encoding="utf-8")
    (external / "Specs" / "table.csv").write_text("K,V\nA,1\n", encoding="utf-8")
    (external / "Specs" / "blob.bin").write_bytes(b"\xff\xfe")

    monkeypatch.setattr(native_import_routes, "pick_native_folder", lambda _prompt="": external)
    res = area_client.post("/api/workspace/import-native-folder", json={"anonymize": False})
    assert res.status_code == 200
    body = res.json()
    assert body["cancelled"] is False and body["imported_count"] == 2 and body["skipped_count"] >= 3
    assert (tmp_path / "knowledge_base" / "Team Wiki" / "Specs" / "2026" / "plan.md").is_file()
    assert (tmp_path / "knowledge_base" / "Team Wiki" / "Specs" / "table.md").is_file()
    assert not (tmp_path / "knowledge_base" / "Team Wiki" / ".git").exists()


def test_obsidian_style_linked_vault_lifecycle(
    area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = tmp_path.parent / f"{tmp_path.name}_obsidian_vault" / "Yggdrasil HQ"
    (vault / ".obsidian").mkdir(parents=True)
    (vault / "Projects").mkdir()
    doc = vault / "Projects" / "guide.md"
    doc.write_text("# Yggdrasil Architecture\n\n## Overview\nZero-copy Obsidian vault.\n", encoding="utf-8")
    (vault / ".obsidian" / "app.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(area_routes, "pick_native_folder", lambda _prompt="": None)
    assert area_client.post("/api/workspace/link-folder", json={}).json()["cancelled"] is True

    monkeypatch.setattr(area_routes, "pick_native_folder", lambda _prompt="": vault)
    linked = area_client.post("/api/workspace/link-folder", json={})
    assert linked.status_code == 200
    data = linked.json()
    slug = data["linked_area"]
    assert slug == "yggdrasil_hq" and data["doc_count"] == 1
    assert any(a["name"] == slug and a["linked"] is True and a["display_name"] == "Yggdrasil HQ" for a in data["areas"])
    assert not (vault / "index.json").exists() and not (vault / ".knowledge-area.json").exists()
    assert not any(".obsidian" in f["path"] for f in data["subfolders"])

    # Graph & search work directly against the linked vault in place
    graph = area_client.get("/api/graph?all_areas=false")
    assert graph.status_code == 200
    assert any(n["label"] == "Yggdrasil HQ" for n in graph.json()["nodes"])

    # Unlinking removes only REALM's reference and keeps the external folder intact
    removed = area_client.delete(f"/api/workspace/{slug}")
    assert removed.status_code == 200 and removed.json()["unlinked"] is True
    assert doc.is_file() and (vault / ".obsidian" / "app.json").is_file()


def test_ui_exposes_linked_vault_native_import_and_modal_switches(area_client: TestClient) -> None:
    html = area_client.get("/").text
    for marker in (
        'id="upload-folder-input"',
        "webkitdirectory",
        'id="import-native-folder-btn"',
        'id="link-vault-btn"',
        'id="settings-link-vault-btn"',
        'id="cfg-anonymize-uploads" type="checkbox" switch',
        'id="settings-reveal-folder-btn"',
        'id="settings-sync-folder-btn"',
        "linkExistingFolder",
        "importNativeFolder",
        "dialog .text-xs",
        "dialog select",
    ):
        assert marker in html
