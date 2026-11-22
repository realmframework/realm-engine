"""Atomic local persistence, DAG cycle validation, and CRUD for Workflow Pipelines."""

from collections import deque
from pathlib import Path

from core.json_store import (
    area_store_path,
    load_model_json,
    new_id,
    save_model_json,
    store_lock,
    utc_now,
)
from core.workflow_contracts import (
    WorkflowDefinition,
    WorkflowEdge,
    WorkflowNode,
    WorkflowRun,
    WorkflowState,
)
from features.workflows.templates import starter_templates

MAX_RUN_HISTORY = 40

__all__ = [
    "MAX_RUN_HISTORY", "add_workflow", "delete_workflow", "install_template",
    "load_workflows", "new_id", "record_run", "save_workflows", "store_lock",
    "topological_order", "update_workflow", "utc_now", "workflows_path",
]


def workflows_path(area: str, root: Path | None = None) -> Path:
    return area_store_path(area, "workflows.json", root)


def topological_order(nodes: list[WorkflowNode], edges: list[WorkflowEdge]) -> list[WorkflowNode]:
    """Validate DAG integrity and return nodes in deterministic topological order."""
    by_id = {node.id: node for node in nodes}
    if len(by_id) != len(nodes):
        raise ValueError("Duplicate node IDs in workflow")
    indegree: dict[str, int] = {node.id: 0 for node in nodes}
    adj: dict[str, list[str]] = {node.id: [] for node in nodes}
    for edge in edges:
        if edge.source not in by_id or edge.target not in by_id:
            raise ValueError(f"Edge {edge.id} references unknown node")
        if edge.source == edge.target:
            raise ValueError("Workflow contains a cycle (self-loop)")
        adj[edge.source].append(edge.target)
        indegree[edge.target] += 1
    queue = deque(node.id for node in nodes if indegree[node.id] == 0)
    ordered: list[WorkflowNode] = []
    while queue:
        nid = queue.popleft()
        ordered.append(by_id[nid])
        for nxt in adj[nid]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    if len(ordered) != len(nodes):
        raise ValueError("Workflow contains a cycle")
    return ordered


def load_workflows(path: Path) -> WorkflowState:
    return load_model_json(path, WorkflowState, WorkflowState)


def save_workflows(state: WorkflowState, path: Path) -> WorkflowState:
    return save_model_json(state, path, WorkflowState)


def add_workflow(
    state: WorkflowState,
    name: str,
    description: str,
    trigger_kind: str,
    schedule_minutes: int,
    nodes: list[WorkflowNode],
    edges: list[WorkflowEdge],
    enabled: bool = True,
) -> tuple[WorkflowState, WorkflowDefinition]:
    clean_nodes = nodes or [WorkflowNode(id="n1", kind="trigger", label="Manual Trigger", x=40, y=100, config={"trigger_kind": trigger_kind})]
    topological_order(clean_nodes, edges)
    now = utc_now()
    wf = WorkflowDefinition.model_validate({
        "id": new_id("wf"),
        "name": name.strip() or "Untitled Workflow",
        "description": description.strip(),
        "enabled": enabled,
        "trigger_kind": trigger_kind,
        "schedule_minutes": schedule_minutes,
        "nodes": [n.model_dump() for n in clean_nodes],
        "edges": [e.model_dump() for e in edges],
        "created_at": now,
        "updated_at": now,
    })
    return state.model_copy(update={"workflows": [wf, *state.workflows]}), wf


def update_workflow(state: WorkflowState, wf_id: str, patch: dict[str, object]) -> tuple[WorkflowState, WorkflowDefinition | None]:
    updated: WorkflowDefinition | None = None
    items: list[WorkflowDefinition] = []
    for wf in state.workflows:
        if wf.id != wf_id:
            items.append(wf)
            continue
        merged = {**wf.model_dump(), **{k: v for k, v in patch.items() if v is not None}, "updated_at": utc_now()}
        candidate = WorkflowDefinition.model_validate(merged)
        topological_order(candidate.nodes, candidate.edges)
        updated = candidate
        items.append(candidate)
    return state.model_copy(update={"workflows": items}), updated


def delete_workflow(state: WorkflowState, wf_id: str) -> tuple[WorkflowState, bool]:
    kept = [w for w in state.workflows if w.id != wf_id]
    return state.model_copy(update={"workflows": kept}), len(kept) < len(state.workflows)


def install_template(state: WorkflowState, template_id: str) -> tuple[WorkflowState, WorkflowDefinition | None]:
    now = utc_now()
    tpl = next((t for t in starter_templates(now) if t.id == template_id), None)
    if tpl is None:
        return state, None
    installed = tpl.model_copy(update={"id": new_id("wf"), "created_at": now, "updated_at": now})
    return state.model_copy(update={"workflows": [installed, *state.workflows]}), installed


def record_run(state: WorkflowState, run: WorkflowRun) -> WorkflowState:
    runs = [run, *[r for r in state.runs if r.run_id != run.run_id]][:MAX_RUN_HISTORY]
    return state.model_copy(update={"runs": runs})
