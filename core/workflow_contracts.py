"""Strict Pydantic v2 contracts for Native Local Workflow & Agent Pipelines (Milestone 5)."""

from typing import Literal

from pydantic import Field

from core.contracts import ProviderName, StrictModel

TriggerKind = Literal["manual", "schedule", "file_imported", "task_done"]
NodeKind = Literal[
    "trigger",
    "vault_search",
    "run_agent",
    "condition",
    "extract_tasks",
    "generate_slides",
    "save_guide",
    "log_impact",
]
EdgeBranch = Literal["default", "true", "false"]
StepStatus = Literal["completed", "skipped", "failed", "cancelled"]
RunStatus = Literal["running", "completed", "cancelled", "failed"]

_ID_RE = r"^[a-zA-Z0-9_-]{1,64}$"


class WorkflowNode(StrictModel):
    id: str = Field(..., pattern=_ID_RE)
    kind: NodeKind
    label: str = Field(..., min_length=1, max_length=120)
    x: float = Field(default=40.0, ge=0.0, le=4000.0)
    y: float = Field(default=60.0, ge=0.0, le=4000.0)
    config: dict[str, str | int | float | bool] = Field(default_factory=dict)


class WorkflowEdge(StrictModel):
    id: str = Field(..., pattern=_ID_RE)
    source: str = Field(..., pattern=_ID_RE)
    target: str = Field(..., pattern=_ID_RE)
    branch: EdgeBranch = "default"


class WorkflowDefinition(StrictModel):
    id: str = Field(..., pattern=_ID_RE)
    name: str = Field(..., min_length=1, max_length=140)
    description: str = Field(default="", max_length=600)
    enabled: bool = True
    trigger_kind: TriggerKind = "manual"
    schedule_minutes: int = Field(default=0, ge=0, le=10080)
    nodes: list[WorkflowNode] = Field(default_factory=list, max_length=40)
    edges: list[WorkflowEdge] = Field(default_factory=list, max_length=80)
    created_at: str = Field(..., min_length=1, max_length=64)
    updated_at: str = Field(..., min_length=1, max_length=64)


class WorkflowStepResult(StrictModel):
    node_id: str = Field(..., min_length=1, max_length=64)
    label: str = Field(..., min_length=1, max_length=120)
    kind: NodeKind
    status: StepStatus
    output_preview: str = Field(default="", max_length=1200)
    artifact_note: str = Field(default="", max_length=300)
    duration_ms: int = Field(default=0, ge=0)


class WorkflowRun(StrictModel):
    run_id: str = Field(..., min_length=1, max_length=64)
    workflow_id: str = Field(..., min_length=1, max_length=64)
    workflow_name: str = Field(..., min_length=1, max_length=140)
    trigger_source: str = Field(default="manual", max_length=40)
    status: RunStatus
    started_at: str = Field(..., min_length=1, max_length=64)
    finished_at: str = Field(default="", max_length=64)
    steps: list[WorkflowStepResult] = Field(default_factory=list, max_length=60)
    error: str = Field(default="", max_length=600)


class WorkflowState(StrictModel):
    workflows: list[WorkflowDefinition] = Field(default_factory=list, max_length=60)
    runs: list[WorkflowRun] = Field(default_factory=list, max_length=60)


class WorkflowCreateBody(StrictModel):
    name: str = Field(..., min_length=1, max_length=140)
    description: str = Field(default="", max_length=600)
    enabled: bool = True
    trigger_kind: TriggerKind = "manual"
    schedule_minutes: int = Field(default=0, ge=0, le=10080)
    nodes: list[WorkflowNode] = Field(default_factory=list, max_length=40)
    edges: list[WorkflowEdge] = Field(default_factory=list, max_length=80)


class WorkflowPatchBody(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=140)
    description: str | None = Field(default=None, max_length=600)
    enabled: bool | None = None
    trigger_kind: TriggerKind | None = None
    schedule_minutes: int | None = Field(default=None, ge=0, le=10080)
    nodes: list[WorkflowNode] | None = Field(default=None, max_length=40)
    edges: list[WorkflowEdge] | None = Field(default=None, max_length=80)


class WorkflowRunBody(StrictModel):
    input_text: str = Field(default="", max_length=8000)
    provider: ProviderName = "ollama"
    model: str = Field(default="qwen3:8b", min_length=1, max_length=120)
    trigger_source: str = Field(default="manual", max_length=40)
