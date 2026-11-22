"""Strict Pydantic v2 contracts for Time Tracking, Impact Documentation, ROI, and Superfocus."""

from typing import Literal

from pydantic import Field

from core.contracts import StrictModel

TimeSource = Literal["timer", "focus", "manual"]
OutcomeTag = Literal["quality", "time_saved", "revenue", "wellbeing", "milestone"]
GoalStatus = Literal["active", "achieved", "paused"]
SoundscapeMode = Literal["off", "brown", "rain", "drone"]
_DATE_RE = r"^$|^\d{4}-\d{2}-\d{2}$"


class ActiveTimer(StrictModel):
    label: str = Field(default="Work Session", min_length=1, max_length=180)
    project_id: str = Field(default="", max_length=64)
    task_id: str = Field(default="", max_length=64)
    category: str = Field(default="deep_work", max_length=48)
    hourly_rate: float = Field(default=0.0, ge=0.0, le=10000.0)
    started_at: str = Field(default="", max_length=64)
    accumulated_seconds: int = Field(default=0, ge=0, le=864000)
    is_paused: bool = False


class TimeEntry(StrictModel):
    id: str = Field(..., min_length=1, max_length=64)
    label: str = Field(..., min_length=1, max_length=180)
    project_id: str = Field(default="", max_length=64)
    task_id: str = Field(default="", max_length=64)
    category: str = Field(default="deep_work", max_length=48)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    duration_minutes: float = Field(..., gt=0.0, le=1440.0)
    hourly_rate: float = Field(default=0.0, ge=0.0, le=10000.0)
    billable: bool = True
    source: TimeSource = "manual"
    notes: str = Field(default="", max_length=1200)
    created_at: str = Field(default="", max_length=64)


class ImpactEntry(StrictModel):
    id: str = Field(..., min_length=1, max_length=64)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    project_id: str = Field(default="", max_length=64)
    task_ids: list[str] = Field(default_factory=list, max_length=25)
    what_done: str = Field(..., min_length=1, max_length=1000)
    effect: str = Field(..., min_length=1, max_length=1500)
    evidence_notes: str = Field(default="", max_length=2000)
    hours_invested: float = Field(default=0.0, ge=0.0, le=5000.0)
    direct_cost: float = Field(default=0.0, ge=0.0, le=10_000_000.0)
    estimated_value: float = Field(default=0.0, ge=0.0, le=10_000_000.0)
    time_saved_hours: float = Field(default=0.0, ge=0.0, le=5000.0)
    outcome_tag: OutcomeTag = "quality"
    created_at: str = Field(default="", max_length=64)


class ImpactLedgerState(StrictModel):
    default_hourly_rate: float = Field(default=85.0, ge=0.0, le=10000.0)
    currency: str = Field(default="EUR", min_length=1, max_length=8)
    active_timer: ActiveTimer | None = None
    time_entries: list[TimeEntry] = Field(default_factory=list, max_length=5000)
    impact_entries: list[ImpactEntry] = Field(default_factory=list, max_length=3000)


class GoalSeason(StrictModel):
    id: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=140)
    why: str = Field(default="", max_length=800)
    project_id: str = Field(default="", max_length=64)
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    target_hours: float = Field(default=24.0, gt=0.0, le=2000.0)
    weekly_milestones: list[str] = Field(default_factory=list, max_length=24)
    status: GoalStatus = "active"
    created_at: str = Field(default="", max_length=64)


class FocusSession(StrictModel):
    id: str = Field(..., min_length=1, max_length=64)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    goal_id: str = Field(default="", max_length=64)
    project_id: str = Field(default="", max_length=64)
    task_id: str = Field(default="", max_length=64)
    label: str = Field(..., min_length=1, max_length=180)
    planned_minutes: int = Field(default=45, ge=5, le=240)
    actual_minutes: float = Field(..., gt=0.0, le=480.0)
    quality_rating: int = Field(default=4, ge=1, le=5)
    soundscape: SoundscapeMode = "off"
    reflection: str = Field(default="", max_length=1000)
    completed_at: str = Field(default="", max_length=64)


class PlannedFocusBlock(StrictModel):
    title: str = Field(..., min_length=1, max_length=180)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    start_time: str = Field(default="09:00", pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(default="10:30", pattern=r"^\d{2}:\d{2}$")
    goal_id: str = Field(default="", max_length=64)
    project_id: str = Field(default="", max_length=64)
    notes: str = Field(default="", max_length=600)


class FocusState(StrictModel):
    goals: list[GoalSeason] = Field(default_factory=list, max_length=100)
    sessions: list[FocusSession] = Field(default_factory=list, max_length=5000)
    default_minutes: int = Field(default=45, ge=5, le=180)
    default_soundscape: SoundscapeMode = "brown"
