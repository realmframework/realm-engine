"""Unit & integration tests for Milestone 5 Workflow DAG engine, branching, privacy & cancellation."""

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.contracts import TutorConfig, WorkspaceConfig
from core.workflow_contracts import WorkflowEdge, WorkflowNode, WorkflowRun
from features.workflows import engine, router, store, templates


def test_dag_cycle_detection_and_topological_order() -> None:
    nodes = [
        WorkflowNode(id="a", kind="trigger", label="Start"),
        WorkflowNode(id="b", kind="vault_search", label="Search"),
        WorkflowNode(id="c", kind="save_guide", label="Save"),
    ]
    order = store.topological_order(nodes, [WorkflowEdge(id="e1", source="a", target="b"), WorkflowEdge(id="e2", source="b", target="c")])
    assert [n.id for n in order] == ["a", "b", "c"]

    with pytest.raises(ValueError, match="cycle"):
        store.topological_order(nodes, [WorkflowEdge(id="e1", source="a", target="b"), WorkflowEdge(id="e2", source="b", target="a")])

    with pytest.raises(ValueError, match="self-loop"):
        store.topological_order(nodes, [WorkflowEdge(id="e1", source="a", target="a")])


def test_conditional_branching_and_local_privacy_guard(tmp_path: Path) -> None:
    cfg = WorkspaceConfig(app_title="WF", knowledge_dir="demo", active_dirs=["demo"], strict_local_only=True)
    st, wf = store.add_workflow(
        store.WorkflowState(),
        "Branching Test",
        "",
        "manual",
        0,
        [
            WorkflowNode(id="n1", kind="trigger", label="Start"),
            WorkflowNode(id="n2", kind="condition", label="Has Urgent", config={"contains": "urgent"}),
            WorkflowNode(id="n3", kind="extract_tasks", label="True Path"),
            WorkflowNode(id="n4", kind="save_guide", label="False Path", config={"title": "Archive"}),
        ],
        [
            WorkflowEdge(id="e1", source="n1", target="n2"),
            WorkflowEdge(id="e2", source="n2", target="n3", branch="true"),
            WorkflowEdge(id="e3", source="n2", target="n4", branch="false"),
        ],
    )
    called: list[str] = []
    cbs: dict[str, object] = {
        "extract_tasks": lambda txt, _p: called.append("tasks") or 2,
        "save_guide": lambda title, _m, _s: called.append(f"guide:{title}") or "archive.md",
    }

    async def _run() -> list[dict[str, object]]:
        return [ev async for ev in engine.run_workflow_stream(wf, "Urgent client deadline", "manual", cfg, TutorConfig(), None, cbs, tmp_path)]

    events = asyncio.run(_run())
    assert called == ["tasks"]
    skipped = [st_ev["node_id"] for ev in events if ev.get("event") == "step_skipped" and isinstance(st_ev := ev.get("step"), dict)]
    assert skipped == ["n4"]

    # Local-only lock blocks cloud provider on run_agent node
    _, ai_wf = store.add_workflow(st, "AI", "", "manual", 0, [WorkflowNode(id="a1", kind="run_agent", label="Agent")], [])
    async def _run_cloud() -> list[dict[str, object]]:
        return [ev async for ev in engine.run_workflow_stream(ai_wf, "hi", "manual", cfg, TutorConfig(provider="openai", model="gpt-4o-mini"), None, {}, tmp_path)]

    cloud_events = asyncio.run(_run_cloud())
    assert any(ev.get("event") == "run_error" and "Local-Only" in str(ev.get("error")) for ev in cloud_events)


def test_cancellation_and_due_schedule_detection(tmp_path: Path) -> None:
    cfg = WorkspaceConfig(app_title="WF", knowledge_dir="demo", active_dirs=["demo"], strict_local_only=True)
    _, wf = store.add_workflow(
        store.WorkflowState(),
        "Slow Agent",
        "",
        "schedule",
        30,
        [WorkflowNode(id="n1", kind="run_agent", label="Slow")],
        [],
    )

    async def _slow_stream(*_args: object, **_kwargs: object):
        for i in range(10):
            await asyncio.sleep(0.02)
            yield {"event": "token", "text": f"tok{i}"}

    async def _run_cancel() -> str:
        run_status = ""
        async for ev in engine.run_workflow_stream(wf, "go", "manual", cfg, TutorConfig(), None, {"stream_messages": _slow_stream}, tmp_path):
            if ev.get("event") == "run_start":
                engine.cancel_run(str(ev["run_id"]))
            if ev.get("event") == "run_done" and isinstance(run_obj := ev.get("run"), dict):
                run_status = str(run_obj["status"])
        return run_status

    assert asyncio.run(_run_cancel()) == "cancelled"

    now = datetime.now(UTC)
    assert [w.id for w in engine.due_scheduled_workflows([wf], [], now)] == [wf.id]
    recent_run = WorkflowRun(run_id="r1", workflow_id=wf.id, workflow_name=wf.name, status="completed", started_at=(now - timedelta(minutes=5)).isoformat())
    assert engine.due_scheduled_workflows([wf], [recent_run], now) == []


def test_router_templates_sse_and_cycle_rejection(tmp_path: Path) -> None:
    cfg = WorkspaceConfig(app_title="WF", knowledge_dir="demo", active_dirs=["demo"], strict_local_only=True)
    app = FastAPI()
    app.include_router(
        router.build_router(
            lambda: cfg,
            lambda _c: {
                "vault_search": lambda q, k: f"Found passages for {q} ({k})",
                "extract_tasks": lambda _t, _p: 3,
                "generate_slides": lambda title, _m, fmt: f"{title}.{fmt}",
                "save_guide": lambda title, _m, _s: f"{title}.md",
                "log_impact": lambda _w, _e, _t: "imp_123",
            },
            lambda: tmp_path,
        )
    )
    client = TestClient(app)
    assert len(templates.starter_templates(store.utc_now())) == 4
    inst = client.post("/api/workflows/from-template/tpl_report_to_slides")
    assert inst.status_code == 200
    wf_id = inst.json()["item"]["id"]

    stream = client.post(f"/api/workflows/{wf_id}/run/stream", json={"input_text": "Q4 Review"})
    assert stream.status_code == 200
    assert "event: run_start" in stream.text
    assert "event: run_done" in stream.text
    assert len(client.get("/api/workflows/runs").json()["runs"]) == 1

    bad = client.post(
        "/api/workflows",
        json={
            "name": "Cyclic",
            "nodes": [{"id": "a", "kind": "trigger", "label": "A"}, {"id": "b", "kind": "save_guide", "label": "B"}],
            "edges": [{"id": "e1", "source": "a", "target": "b"}, {"id": "e2", "source": "b", "target": "a"}],
        },
    )
    assert bad.status_code == 400
