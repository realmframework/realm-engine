"""Tests for non-destructive folder unload/reload, SSE folder import progress, and readable graph controls."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from features.ui import area_routes, import_stream_routes


def test_unload_and_reload_subfolder_keeps_files_untouched(area_client: TestClient, tmp_path: Path) -> None:
    sub = tmp_path / "knowledge_base" / "big_pack" / "nested"
    sub.mkdir(parents=True)
    doc = sub / "deep_note.md"
    doc.write_text("# Deep Note\n\n## Core\nUnloaded without deletion.\n", encoding="utf-8")

    synced = area_client.post("/api/workspace/sync-folder")
    assert synced.status_code == 200
    assert any(g["title"] == "Deep Note" for g in area_client.get("/api/guides").json())

    # Unload hides guides from catalog, search & graph WITHOUT deleting a single file
    unloaded = area_client.post("/api/subfolders/unload", json={"path": "big_pack"})
    assert unloaded.status_code == 200
    body = unloaded.json()
    assert any(u["path"] == "big_pack" for u in body["unloaded_subfolders"])
    assert not any(f["path"].startswith("big_pack") for f in body["subfolders"])
    assert not any(g["title"] == "Deep Note" for g in area_client.get("/api/guides").json())
    assert not any(n["label"] == "Deep Note" for n in area_client.get("/api/graph?all_areas=false").json()["nodes"])
    assert doc.is_file()

    # Reload brings the guides straight back
    reloaded = area_client.post("/api/subfolders/reload", json={"path": "big_pack"})
    assert reloaded.status_code == 200
    assert reloaded.json()["unloaded_subfolders"] == []
    assert any(g["title"] == "Deep Note" for g in area_client.get("/api/guides").json())


def test_linked_vault_blocks_destructive_subfolder_delete_and_allows_unload(
    area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = tmp_path.parent / f"{tmp_path.name}_safe_vault" / "Millennium Vault"
    (vault / "Research").mkdir(parents=True)
    doc = vault / "Research" / "dossier.md"
    doc.write_text("# Dossier\n\n## Notes\nProtected on disk.\n", encoding="utf-8")

    monkeypatch.setattr(area_routes, "pick_native_folder", lambda _p="": vault)
    linked = area_client.post("/api/workspace/link-folder", json={})
    assert linked.status_code == 200

    # Permanent delete is refused for linked vaults
    blocked = area_client.delete("/api/subfolders?path=Research")
    assert blocked.status_code == 403
    assert doc.is_file()

    # Non-destructive unload succeeds and keeps disk untouched
    ul = area_client.post("/api/subfolders/unload", json={"path": "Research"})
    assert ul.status_code == 200 and ul.json()["doc_count"] == 0
    assert doc.is_file()


def test_stream_native_folder_import_emits_progress_and_done(
    area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "stream_src" / "Archive"
    src.mkdir(parents=True)
    (src / "one.md").write_text("# First\n\n## Sec\nHello.\n", encoding="utf-8")
    (src / "two.txt").write_text("Second note.", encoding="utf-8")

    monkeypatch.setattr(import_stream_routes, "pick_native_folder", lambda _p="": src)
    res = area_client.post("/api/workspace/import-native-folder/stream", json={"anonymize": False})
    assert res.status_code == 200
    text = res.text
    assert "event: start" in text
    assert "event: progress" in text
    assert "event: done" in text
    assert (tmp_path / "knowledge_base" / "Archive" / "one.md").is_file()
    assert (tmp_path / "knowledge_base" / "Archive" / "two.md").is_file()


def test_ui_exposes_progress_panel_unload_controls_and_smart_graph_hud(area_client: TestClient) -> None:
    html = area_client.get("/").text
    for marker in (
        'id="upload-progress-panel"',
        'id="upload-progress-bar"',
        'id="upload-link-vault-btn"',
        "data-unload-folder",
        "data-reload-folder",
        "data-tree-doc",
        "renderTreeDoc",
        "id='graph-controls-toggle'",
        "id='graph-controls-panel'",
        "id='graph-labels-btn'",
        "id='graph-focus-banner'",
        "id='graph-zoom-pct'",
        "id='graph-inspector-line'",
        "normalizeWheelDelta",
        "layoutConstellation",
    ):
        assert marker in html
    assert "id='graph-tooltip'" not in html
