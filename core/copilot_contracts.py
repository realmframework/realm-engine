"""Strict Pydantic v2 contracts for the Right Sidebar Context-Aware REALM Copilot."""

from typing import Literal

from pydantic import Field

from core.contracts import ProviderName, StrictModel

CopilotViewKind = Literal["file", "work", "focus", "impact", "workflows", "library", "chat", "graph"]
CopilotActionKind = Literal[
    "update_document",
    "create_note",
    "create_task",
    "update_task",
    "create_event",
    "create_goal",
    "upsert_agent",
    "upsert_workflow",
]


class CopilotMessage(StrictModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=12000)


class CopilotAttachedFile(StrictModel):
    doc_id: str = Field(..., min_length=1, max_length=260)
    filename: str = Field(..., min_length=1, max_length=200)
    content: str = Field(default="", max_length=12000)


class CopilotContext(StrictModel):
    view: CopilotViewKind = "chat"
    doc_id: str = Field(default="", max_length=260)
    filename: str = Field(default="", max_length=200)
    doc_content: str = Field(default="", max_length=24000)
    doc_readonly: bool = False
    selected_text: str = Field(default="", max_length=6000)
    extra_files: list[CopilotAttachedFile] = Field(default_factory=list, max_length=4)
    work_summary: str = Field(default="", max_length=6000)
    workflow_summary: str = Field(default="", max_length=6000)
    agents_summary: str = Field(default="", max_length=4000)


class CopilotChatRequest(StrictModel):
    messages: list[CopilotMessage] = Field(..., min_length=1, max_length=24)
    context: CopilotContext = Field(default_factory=CopilotContext)
    provider: ProviderName = "ollama"
    model: str | None = None
    api_key: str | None = None
    agent_id: str = Field(default="saga", max_length=64)
    format_id: str | None = Field(default=None, max_length=64)


class CopilotActionProposal(StrictModel):
    id: str = Field(..., min_length=1, max_length=48)
    kind: CopilotActionKind
    title: str = Field(..., min_length=1, max_length=160)
    summary: str = Field(default="", max_length=400)
    payload: dict[str, object] = Field(default_factory=dict)
    diff_before: str = Field(default="", max_length=4000)
    diff_after: str = Field(default="", max_length=4000)
