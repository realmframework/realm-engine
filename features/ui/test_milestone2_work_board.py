"""Integration tests for Milestone 2 (Work Board UI shell, Library sync, and ZIP backup)."""

from pathlib import Path

from fastapi.testclient import TestClient

from core.contracts import WorkspaceConfig
from features.ui import app as ui_app
from features.ui import chat_store, workspace


def _isolated_client(tmp_path: Path, monkeypatch: object) -> TestClient:
    mp = monkeypatch  # type: ignore[assignment]
    area = tmp_path / "work_ws"
    area.mkdir(parents=True, exist_ok=True)
    (area / "meeting_notes.md").write_text("# Q2 Planning\n\n- [ ] Finalize impact report by 2026-06-15\n- [ ] Urgent: Review budget\n", encoding="utf-8")
    cfg = WorkspaceConfig(app_title="Work OS", knowledge_dir="work_ws", active_dirs=["work_ws"], strict_local_only=True)
    mp.setattr(workspace, "REPO_ROOT", tmp_path)  # type: ignore[attr-defined]
    mp.setattr(workspace, "WORKSPACE_FILE", tmp_path / "workspace.json")  # type: ignore[attr-defined]
    mp.setattr(chat_store, "REPO_ROOT", tmp_path)  # type: ignore[attr-defined]
    mp.setattr(chat_store, "CHATS_FILE", tmp_path / "chats.json")  # type: ignore[attr-defined]
    workspace.save_workspace_config(cfg, tmp_path / "workspace.json")
    mp.setattr(ui_app, "WORKSPACE_CONFIG", cfg)  # type: ignore[attr-defined]
    mp.setattr(ui_app, "INDEX", [])  # type: ignore[attr-defined]
    mp.setattr(ui_app, "_INDEX_KEY", None)  # type: ignore[attr-defined]
    return TestClient(ui_app._build_local_app())


def test_work_board_html_and_extract_from_guide_and_sync(tmp_path: Path, monkeypatch: object) -> None:
    client = _isolated_client(tmp_path, monkeypatch)
    html = client.get("/").text
    for needle in ("sidebar-work-btn", "work-board-view", "wb-tab-kanban", "wb-tab-calendar", "work-task-modal", "work-project-modal", "work-event-modal", "work-extract-modal"):
        assert needle in html

    ext = client.post("/api/work-board/extract", json={"doc_id": "meeting_notes", "use_ai": False})
    assert ext.status_code == 200
    data = ext.json()
    assert data["created_count"] == 2
    assert any(tk["priority"] == "urgent" for tk in data["tasks"])
    assert any(tk["due_date"] == "2026-06-15" for tk in data["tasks"])

    sync = client.post("/api/work-board/sync-vault")
    assert sync.status_code == 200
    assert (tmp_path / "work_ws" / "work_board_snapshot.md").is_file()


def test_zip_backup_preserves_work_board_json(tmp_path: Path, monkeypatch: object) -> None:
    client = _isolated_client(tmp_path, monkeypatch)
    client.post("/api/work-board/projects", json={"title": "Annual Strategy", "color": "#38D399"})
    client.post("/api/work-board/tasks", json={"title": "Prepare deck", "due_date": "2026-07-01"})
    client.post("/api/work-board/events", json={"title": "Kickoff", "date": "2026-07-02", "start_time": "09:30", "end_time": "10:30"})

    export_res = client.get("/api/backup/export")
    assert export_res.status_code == 200
    zip_bytes = export_res.content

    wb_file = tmp_path / "work_ws" / "work_board.json"
    assert wb_file.is_file()
    wb_file.unlink()
    assert client.get("/api/work-board").json()["tasks"] == []

    imp = client.post("/api/backup/import", files={"file": ("backup.zip", zip_bytes, "application/zip")})
    assert imp.status_code == 200
    restored = client.get("/api/work-board").json()
    assert len(restored["projects"]) == 1 and restored["projects"][0]["title"] == "Annual Strategy"
    assert len(restored["tasks"]) == 1 and restored["tasks"][0]["title"] == "Prepare deck"
    assert len(restored["events"]) == 1 and restored["events"][0]["title"] == "Kickoff"
