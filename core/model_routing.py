"""Per-agent model routing, Local-Only Lock enforcement, Ollama OOM gate, and context fitting."""

import asyncio
import os
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from threading import Lock, Semaphore

import httpx
from fastapi import HTTPException

from core.agent_presets import AgentPersona
from core.cancellation import check_cancelled
from core.context_meter import approx_tokens, model_context_window
from core.contracts import WorkspaceConfig
from core.runtime import is_loopback_url, ollama_base_url
from core.secrets import get_api_key

OLLAMA_CHAT_URL = f"{ollama_base_url()}/api/chat"
DEFAULT_LOCAL_MODEL = "qwen3:8b"
_ORIG_HTTPX_POST = httpx.post
_OLLAMA_LOCK = Lock()
_OLLAMA_EXEC_GATE = Semaphore(1)
_LAST_OLLAMA_MODEL = ""


def _is_cloud_target(provider: str, model: str) -> bool:
    return provider != "ollama" or "cloud" in (model or "").lower()

def _post_unload(model_name: str) -> None:
    try:
        url = OLLAMA_CHAT_URL if httpx.post is not _ORIG_HTTPX_POST else f"{ollama_base_url()}/api/chat"
        if httpx.post is _ORIG_HTTPX_POST:
            with httpx.Client(trust_env=not is_loopback_url(url), follow_redirects=False, timeout=5.0) as client:
                client.post(url, json={"model": model_name, "keep_alive": 0})
        else:
            httpx.post(url, json={"model": model_name, "keep_alive": 0}, timeout=5.0)
    except httpx.HTTPError:
        pass


def maybe_unload_previous_ollama(next_provider: str, next_model: str, *, unload_on_cloud: bool = False) -> str | None:
    """Ask Ollama to unload the previously active local model before switching models."""
    global _LAST_OLLAMA_MODEL
    if next_provider != "ollama":
        if not unload_on_cloud:
            return None
        with _OLLAMA_LOCK:
            prev, _LAST_OLLAMA_MODEL = _LAST_OLLAMA_MODEL, ""
        if prev:
            _post_unload(prev)
        return prev or None
    target = (next_model or "").strip() or DEFAULT_LOCAL_MODEL
    with _OLLAMA_LOCK:
        prev = _LAST_OLLAMA_MODEL if (_LAST_OLLAMA_MODEL and _LAST_OLLAMA_MODEL != target) else ""
        _LAST_OLLAMA_MODEL = target
    if prev:
        _post_unload(prev)
    return prev or None


@contextmanager
def ollama_slot(provider: str, model: str = "") -> Iterator[None]:
    if provider != "ollama":
        maybe_unload_previous_ollama(provider, model, unload_on_cloud=True)
        yield
        return
    while not _OLLAMA_EXEC_GATE.acquire(timeout=0.15):
        check_cancelled()
    try:
        maybe_unload_previous_ollama("ollama", model)
        yield
    finally:
        _OLLAMA_EXEC_GATE.release()
@asynccontextmanager
async def async_ollama_slot(provider: str, model: str = "") -> AsyncIterator[None]:
    if provider != "ollama":
        await asyncio.to_thread(maybe_unload_previous_ollama, provider, model, unload_on_cloud=True)
        yield
        return
    while not _OLLAMA_EXEC_GATE.acquire(blocking=False):
        check_cancelled()
        await asyncio.sleep(0.1)
    try:
        await asyncio.to_thread(maybe_unload_previous_ollama, "ollama", model)
        yield
    finally:
        _OLLAMA_EXEC_GATE.release()


def _enforce_local_only(cfg: WorkspaceConfig, provider: str, model: str, agent_name: str, is_pinned: bool) -> None:
    if not cfg.strict_local_only:
        return
    if _is_cloud_target(provider, model):
        label = f"{provider}/{model}" if model else provider
        detail = (
            f"{agent_name} is pinned to {label}, which is blocked by Strict Local-Only Lock. "
            f"Allow Cloud APIs in Settings or clear {agent_name}'s pinned model."
            if is_pinned
            else "Strict Local-Only Lock is active. Use a local Ollama model or disable the lock in Settings."
        )
        raise HTTPException(status_code=403, detail=detail)
    if not is_loopback_url(ollama_base_url()) and os.environ.get("REALM_ALLOW_REMOTE_OLLAMA", "").strip() != "1":
        raise HTTPException(status_code=403, detail="Strict Local-Only Lock blocks non-loopback OLLAMA_HOST targets.")


def resolve_agent_model(
    agent: AgentPersona,
    cfg: WorkspaceConfig,
    req_provider: str | None,
    req_model: str | None,
    req_api_key: str | None,
) -> tuple[str, str, str | None, bool, str]:
    """Resolve effective (provider, model, api_key, is_pinned, notice) respecting privacy & keys."""
    fallback_prov, fallback_model = (req_provider or "ollama").strip().lower(), (req_model or "").strip()
    pinned_prov, pinned_model = (agent.model_provider or "").strip().lower(), (agent.model_name or "").strip()
    if not pinned_prov:
        _enforce_local_only(cfg, fallback_prov, fallback_model, agent.name, False)
        return fallback_prov, fallback_model, req_api_key, False, ""
    _enforce_local_only(cfg, pinned_prov, pinned_model, agent.name, True)
    if pinned_prov != "ollama":
        candidate_key = req_api_key if pinned_prov == fallback_prov else None
        resolved_key = get_api_key(pinned_prov, candidate_key)
        if not resolved_key:
            _enforce_local_only(cfg, fallback_prov, fallback_model, agent.name, False)
            notice = f"{agent.name}'s pinned provider ({pinned_prov}) has no saved API key — fell back to {fallback_model or fallback_prov}."
            return fallback_prov, fallback_model, req_api_key, False, notice
        return pinned_prov, pinned_model, resolved_key, True, ""
    effective_model = pinned_model or fallback_model
    _enforce_local_only(cfg, "ollama", effective_model, agent.name, bool(pinned_model))
    return "ollama", effective_model, None, True, ""


def trim_history_for_model(history: list[tuple[str, str]], provider: str, model: str, summary: str = "") -> list[tuple[str, str]]:
    """Keep the most recent turns that fit comfortably inside the target model's context window."""
    if not history:
        return []
    budget = max(2048, int(model_context_window(provider, model or DEFAULT_LOCAL_MODEL) * 0.55) - approx_tokens(summary) - 1200)
    kept: list[tuple[str, str]] = []
    used = 0
    for pair in reversed(history):
        cost = approx_tokens(pair[0]) + approx_tokens(pair[1])
        if kept and used + cost > budget:
            break
        kept.append(pair)
        used += cost
    kept.reverse()
    return kept
