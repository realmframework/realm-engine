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
