"""Integration tests for Milestone 5: Native Local Workflow Studio, SSE End-to-End & Backup."""

import io
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from core.contracts import WorkspaceConfig
from features.ui import app as ui_app
from features.ui import chat_store, workspace


def _client(tmp_path: Path, monkeypatch: object) -> TestClient:
    mp = monkeypatch  # type: ignore[assignment]
    area = tmp_path / "wf_ws"
    area.mkdir(parents=True, exist_ok=True)
    (area / "report.md").write_text("# Q4 Program Report\n\n- Finalize client launch deck\n- Review impact metrics\n", encoding="utf-8")
    cfg = WorkspaceConfig(app_title="WF Test", knowledge_dir="wf_ws", active_dirs=["wf_ws"], strict_local_only=True)
    mp.setattr(workspace, "REPO_ROOT", tmp_path)  # type: ignore[attr-defined]
    mp.setattr(workspace, "WORKSPACE_FILE", tmp_path / "workspace.json")  # type: ignore[attr-defined]
    mp.setattr(chat_store, "REPO_ROOT", tmp_path)  # type: ignore[attr-defined]
    mp.setattr(chat_store, "CHATS_FILE", tmp_path / "chats.json")  # type: ignore[attr-defined]
    workspace.save_workspace_config(cfg, tmp_path / "workspace.json")
    mp.setattr(ui_app, "WORKSPACE_CONFIG", cfg)  # type: ignore[attr-defined]
    mp.setattr(ui_app, "INDEX", [])  # type: ignore[attr-defined]
    mp.setattr(ui_app, "_INDEX_KEY", None)  # type: ignore[attr-defined]
    return TestClient(ui_app._build_local_app())


def test_m5_html_contains_workflow_studio_canvas_toolbar_and_modals(tmp_path: Path, monkeypatch: object) -> None:
    client = _client(tmp_path, monkeypatch)
    html = client.get("/").text
    for needle in (
        'id="sidebar-workflows-btn"',
        'id="workflows-view"',
        'id="wf-toolbar"',
        'role="toolbar"',
        'focusgroup="toolbar wrap"',
        'id="wf-canvas-stage"',
        'id="wf-svg-layer"',
        'id="wf-steps-panel"',
        'id="wf-templates-modal"',
        'id="wf-run-modal"',
        "wfBindNodeDrag",
        "runActiveWorkflowStream",
    ):
        assert needle in html


def test_workflow_e2e_creates_slides_tasks_guide_impact_and_survives_zip_backup(tmp_path: Path, monkeypatch: object) -> None:
    client = _client(tmp_path, monkeypatch)
    # Install Report -> Fact-Check -> Slides + Tasks template and run live SSE stream (offline fallback works with zero network)
    tpl_res = client.post("/api/workflows/from-template/tpl_report_to_slides")
    assert tpl_res.status_code == 200
    wf_id = tpl_res.json()["item"]["id"]

    stream_res = client.post(f"/api/workflows/{wf_id}/run/stream", json={"input_text": "Q4 Program Report"})
    assert stream_res.status_code == 200
    assert "event: run_start" in stream_res.text
    assert "event: run_done" in stream_res.text

    # Verify generated .pptx file on disk and extracted Kanban tasks!
    exports_dir = tmp_path / "wf_ws" / "exports"
    assert any(p.suffix == ".pptx" for p in exports_dir.glob("*"))
    board = client.get("/api/work-board").json()
    assert len(board["tasks"]) >= 1

    # Install Weekly Review template and run it to create Impact Entry + Saved Guide!
    wk_res = client.post("/api/workflows/from-template/tpl_weekly_review")
    assert wk_res.status_code == 200
    wk_id = wk_res.json()["item"]["id"]
    wk_stream = client.post(f"/api/workflows/{wk_id}/run/stream", json={"input_text": "Week 47 milestones"})
    assert wk_stream.status_code == 200
    assert len(client.get("/api/impact").json()["impact_entries"]) >= 1
    assert any((tmp_path / "wf_ws" / "reviews").glob("*.md"))

    # Verify ZIP backup exports and restores workflows.json cleanly!
    zip_res = client.get("/api/backup/export")
    assert zip_res.status_code == 200
    with zipfile.ZipFile(io.BytesIO(zip_res.content), "r") as zf:
        assert "workflows.json" in set(zf.namelist())

    assert client.delete(f"/api/workflows/{wf_id}").status_code == 200
    assert len(client.get("/api/workflows").json()["workflows"]) == 1

    restored = client.post("/api/backup/import", files={"file": ("backup.zip", zip_res.content, "application/zip")})
    assert restored.status_code == 200
    assert len(client.get("/api/workflows").json()["workflows"]) == 2
