"""Strict Pydantic v2 request payloads for Impact Ledger API endpoints."""

from typing import Literal

from pydantic import Field

from core.contracts import ProviderName, StrictModel
from core.impact_contracts import OutcomeTag, TimeSource

_DATE_RE = r"^$|^\d{4}-\d{2}-\d{2}$"


class ImpactSettingsBody(StrictModel):
    default_hourly_rate: float = Field(..., ge=0.0, le=10000.0)
    currency: str = Field(default="EUR", min_length=1, max_length=8)


class TimerStartBody(StrictModel):
    label: str = Field(default="Work Session", min_length=1, max_length=180)
    project_id: str = Field(default="", max_length=64)
    task_id: str = Field(default="", max_length=64)
    category: str = Field(default="deep_work", max_length=48)
    hourly_rate: float = Field(default=0.0, ge=0.0, le=10000.0)


class TimerStopBody(StrictModel):
    notes: str = Field(default="", max_length=1200)


class TimeEntryBody(StrictModel):
    label: str = Field(..., min_length=1, max_length=180)
    duration_minutes: float = Field(..., gt=0.0, le=1440.0)
    date: str = Field(default="", pattern=_DATE_RE)
    project_id: str = Field(default="", max_length=64)
    task_id: str = Field(default="", max_length=64)
    category: str = Field(default="deep_work", max_length=48)
    hourly_rate: float = Field(default=0.0, ge=0.0, le=10000.0)
    source: TimeSource = "manual"
    notes: str = Field(default="", max_length=1200)


class ImpactCreateBody(StrictModel):
    date: str = Field(default="", pattern=_DATE_RE)
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


class ImpactPatchBody(StrictModel):
    date: str | None = Field(default=None, pattern=_DATE_RE)
    project_id: str | None = Field(default=None, max_length=64)
    what_done: str | None = Field(default=None, min_length=1, max_length=1000)
    effect: str | None = Field(default=None, min_length=1, max_length=1500)
    evidence_notes: str | None = Field(default=None, max_length=2000)
    hours_invested: float | None = Field(default=None, ge=0.0, le=5000.0)
    direct_cost: float | None = Field(default=None, ge=0.0, le=10_000_000.0)
    estimated_value: float | None = Field(default=None, ge=0.0, le=10_000_000.0)
    time_saved_hours: float | None = Field(default=None, ge=0.0, le=5000.0)
    outcome_tag: OutcomeTag | None = None


class ImpactDraftBody(StrictModel):
    notes: str = Field(default="", max_length=10000)
    hours: float = Field(default=0.0, ge=0.0, le=5000.0)
    use_ai: bool = True
    provider: ProviderName = "ollama"
    model: str = Field(default="", max_length=120)
    language: str = Field(default="en", max_length=12)


class ImpactReportBody(StrictModel):
    format: Literal["pdf", "pptx"] = "pdf"
    title: str = Field(default="", max_length=160)
