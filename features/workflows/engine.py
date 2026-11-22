"""Async DAG executor with conditional branching, live SSE events, cancellation & scheduler."""

import asyncio
import time
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

from core.contracts import TutorConfig, WorkspaceConfig
from core.workflow_contracts import (
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowRun,
    WorkflowStepResult,
)
from features.workflows import nodes, store

ACTIVE_RUNS: dict[str, asyncio.Event] = {}


def cancel_run(run_id: str) -> bool:
    ev = ACTIVE_RUNS.get(run_id)
    if ev is None:
        return False
    ev.set()
    return True


def _edge_is_active(edge: WorkflowEdge, active: set[str], conds: dict[str, bool]) -> bool:
    if edge.source not in active:
        return False
    if edge.source in conds:
        if edge.branch == "true":
            return conds[edge.source] is True
        if edge.branch == "false":
            return conds[edge.source] is False
    return True


async def run_workflow_stream(
    wf: WorkflowDefinition,
    user_input: str,
    trigger_source: str,
    cfg: WorkspaceConfig,
    tutor_cfg: TutorConfig,
    api_key: str | None,
    callbacks: dict[str, object],
    root: Path | None = None,
) -> AsyncIterator[dict[str, object]]:
    """Execute workflow DAG, yielding live SSE dicts and ending with run_done/run_error."""
    ordered = store.topological_order(wf.nodes, wf.edges)
    run_id, cancel_ev, started_at = store.new_id("run"), asyncio.Event(), store.utc_now()
    ACTIVE_RUNS[run_id] = cancel_ev
    inc: dict[str, list[WorkflowEdge]] = {}
    for edge in wf.edges:
        inc.setdefault(edge.target, []).append(edge)
    steps: list[WorkflowStepResult] = []
    outputs: dict[str, str] = {}
    active_nodes: set[str] = set()
    conds: dict[str, bool] = {}
    status, err_msg = "completed", ""
    yield {"event": "run_start", "run_id": run_id, "workflow_id": wf.id, "workflow_name": wf.name, "total_steps": len(ordered)}
    try:
        for node in ordered:
            if cancel_ev.is_set():
                status = "cancelled"
                break
            parents = inc.get(node.id, [])
            if parents:
                live = [e for e in parents if _edge_is_active(e, active_nodes, conds)]
                if not live:
                    sr = WorkflowStepResult(node_id=node.id, label=node.label, kind=node.kind, status="skipped", artifact_note="Branch not taken")
                    steps.append(sr)
                    yield {"event": "step_skipped", "run_id": run_id, "step": sr.model_dump()}
                    continue
                prev_text = "\n\n".join(outputs.get(e.source, "") for e in live if outputs.get(e.source, "")).strip()
            else:
                prev_text = user_input
            yield {"event": "step_start", "run_id": run_id, "node_id": node.id, "label": node.label, "kind": node.kind}
            t0 = time.monotonic()
            out_text, note, cond_val = await nodes.execute_node(node, user_input, prev_text, cfg, tutor_cfg, api_key, cancel_ev, callbacks, root)
            ms = max(0, int((time.monotonic() - t0) * 1000))
            outputs[node.id] = out_text
            active_nodes.add(node.id)
            if cond_val is not None:
                conds[node.id] = cond_val
            sr = WorkflowStepResult(node_id=node.id, label=node.label, kind=node.kind, status="completed", output_preview=out_text[:1000], artifact_note=note[:290], duration_ms=ms)
            steps.append(sr)
            yield {"event": "step_done", "run_id": run_id, "step": sr.model_dump()}
    except asyncio.CancelledError:
        status = "cancelled"
    except Exception as exc:
        status, err_msg = "failed", str(exc)[:580]
        yield {"event": "run_error", "run_id": run_id, "error": err_msg}
    finally:
        ACTIVE_RUNS.pop(run_id, None)
    run = WorkflowRun.model_validate({
        "run_id": run_id, "workflow_id": wf.id, "workflow_name": wf.name, "trigger_source": trigger_source,
        "status": status, "started_at": started_at, "finished_at": store.utc_now(),
        "steps": [s.model_dump() for s in steps], "error": err_msg,
    })
    yield {"event": "run_done", "run": run.model_dump()}


def due_scheduled_workflows(workflows: list[WorkflowDefinition], runs: list[WorkflowRun], now: datetime | None = None) -> list[WorkflowDefinition]:
    """Return enabled scheduled workflows whose interval has elapsed since last run."""
    ref, last_by_wf = now or datetime.now(UTC), {}
    for run in runs:
        if run.workflow_id not in last_by_wf:
            try:
                last_by_wf[run.workflow_id] = datetime.fromisoformat(run.started_at)
            except ValueError:
                continue
    return [
        wf for wf in workflows
        if wf.enabled and wf.trigger_kind == "schedule" and wf.schedule_minutes >= 5
        and (wf.id not in last_by_wf or (ref - last_by_wf[wf.id]) >= timedelta(minutes=wf.schedule_minutes))
    ]


async def run_workflow_silent(
    wf: WorkflowDefinition, user_input: str, trigger_source: str, cfg: WorkspaceConfig,
    tutor_cfg: TutorConfig, callbacks: dict[str, object], save_run: Callable[[WorkflowRun], None], root: Path | None = None,
) -> WorkflowRun | None:
    """Execute a workflow non-interactively for local schedule or event triggers."""
    final_run: WorkflowRun | None = None
    async for ev in run_workflow_stream(wf, user_input, trigger_source, cfg, tutor_cfg, None, callbacks, root):
        if ev.get("event") == "run_done" and isinstance(ev.get("run"), dict):
            final_run = WorkflowRun.model_validate(ev["run"])
            save_run(final_run)
    return final_run


async def tick_scheduled_workflows(cfg: WorkspaceConfig, callbacks: dict[str, object], root: Path | None = None) -> int:
    """Run any locally scheduled workflows that are due for the active workspace."""
    path = store.workflows_path(cfg.knowledge_dir, root)
    state = store.load_workflows(path)
    due = due_scheduled_workflows(state.workflows, state.runs)
    for wf in due:
        await run_workflow_silent(
            wf, wf.name, "schedule", cfg, TutorConfig(provider="ollama", model="qwen3:8b", temperature=0.2),
            callbacks, lambda run: store.save_workflows(store.record_run(store.load_workflows(path), run), path), root,
        )
    return len(due)
