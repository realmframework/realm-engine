"""Strict Pydantic v2 contracts for the integrated local Bottom Panel Terminal."""

from typing import Literal

from pydantic import Field

from core.contracts import StrictModel


class TerminalCreateRequest(StrictModel):
    label: str = Field(default="", max_length=48)
    cols: int = Field(default=100, ge=20, le=400)
    rows: int = Field(default=24, ge=5, le=120)


class TerminalInputRequest(StrictModel):
    data: str = Field(..., min_length=1, max_length=16384)


class TerminalSignalRequest(StrictModel):
    signal: Literal["interrupt", "eof"] = "interrupt"


class TerminalResizeRequest(StrictModel):
    cols: int = Field(default=100, ge=20, le=400)
    rows: int = Field(default=24, ge=5, le=120)


class TerminalSessionInfo(StrictModel):
    id: str
    label: str
    shell: str
    cwd: str
    running: bool
    exit_code: int | None = None
