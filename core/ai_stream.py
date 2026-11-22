"""Shared local-privacy admission, workspace TutorConfig builder, and LLM stream text collector."""

from __future__ import annotations

import asyncio
import os
import re
from collections.abc import AsyncIterator, Callable

from fastapi import HTTPException

from core.contracts import ProviderName, TutorConfig, WorkspaceConfig
from core.runtime import is_loopback_url, ollama_base_url

StreamMessagesFn = Callable[..., AsyncIterator[dict[str, object]]]
_SAFE_FILENAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def is_local_policy_satisfied(
    config: WorkspaceConfig,
    provider: str | None,
    model: str | None = None,
) -> bool:
    """Return True when the provider/model/Ollama host satisfies workspace strict_local_only."""
    if not config.strict_local_only:
        return True
    if (provider or "ollama") != "ollama" or "cloud" in (model or "").lower():
        return False
    return is_loopback_url(ollama_base_url()) or os.environ.get("REALM_ALLOW_REMOTE_OLLAMA", "").strip() == "1"


def require_local_policy(
    config: WorkspaceConfig,
    provider: str | None,
    model: str | None = None,
) -> None:
    """Enforce workspace strict_local_only privacy lock, raising HTTP 403 on violation."""
    if not config.strict_local_only:
        return
    if (provider or "ollama") != "ollama" or "cloud" in (model or "").lower():
        raise HTTPException(
            status_code=403,
            detail="Strict Local-Only Lock is active. Use a local Ollama model or disable the lock in Settings.",
        )
    if not is_loopback_url(ollama_base_url()) and os.environ.get("REALM_ALLOW_REMOTE_OLLAMA", "").strip() != "1":
        raise HTTPException(
            status_code=403,
            detail="Strict Local-Only Lock blocks non-loopback OLLAMA_HOST targets. Set REALM_ALLOW_REMOTE_OLLAMA=1 to override.",
        )


def build_workspace_tutor_config(
    cfg: WorkspaceConfig,
    provider: ProviderName,
    model: str,
    api_key: str | None = None,
    *,
    temperature: float = 0.2,
) -> TutorConfig:
    """Build a TutorConfig that inherits workspace cloud budget caps and privacy limits."""
    return TutorConfig(
        provider=provider,
        model=model,
        api_key=(api_key or "").strip() or None,
        temperature=temperature,
        daily_cloud_request_limit=cfg.daily_cloud_request_limit,
        daily_budget_usd_limit=cfg.daily_budget_usd_limit,
    )


async def collect_stream_text(
    stream_messages: StreamMessagesFn,
    messages: list[dict[str, str]],
    tutor_config: TutorConfig,
    *,
    cancel_check: Callable[[], bool] | None = None,
    max_tokens: int = 2048,
) -> str:
    """Collect assistant text from stream_messages_events using the canonical type='token'/delta contract."""
    chunks: list[str] = []
    async for ev in stream_messages(messages, tutor_config, max_tokens=max_tokens):
        if cancel_check is not None and cancel_check():
            raise asyncio.CancelledError("Stream cancelled")
        if ev.get("type") == "token" and isinstance(ev.get("delta"), str):
            chunks.append(str(ev["delta"]))
    return "".join(chunks)


def safe_download_filename(raw: str, fallback: str = "realm") -> str:
    """Sanitize a filename segment for safe Content-Disposition headers."""
    cleaned = _SAFE_FILENAME_RE.sub("_", (raw or "").strip()).strip("._-")[:64]
    return cleaned or fallback
