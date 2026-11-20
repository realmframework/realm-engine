"""Shared Pydantic v2 data contracts for the AI Engineering Knowledge Engine."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ProviderName = Literal["ollama", "openai", "kimi", "deepseek", "gemini", "anthropic", "xai", "mistral"]
RetrievalMode = Literal["hybrid", "lexical", "vector"]
ReasoningEffort = Literal["low", "medium", "high", "max"]


class KnowledgeChunk(BaseModel):
    model_config = ConfigDict(strict=True)
    id: str
    title: str
    file_path: str
    area: str = ""
    doc_id: str = ""
    subfolder: str = ""
    content: str
    tags: list[str]
    embedding: list[float] | None = None
    url: str = ""
    description: str = ""

class SearchQuery(BaseModel):
    model_config = ConfigDict(strict=True)
    subfolder: str | None = None
    doc_id: str | None = None
    query: str = Field(default="")
    top_k: int = Field(default=5, ge=1, le=15)
    tag_filter: str | None = None
    retrieval_mode: RetrievalMode = "hybrid"
    rrf_k: int = Field(default=60, ge=1, le=120)

class SearchResult(BaseModel):
    model_config = ConfigDict(strict=True)
    chunk: KnowledgeChunk
    score: float

class TutorResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    answer: str
    cited_titles: list[str]
    knowledge_gap_detected: bool
    recommended_topics: list[str]

class BudgetLimits(BaseModel):
    model_config = ConfigDict(strict=True)
    daily_cloud_request_limit: int = Field(default=50, ge=0, le=100_000)
    daily_budget_usd_limit: float = Field(default=1.0, ge=0, allow_inf_nan=False)

class TutorConfig(BudgetLimits):
    provider: ProviderName = "ollama"
    model: str = "qwen3:8b"
    api_key: str | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    reasoning_effort: ReasoningEffort | None = None

class WorkspaceConfig(BudgetLimits):
    app_title: str = "AI Engineering"
    hero_greeting: str = "Where should we start?"
    search_placeholder: str = "Ask or search guides..."
    knowledge_dir: str = "knowledge_base"
    active_dirs: list[str] = Field(default_factory=lambda: ["knowledge_base"], min_length=1)
    anonymize_uploads: bool = True
    strict_local_only: bool = True
    run_mode: Literal["local", "cloud", "search"] = "local"

    @model_validator(mode="after")
    def synchronize_areas(self) -> "WorkspaceConfig":
        self.active_dirs = list(dict.fromkeys(self.active_dirs if "active_dirs" in self.model_fields_set else [self.knowledge_dir]))
        self.knowledge_dir = self.active_dirs[0]
        return self

class ChatTurnRequest(SearchQuery):
    model_config = ConfigDict(strict=True)
    query: str = Field(...)
    tag: str | None = None
    ask_tutor: bool = True
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)

class ChatTurn(SearchQuery):
    model_config = ConfigDict(strict=True)
    query: str = Field(...)
    tag: str | None = None
    ask_tutor: bool = True
    tutor: TutorResponse | None = None
    results: list[SearchResult] = Field(default_factory=list)
    created_at: str
    temperature: float = 0.2

class ChatSession(BaseModel):
    model_config = ConfigDict(strict=True)
    chat_id: str
    title: str
    updated_at: str
    turns: list[ChatTurn] = Field(default_factory=list)
    area: str = "knowledge_base"
    active_dirs: list[str] = Field(default_factory=list)
    subfolder: str | None = None
    doc_id: str | None = None

class AnonymizationPreview(BaseModel):
    model_config = ConfigDict(strict=True)
    text: str | None = Field(default=None, max_length=1_000_000)
    filename: str = Field(default="", max_length=255)
    doc_id: str | None = None

class AnonymizationReport(BaseModel):
    model_config = ConfigDict(strict=True)
    scrubbed_text: str
    total_redacted: int
    counts_by_type: dict[str, int]
    samples: list[dict[str, str]]

class KnowledgeArea(BaseModel):
    model_config = ConfigDict(strict=True)
    name: str
    doc_count: int
    color: str
    can_delete: bool

class PublicHistoryTurn(BaseModel):
    model_config = ConfigDict(strict=True)
    query: str = Field(..., min_length=1, max_length=500)
    answer: str = Field(default="", max_length=1500)

class PublicAskRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    query: str = Field(..., min_length=1, max_length=500)
    area: str | None = None
    areas: list[str] | None = None
    tag: str | None = None
    doc_id: str | None = None
    subfolder: str | None = None
    top_k: int = Field(default=5, ge=1, le=8)
    history: list[PublicHistoryTurn] = Field(default_factory=list, max_length=3)
