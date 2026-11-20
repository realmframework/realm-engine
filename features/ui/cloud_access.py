"""Inject budget admission into UI composition without importing other feature slices."""

from collections.abc import Callable

from fastapi import HTTPException

from core.contracts import WorkspaceConfig
from features.ui.privacy import require_local


def build_guard(config: Callable[[], WorkspaceConfig], record: Callable[..., str | None], estimate: Callable[..., tuple[int, float]]) -> Callable[[str, str, str], None]:
    def guard(provider: str, text: str, kind: str = "embedding") -> None:
        active = config()
        require_local(active, provider)
        if provider == "ollama":
            return
        tokens, cost = estimate(text, output_tokens=0, kind=provider + "_speech" if kind == "speech" else kind)
        denied = record(provider, tokens, active.daily_cloud_request_limit, active.daily_budget_usd_limit, cost)
        if denied:
            raise HTTPException(status_code=429, detail=denied)
    return guard


def build_embedder(embed: Callable[..., list[float]], guard: Callable[[str, str, str], None]) -> Callable[..., list[float]]:
    def guarded(text: str, provider: str = "ollama", api_key: str | None = None) -> list[float]:
        if provider in {"openai", "mistral"}:
            guard(provider, text, "embedding")
        return embed(text, provider=provider, api_key=api_key)
    return guarded
