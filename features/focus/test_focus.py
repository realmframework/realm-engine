"""Unit and router tests for Goal Seasons, Deep Focus auto time-sync, and Weekly Planner."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.contracts import WorkspaceConfig
from features.focus import router, service


def test_goal_trajectory_and_auto_time_sync(tmp_path: Path) -> None:
    cfg = WorkspaceConfig(app_title="Focus Test", knowledge_dir="demo_foc", active_dirs=["demo_foc"], strict_local_only=True)
    (tmp_path / "demo_foc").mkdir(parents=True, exist_ok=True)
    synced_time: list[tuple[str, float]] = []
    scheduled: list[str] = []

    app = FastAPI()
    app.include_router(
        router.build_router(
            lambda: cfg,
            None,
            lambda _a, lbl, mins, _p, _t, _n: synced_time.append((lbl, mins)),
            lambda _a: [{"title": "Draft Q4 impact deck", "project_id": "p1"}],
            lambda _a, blks: (scheduled.extend(b.title for b in blks) or len(blks)),
            lambda: tmp_path,
        )
    )
    client = TestClient(app)
    g = client.post("/api/focus/goals", json={"title": "Master Strategy Delivery", "target_hours": 10.0, "start_date": "2026-10-01", "end_date": "2026-12-31"}).json()["item"]
    sess = client.post("/api/focus/sessions", json={"label": "Deep outline sprint", "planned_minutes": 45, "actual_minutes": 60.0, "quality_rating": 5, "soundscape": "brown", "goal_id": g["id"]})
    assert sess.status_code == 200
    assert synced_time == [("Deep outline sprint", 60.0)]
    an = sess.json()["analytics"]
    assert an["total_hours"] == 1.0 and an["avg_quality"] == 5.0 and an["trajectories"][g["id"]]["logged_hours"] == 1.0

    plan = client.post("/api/focus/weekly-plan", json={"use_ai": False}).json()
    assert plan["mode"] == "deterministic" and len(plan["blocks"]) >= 4
    acc = client.post("/api/focus/weekly-plan/accept", json={"blocks": plan["blocks"]}).json()
    assert acc["scheduled_count"] == len(plan["blocks"]) and len(scheduled) == len(plan["blocks"])


def test_trajectory_pace_labels() -> None:
    state = service.FocusState()
    state, g = service.add_goal(state, "12-Week Goal", start_date="2026-01-01", end_date="2026-04-01", target_hours=10.0)
    state, _ = service.add_session(state, "Sprint 1", 60, 300.0, goal_id=g.id, date_str="2026-01-15")
    traj = service.goal_trajectory(g, state.sessions, today="2026-01-20")
    assert traj["pace"] == "ahead" and traj["pct_hours"] == 50.0
