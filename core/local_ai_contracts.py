"""Pydantic v2 contracts for Built-in Private AI (managed llama-server sidecar)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from core.contracts import StrictModel

LocalAiProfile = Literal["eco", "performance"]
LocalAiTier = Literal["ultra_light", "compact", "balanced", "deep"]
LocalAiPlatformKey = Literal[
    "macos-arm64",
    "macos-x64",
    "win-vulkan-x64",
    "win-vulkan-arm64",
    "linux-vulkan-x64",
    "linux-vulkan-arm64",
]
LocalAiRunState = Literal["not_installed", "downloading", "sleeping", "waking", "ready", "error"]


class LocalAiModelPreset(StrictModel):
    id: str
    tier: LocalAiTier
    label_key: str
    filename: str
    url: str
    sha256: str
    size_bytes: int
    min_ram_gb: int
    supports_reasoning: bool = True
    default_ctx_eco: int = 4096
    default_ctx_perf: int = 8192


class LocalAiRuntimeAsset(StrictModel):
    platform_key: LocalAiPlatformKey
    release_tag: str
    archive_name: str
    url: str
    sha256: str
    size_bytes: int
    binary_name: str


class LocalAiState(StrictModel):
    profile: LocalAiProfile = "eco"
    idle_minutes: int = Field(default=5, ge=1, le=60)
    active_model_id: str = ""
    installed_runtime_tag: str = ""
    force_cpu: bool = False


class LocalAiSetupRequest(StrictModel):
    model_id: str = Field(default="recommended", min_length=1, max_length=64)
    profile: LocalAiProfile | None = None


class LocalAiConfigUpdate(StrictModel):
    profile: LocalAiProfile | None = None
    idle_minutes: int | None = Field(default=None, ge=1, le=60)
    active_model_id: str | None = Field(default=None, max_length=64)
    force_cpu: bool | None = None


class LocalAiPresetView(StrictModel):
    id: str
    tier: LocalAiTier
    label_key: str
    size_gb: float
    min_ram_gb: int
    installed: bool
    recommended: bool


class LocalAiStatusResponse(StrictModel):
    supported: bool
    platform_key: str
    ram_gb: int
    low_ram_warning: bool
    runtime_installed: bool
    installed_models: list[str]
    active_model_id: str
    recommended_model_id: str
    recommended_size_gb: float
    disk_used_mb: int
    free_disk_gb: float
    state: LocalAiRunState
    offline_ready: bool
    gpu_active: bool
    profile: LocalAiProfile
    idle_minutes: int
    ctx_size: int
    threads: int
    force_cpu: bool
    last_error: str
    presets: list[LocalAiPresetView]
