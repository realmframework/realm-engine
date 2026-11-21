"""Strict Pydantic v2 contracts for Solo Work OS features (Slides, Agent Builder, Board, Impact, Workflows)."""

from typing import Literal

from pydantic import Field

from core.contracts import StrictModel


class SlideItem(StrictModel):
    title: str = Field(..., min_length=1, max_length=180)
    bullets: list[str] = Field(default_factory=list, max_length=12)
    table_rows: list[list[str]] = Field(default_factory=list, max_length=16)
    speaker_notes: str = Field(default="", max_length=2000)
    is_title_slide: bool = False


class DeckSpec(StrictModel):
    title: str = Field(..., min_length=1, max_length=180)
    subtitle: str = Field(default="", max_length=220)
    accent_hex: str = Field(default="#4BB8E8", pattern=r"^#[0-9A-Fa-f]{6}$")
    glow_hex: str = Field(default="#6366F1", pattern=r"^#[0-9A-Fa-f]{6}$")
    slides: list[SlideItem] = Field(..., min_length=1, max_length=60)


class AgentBuilderMessage(StrictModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)


class AgentDraft(StrictModel):
    name: str = Field(..., min_length=1, max_length=40)
    role: str = Field(default="Specialist", max_length=64)
    tagline: str = Field(default="", max_length=160)
    palette: str = Field(default="realm", max_length=32)
    default_format: str = Field(default="", max_length=64)
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    instructions: str = Field(default="", max_length=3000)


PriorityLevel = Literal["low", "medium", "high", "urgent"]
RecurrenceRule = Literal["none", "daily", "weekly", "monthly"]
ProjectStatus = Literal["active", "on_hold", "completed"]
EventKind = Literal["event", "focus", "milestone", "deadline"]
_DATE_RE = r"^$|^\d{4}-\d{2}-\d{2}$"
_TIME_RE = r"^$|^\d{2}:\d{2}$"
_HEX_RE = r"^#[0-9A-Fa-f]{6}$"


class BoardColumn(StrictModel):
    id: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=60)
    color: str = Field(default="#4BB8E8", pattern=_HEX_RE)
    is_done: bool = False


class TaskSubitem(StrictModel):
    id: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=180)
    done: bool = False


class WorkProject(StrictModel):
    id: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)
    color: str = Field(default="#4BB8E8", pattern=_HEX_RE)
    status: ProjectStatus = "active"
    target_date: str = Field(default="", pattern=_DATE_RE)
    target_hours: float = Field(default=0.0, ge=0.0, le=10000.0)
    created_at: str = Field(default="", max_length=64)


class WorkTask(StrictModel):
    id: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    column_id: str = Field(default="todo", min_length=1, max_length=64)
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
    position: int = Field(default=0, ge=0)
    completed_at: str = Field(default="", max_length=64)
    created_at: str = Field(default="", max_length=64)
    updated_at: str = Field(default="", max_length=64)


class CalendarEvent(StrictModel):
    id: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=200)
    notes: str = Field(default="", max_length=2000)
    kind: EventKind = "event"
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    start_time: str = Field(default="", pattern=_TIME_RE)
    end_time: str = Field(default="", pattern=_TIME_RE)
    project_id: str = Field(default="", max_length=64)
    task_id: str = Field(default="", max_length=64)
    uid: str = Field(default="", max_length=180)


class WorkBoardState(StrictModel):
    columns: list[BoardColumn] = Field(default_factory=list, max_length=12)
    projects: list[WorkProject] = Field(default_factory=list, max_length=100)
    tasks: list[WorkTask] = Field(default_factory=list, max_length=2000)
    events: list[CalendarEvent] = Field(default_factory=list, max_length=2000)
