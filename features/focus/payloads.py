"""Strict Pydantic v2 request payloads for Goal Seasons, Deep Focus, and AI Weekly Planner."""

from pydantic import Field

from core.contracts import ProviderName, StrictModel
from core.impact_contracts import GoalStatus, PlannedFocusBlock, SoundscapeMode

_DATE_RE = r"^$|^\d{4}-\d{2}-\d{2}$"


class GoalCreateBody(StrictModel):
    title: str = Field(..., min_length=1, max_length=140)
    why: str = Field(default="", max_length=800)
    project_id: str = Field(default="", max_length=64)
    start_date: str = Field(default="", pattern=_DATE_RE)
    end_date: str = Field(default="", pattern=_DATE_RE)
    target_hours: float = Field(default=24.0, gt=0.0, le=2000.0)
    weekly_milestones: list[str] = Field(default_factory=list, max_length=24)
    status: GoalStatus = "active"


class GoalPatchBody(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=140)
    why: str | None = Field(default=None, max_length=800)
    project_id: str | None = Field(default=None, max_length=64)
    start_date: str | None = Field(default=None, pattern=_DATE_RE)
    end_date: str | None = Field(default=None, pattern=_DATE_RE)
    target_hours: float | None = Field(default=None, gt=0.0, le=2000.0)
    weekly_milestones: list[str] | None = Field(default=None, max_length=24)
    status: GoalStatus | None = None


class FocusSessionBody(StrictModel):
    label: str = Field(..., min_length=1, max_length=180)
    planned_minutes: int = Field(default=45, ge=5, le=240)
    actual_minutes: float = Field(..., gt=0.0, le=480.0)
    quality_rating: int = Field(default=4, ge=1, le=5)
    soundscape: SoundscapeMode = "off"
    reflection: str = Field(default="", max_length=1000)
    goal_id: str = Field(default="", max_length=64)
    project_id: str = Field(default="", max_length=64)
    task_id: str = Field(default="", max_length=64)
    date: str = Field(default="", pattern=_DATE_RE)
    log_time: bool = True


class WeeklyPlanBody(StrictModel):
    use_ai: bool = True
    provider: ProviderName = "ollama"
    model: str = Field(default="", max_length=120)
    language: str = Field(default="en", max_length=12)


class AcceptPlanBody(StrictModel):
    blocks: list[PlannedFocusBlock] = Field(..., min_length=1, max_length=14)
