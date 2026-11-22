"""Integration tests for Milestone 4: Time Tracking, Wirksamkeit/ROI, Superfocus & Backup."""

import io
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from core.contracts import WorkspaceConfig
from features.ui import app as ui_app
from features.ui import chat_store, workspace


def _client(tmp_path: Path, monkeypatch: object) -> TestClient:
    mp = monkeypatch  # type: ignore[assignment]
    area = tmp_path / "impact_ws"
    area.mkdir(parents=True, exist_ok=True)
    (area / "guide.md").write_text("# Program Notes\n\nLocal-only impact tracking.\n", encoding="utf-8")
    cfg = WorkspaceConfig(app_title="Impact Test", knowledge_dir="impact_ws", active_dirs=["impact_ws"], strict_local_only=True)
    mp.setattr(workspace, "REPO_ROOT", tmp_path)  # type: ignore[attr-defined]
    mp.setattr(workspace, "WORKSPACE_FILE", tmp_path / "workspace.json")  # type: ignore[attr-defined]
    mp.setattr(chat_store, "REPO_ROOT", tmp_path)  # type: ignore[attr-defined]
    mp.setattr(chat_store, "CHATS_FILE", tmp_path / "chats.json")  # type: ignore[attr-defined]
    workspace.save_workspace_config(cfg, tmp_path / "workspace.json")
    mp.setattr(ui_app, "WORKSPACE_CONFIG", cfg)  # type: ignore[attr-defined]
    mp.setattr(ui_app, "INDEX", [])  # type: ignore[attr-defined]
    mp.setattr(ui_app, "_INDEX_KEY", None)  # type: ignore[attr-defined]
    return TestClient(ui_app._build_local_app())


def test_m4_html_contains_sidebar_views_progress_rings_and_modals(tmp_path: Path, monkeypatch: object) -> None:
    client = _client(tmp_path, monkeypatch)
    html = client.get("/").text
    for needle in (
        'id="sidebar-focus-btn"',
        'id="sidebar-impact-btn"',
        'id="focus-view"',
        'id="impact-view"',
        'id="deep-focus-modal"',
        'id="goal-season-modal"',
        'id="impact-entry-modal"',
        'class="focus-ring"',
        "goal-progress",
        "startFocusSoundscape",
        "downloadImpactReport",
    ):
        assert needle in html


def test_focus_session_auto_logs_time_and_weekly_plan_schedules_calendar(tmp_path: Path, monkeypatch: object) -> None:
    client = _client(tmp_path, monkeypatch)
    proj = client.post("/api/work-board/projects", json={"title": "Q4 Program", "color": "#4BB8E8"}).json()["projects"][-1]
    goal = client.post(
        "/api/focus/goals",
        json={"title": "Ship Impact Review", "start_date": "2026-11-01", "end_date": "2026-12-31", "target_hours": 15, "project_id": proj["id"]},
    ).json()["item"]
    sess = client.post(
        "/api/focus/sessions",
        json={"label": "Draft executive brief", "planned_minutes": 45, "actual_minutes": 45, "quality_rating": 5, "soundscape": "brown", "goal_id": goal["id"], "project_id": proj["id"], "log_time": True},
    )
    assert sess.status_code == 200
    impact = client.get("/api/impact").json()
    assert len(impact["time_entries"]) == 1
    assert impact["time_entries"][0]["source"] == "focus"
    assert impact["time_entries"][0]["duration_minutes"] == 45.0

    plan = client.post("/api/focus/weekly-plan", json={"use_ai": False, "language": "de"}).json()
    assert len(plan["blocks"]) >= 1
    accepted = client.post("/api/focus/weekly-plan/accept", json={"blocks": plan["blocks"][:2]}).json()
    assert accepted["scheduled_count"] == len(plan["blocks"][:2])
    board = client.get("/api/work-board").json()
    assert len(board["events"]) == len(plan["blocks"][:2])


def test_impact_reports_csv_and_zip_backup_roundtrip(tmp_path: Path, monkeypatch: object) -> None:
    client = _client(tmp_path, monkeypatch)
    created = client.post(
        "/api/impact/entries",
        json={"what_done": "Standardized onboarding checklist", "effect": "Cut setup questions in half", "hours_invested": 3.0, "time_saved_hours": 8.0, "estimated_value": 1200.0, "outcome_tag": "time_saved"},
    )
    assert created.status_code == 200
    assert client.post("/api/focus/goals", json={"title": "Q4 Focus", "start_date": "2026-11-01", "end_date": "2026-12-31", "target_hours": 10}).status_code == 200
    assert client.post("/api/impact/report", json={"format": "pdf"}).content.startswith(b"%PDF")
    assert client.post("/api/impact/report", json={"format": "pptx"}).content.startswith(b"PK")
    assert "Duration (min)" in client.get("/api/impact/timesheet.csv").text

    backup_res = client.get("/api/backup/export")
    assert backup_res.status_code == 200
    with zipfile.ZipFile(io.BytesIO(backup_res.content), "r") as zf:
        names = set(zf.namelist())
        assert "impact_ledger.json" in names
        assert "focus_engine.json" in names

    entry_id = created.json()["item"]["id"]
    assert client.delete(f"/api/impact/entries/{entry_id}").status_code == 200
    assert client.get("/api/impact").json()["impact_entries"] == []

    restored = client.post("/api/backup/import", files={"file": ("backup.zip", backup_res.content, "application/zip")})
    assert restored.status_code == 200
    after = client.get("/api/impact").json()
    assert len(after["impact_entries"]) == 1
    assert after["impact_entries"][0]["what_done"] == "Standardized onboarding checklist"
