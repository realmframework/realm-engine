"""Unit and API tests for Time Tracking, Wirksamkeitsdokumentation, ROI math, and PDF/PPTX reports."""

import io
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pptx import Presentation

from core.contracts import WorkspaceConfig
from features.impact_ledger import router, service, store


def _make_client(tmp_path: Path) -> TestClient:
    cfg = WorkspaceConfig(app_title="Impact Test", knowledge_dir="demo_imp", active_dirs=["demo_imp"], strict_local_only=True)
    (tmp_path / "demo_imp").mkdir(parents=True, exist_ok=True)
    app = FastAPI()
    app.include_router(router.build_router(lambda: cfg, None, lambda _a: {"p1": "Strategy Q4"}, lambda: tmp_path))
    return TestClient(app)


def test_roi_math_zero_division_and_csv_formula_guard() -> None:
    empty = store.ImpactLedgerState()
    s0 = store.compute_roi_summary(empty)
    assert s0["total_cost"] == 0.0 and s0["roi_pct"] is None

    state, _ = service.add_time_entry(empty, "=CMD() Workshop", 120.0, project_id="p1", hourly_rate=100.0)
    state, _ = service.add_impact_entry(state, "Automated weekly briefing", "Saved 4 hours per week", project_id="p1", direct_cost=50.0, estimated_value=500.0, time_saved_hours=2.0)
    s1 = store.compute_roi_summary(state)
    # Time cost = 2h * 100 = 200; direct_cost = 50 -> total_cost = 250; value = 500 + 2h * 85 (default rate) = 670 -> net = 420 -> ROI = 168.0%
    assert s1["total_cost"] == 250.0 and s1["total_value"] == 670.0 and s1["net_impact"] == 420.0 and s1["roi_pct"] == 168.0
    csv_out = store.export_timesheet_csv(state)
    assert "'=CMD() Workshop" in csv_out


def test_timer_lifecycle_impact_crud_and_pdf_pptx_reports(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    assert client.post("/api/impact/timer/start", json={"label": "Client deck prep", "project_id": "p1"}).status_code == 200
    assert client.post("/api/impact/timer/toggle").json()["active_timer"]["is_paused"] is True
    stopped = client.post("/api/impact/timer/stop", json={"notes": "Finished outline"})
    assert stopped.status_code == 200 and len(stopped.json()["time_entries"]) == 1

    imp = client.post("/api/impact/entries", json={"what_done": "Delivered workshop", "effect": "Aligned 12 stakeholders", "project_id": "p1", "estimated_value": 1200.0, "time_saved_hours": 3.0})
    assert imp.status_code == 200 and imp.json()["summary"]["impact_count"] == 1

    draft = client.post("/api/impact/draft", json={"notes": "Ran design review\nCut onboarding time in half", "hours": 2.5, "use_ai": False})
    assert draft.status_code == 200 and draft.json()["draft"]["what_done"] == "Ran design review"

    pdf_res = client.post("/api/impact/report", json={"format": "pdf"})
    assert pdf_res.status_code == 200 and pdf_res.content.startswith(b"%PDF")

    pptx_res = client.post("/api/impact/report", json={"format": "pptx"})
    assert pptx_res.status_code == 200
    prs = Presentation(io.BytesIO(pptx_res.content))
    assert len(prs.slides) == 3

    csv_res = client.get("/api/impact/timesheet.csv")
    assert csv_res.status_code == 200 and "Client deck prep" in csv_res.text
