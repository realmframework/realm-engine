"""Tests for Phase 5: Eco Mode context diet, incremental file watcher, and search highlights."""

import time
from pathlib import Path

from fastapi.testclient import TestClient

from core.file_watcher import (
    FileStamp,
    diff_snapshots,
    poll_watch_cycle,
    scan_directory_mtimes,
)


def test_incremental_file_watcher_detects_added_modified_and_removed(tmp_path: Path) -> None:
    vault = tmp_path / "notes"
    vault.mkdir()
    doc = vault / "first.md"
    doc.write_text("# First\n", encoding="utf-8")
    (vault / ".hidden.md").write_text("ignored", encoding="utf-8")
    snapshots: dict[str, dict[str, FileStamp]] = {}
    assert poll_watch_cycle({"notes": vault}, snapshots) == {}
    assert list(snapshots["notes"].keys()) == ["first.md"]

    # Add second file
    second = vault / "second.md"
    second.write_text("# Second\n", encoding="utf-8")
    changes = poll_watch_cycle({"notes": vault}, snapshots)
    assert changes == {"notes": ["second.md"]}

    # Modify first file (ensure distinct mtime_ns)
    time.sleep(0.01)
    doc.write_text("# First Updated\n", encoding="utf-8")
    changes2 = poll_watch_cycle({"notes": vault}, snapshots)
    assert changes2 == {"notes": ["first.md"]}

    # Remove second file
    second.unlink()
    changes3 = poll_watch_cycle({"notes": vault}, snapshots)
    assert changes3 == {"notes": ["second.md"]}
    scanned = scan_directory_mtimes(vault)
    assert scanned is not None
    assert diff_snapshots({"a.md": (1, 1)}, scanned)[2] == ["a.md"]


def test_eco_mode_caps_retrieval_and_sync_status_endpoint(area_client: TestClient) -> None:
    for i in range(5):
        assert area_client.post(
            "/api/guides/create",
            json={"title": f"Eco Doc {i}", "content": f"## Section\nEco benchmark keyword passage number {i}."},
        ).status_code == 200
    assert area_client.post("/api/workspace/appearance", json={"eco_mode": True}).status_code == 200
    res = area_client.get("/api/search", params={"q": "Eco benchmark keyword", "top_k": 10, "retrieval_mode": "lexical"})
    assert res.status_code == 200
    assert res.json()["rag_config"]["top_k"] <= 3
    assert "Eco" in res.json()["rag_config"]["router_label"]
    assert len(res.json()["results"]) <= 3

    st = area_client.get("/api/workspace/sync-status")
    assert st.status_code == 200 and "sync_version" in st.json() and "watching" in st.json()
    html = area_client.get("/").text
    assert 'id="eco-mode-toggle"' in html and "search-hit-mark" in html
