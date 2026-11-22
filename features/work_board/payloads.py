"""Strict Pydantic v2 request payloads for Work Board API endpoints."""

from pydantic import Field

from core.contracts import ProviderName, StrictModel
from core.work_contracts import (
    EventKind,
    PriorityLevel,
    ProjectStatus,
    RecurrenceRule,
    TaskSubitem,
)

_DATE_RE = r"^$|^\d{4}-\d{2}-\d{2}$"
_TIME_RE = r"^$|^\d{2}:\d{2}$"
_HEX_RE = r"^#[0-9A-Fa-f]{6}$"


class ProjectCreateBody(StrictModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)
    color: str = Field(default="#4BB8E8", pattern=_HEX_RE)
    status: ProjectStatus = "active"
    target_date: str = Field(default="", pattern=_DATE_RE)
    target_hours: float = Field(default=0.0, ge=0.0, le=10000.0)


class ProjectPatchBody(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    color: str | None = Field(default=None, pattern=_HEX_RE)
    status: ProjectStatus | None = None
    target_date: str | None = Field(default=None, pattern=_DATE_RE)
    target_hours: float | None = Field(default=None, ge=0.0, le=10000.0)


class ColumnCreateBody(StrictModel):
    title: str = Field(..., min_length=1, max_length=60)
    color: str = Field(default="#4BB8E8", pattern=_HEX_RE)
    is_done: bool = False


class ColumnPatchBody(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=60)
    color: str | None = Field(default=None, pattern=_HEX_RE)
    is_done: bool | None = None


class TaskCreateBody(StrictModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    column_id: str = Field(default="", max_length=64)
    project_id: str = Field(default="", max_length=64)
    priority: PriorityLevel = "medium"
    due_date: str = Field(default="", pattern=_DATE_RE)
    scheduled_start: str = Field(default="", pattern=_TIME_RE)
    scheduled_end: str = Field(default="", pattern=_TIME_RE)
    recurrence: RecurrenceRule = "none"
    subtasks: list[TaskSubitem] = Field(default_factory=list, max_length=50)
    tags: list[str] = Field(default_factory=list, max_length=16)
    linked_doc_id: str = Field(default="", max_length=260)
    linked_chat_id: str = Field(default="", max_length=120)


class TaskPatchBody(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    column_id: str | None = Field(default=None, min_length=1, max_length=64)
    project_id: str | None = Field(default=None, max_length=64)
    priority: PriorityLevel | None = None
    due_date: str | None = Field(default=None, pattern=_DATE_RE)
    scheduled_start: str | None = Field(default=None, pattern=_TIME_RE)
    scheduled_end: str | None = Field(default=None, pattern=_TIME_RE)
    recurrence: RecurrenceRule | None = None
    subtasks: list[TaskSubitem] | None = Field(default=None, max_length=50)
    tags: list[str] | None = Field(default=None, max_length=16)
    linked_doc_id: str | None = Field(default=None, max_length=260)
    linked_chat_id: str | None = Field(default=None, max_length=120)


class TaskReorderBody(StrictModel):
    task_id: str = Field(..., min_length=1, max_length=64)
    target_column_id: str = Field(..., min_length=1, max_length=64)
    target_index: int = Field(default=0, ge=0, le=5000)


class EventCreateBody(StrictModel):
    title: str = Field(..., min_length=1, max_length=200)
    notes: str = Field(default="", max_length=2000)
    kind: EventKind = "event"
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    start_time: str = Field(default="", pattern=_TIME_RE)
    end_time: str = Field(default="", pattern=_TIME_RE)
    project_id: str = Field(default="", max_length=64)
    task_id: str = Field(default="", max_length=64)


class EventPatchBody(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)
    kind: EventKind | None = None
    date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    start_time: str | None = Field(default=None, pattern=_TIME_RE)
    end_time: str | None = Field(default=None, pattern=_TIME_RE)
    project_id: str | None = Field(default=None, max_length=64)
    task_id: str | None = Field(default=None, max_length=64)


class ExtractTasksBody(StrictModel):
    chat_id: str = Field(default="", max_length=120)
    turn_index: int | None = Field(default=None, ge=0, le=500)
    doc_id: str = Field(default="", max_length=260)
    text: str = Field(default="", max_length=40000)
    project_id: str = Field(default="", max_length=64)
    column_id: str = Field(default="", max_length=64)
    use_ai: bool = True
    save: bool = True
    provider: ProviderName = "ollama"
    model: str = Field(default="", max_length=120)
    language: str = Field(default="en", max_length=12)


class ImportIcsBody(StrictModel):
    ics_text: str = Field(..., min_length=1, max_length=2_000_000)
