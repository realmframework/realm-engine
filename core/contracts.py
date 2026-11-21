"""Shared Pydantic v2 data contracts for the AI Engineering Knowledge Engine."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ProviderName = Literal["ollama", "openai", "kimi", "deepseek", "gemini", "anthropic", "xai", "mistral"]
RetrievalMode = Literal["hybrid", "lexical", "vector"]
ReasoningEffort = Literal["low", "medium", "high", "max"]
class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True)
class KnowledgeChunk(StrictModel):
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
class SearchQuery(StrictModel):
    subfolder: str | None = None
    doc_id: str | None = None
    query: str = Field(default="")
    top_k: int = Field(default=5, ge=1, le=15)
    tag_filter: str | None = None
    retrieval_mode: RetrievalMode = "hybrid"
    rrf_k: int = Field(default=60, ge=1, le=120)
class SearchResult(StrictModel):
    chunk: KnowledgeChunk
    score: float
class TutorResponse(StrictModel):
    answer: str
    cited_titles: list[str]
    knowledge_gap_detected: bool
    recommended_topics: list[str]
class BudgetLimits(StrictModel):
    daily_cloud_request_limit: int = Field(default=50, ge=0, le=100_000)
    daily_budget_usd_limit: float = Field(default=1.0, ge=0, allow_inf_nan=False)
class TutorConfig(BudgetLimits):
    provider: ProviderName = "ollama"
    model: str = "qwen3:8b"
    api_key: str | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    reasoning_effort: ReasoningEffort | None = None
    response_language: Literal["en", "de", "es"] = "en"
class AppearanceUpdate(StrictModel):
    theme_mode: Literal["system", "dark", "light"] = "system"
    theme_accent: str = Field(default="#4BB8E8", pattern=r"^#[0-9A-Fa-f]{6}$")
    theme_glow: str = Field(default="#6366F1", pattern=r"^#[0-9A-Fa-f]{6}$")
    ambient_effects: bool = True
    agent_name: str = Field(default="Saga", min_length=1, max_length=40)
    active_agent: str = Field(default="saga", min_length=1, max_length=64)
    sync_agent_palette: bool = True
    language: Literal["en", "de", "es"] = "en"
    web_search_enabled: bool = False
    web_search_provider: Literal["duckduckgo", "ollama", "searxng"] = "duckduckgo"
    searxng_url: str = Field(default="", max_length=255)
    reading_font: Literal["default", "legible", "dyslexic"] = "default"
    reading_scale: Literal["sm", "md", "lg", "xl"] = "md"
    reading_width: Literal["narrow", "standard", "wide"] = "standard"
    high_contrast_focus: bool = False
    reduce_motion: bool = False
    eco_mode: bool = False
    enable_local_api: bool = False
class WorkspaceConfig(BudgetLimits, AppearanceUpdate):
    app_title: str = "My Knowledge Base"
    hero_greeting: str = "Where should we start?"
    search_placeholder: str = "Ask or search guides..."
    knowledge_dir: str = "knowledge_base"
    active_dirs: list[str] = Field(default_factory=lambda: ["knowledge_base"])
    anonymize_uploads: bool = True
    strict_local_only: bool = True
    run_mode: Literal["local", "cloud", "search"] = "local"
    excluded_subfolders: dict[str, list[str]] = Field(default_factory=dict)
    @model_validator(mode="after")
    def synchronize_areas(self) -> "WorkspaceConfig":
        raw = self.active_dirs if "active_dirs" in self.model_fields_set else ([self.knowledge_dir] if self.knowledge_dir else [])
        self.active_dirs, self.knowledge_dir = (vals := list(dict.fromkeys(d for d in raw if d))), (vals[0] if vals else "")
        return self
class ChatTurnBase(SearchQuery):
    query: str = Field(...)
    tag: str | None = None
    ask_tutor: bool = True
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
class ChatTurnRequest(ChatTurnBase):
    use_web_search: bool = False
    free_chat: bool = False
    format_id: str | None = None
    agent_id: str | None = None
    instruction_prefix: str = Field(default="", max_length=4000)
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None
    muted_doc_ids: list[str] = Field(default_factory=list)
    pinned_doc_ids: list[str] = Field(default_factory=list)
class ChatTurn(ChatTurnBase):
    tutor: TutorResponse | None = None
    results: list[SearchResult] = Field(default_factory=list)
    created_at: str
    thinking: str = ""
    telemetry: dict[str, object] = Field(default_factory=dict)
    format_name: str = ""
    agent_id: str = ""
    agent_name: str = ""
class ChatSession(StrictModel):
    chat_id: str
    title: str
    updated_at: str
    turns: list[ChatTurn] = Field(default_factory=list)
    area: str = "knowledge_base"
    active_dirs: list[str] = Field(default_factory=list)
    subfolder: str | None = None
    doc_id: str | None = None
    compacted_summary: str = ""
    context_cleared_at: int = 0
    free_chat: bool = False
    last_agent_id: str = ""
    attached_notes: list[dict[str, str]] = Field(default_factory=list)
class AnonymizationPreview(StrictModel):
    text: str | None = Field(default=None, max_length=1_000_000)
    filename: str = Field(default="", max_length=255)
    doc_id: str | None = None
class AnonymizationReport(StrictModel):
    scrubbed_text: str
    total_redacted: int
    counts_by_type: dict[str, int]
    samples: list[dict[str, str]]
class KnowledgeArea(StrictModel):
    name: str
    doc_count: int
    color: str
    can_delete: bool
    linked: bool = False
    linked_path: str = ""
    display_name: str = ""
class PublicHistoryTurn(StrictModel):
    query: str = Field(..., min_length=1, max_length=500)
    answer: str = Field(default="", max_length=1500)
class PublicAskRequest(StrictModel):
    query: str = Field(..., min_length=1, max_length=500)
    area: str | None = None
    areas: list[str] | None = None
    tag: str | None = None
    doc_id: str | None = None
    subfolder: str | None = None
    top_k: int = Field(default=5, ge=1, le=8)
    history: list[PublicHistoryTurn] = Field(default_factory=list, max_length=3)
