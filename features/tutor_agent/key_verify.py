"""Lightweight live API key verification against cloud providers without leaking secrets."""

from __future__ import annotations

import httpx

from core.runtime import is_loopback_url, ollama_base_url
from core.secrets import ENV_VARS, get_api_key
from features.tutor_agent.models_discovery import filter_chat_models
from features.tutor_agent.providers import (
    ANTHROPIC_PROVIDER,
    ANTHROPIC_VERSION,
    PROVIDER_ENDPOINTS,
)

VERIFY_TIMEOUT_SECONDS = 8.0
ELEVENLABS_USER_URL = "https://api.elevenlabs.io/v1/user"


def _probe_url_and_headers(provider: str, key: str) -> tuple[str, dict[str, str]] | None:
    if provider == "ollama":
        return f"{ollama_base_url()}/api/tags", {}
    if provider == "elevenlabs":
        return ELEVENLABS_USER_URL, {"xi-api-key": key}
    if provider in PROVIDER_ENDPOINTS:
        base_url = PROVIDER_ENDPOINTS[provider][0]  # type: ignore[index]
        models_url = base_url.replace("/chat/completions", "/models").replace("/messages", "/models")
        if provider == ANTHROPIC_PROVIDER:
            return models_url, {"x-api-key": key, "anthropic-version": ANTHROPIC_VERSION}
        return models_url, {"Authorization": f"Bearer {key}"}
    return None


def _count_models(provider: str, payload: object) -> int:
    if not isinstance(payload, dict):
        return 0
    if provider == "ollama":
        raw = payload.get("models")
        names = [str(m.get("name", "")) for m in raw if isinstance(m, dict)] if isinstance(raw, list) else []
        return len(filter_chat_models(names))
    raw = payload.get("data")
    if isinstance(raw, list):
        names = [str(m.get("id", "")).removeprefix("models/") for m in raw if isinstance(m, dict)]
        return len(filter_chat_models(names))
    return 0


def verify_provider_key(provider: str, api_key: str | None = None) -> dict[str, object]:
    """Verify an explicit or stored provider API key with a minimal auth probe."""
    clean_provider = provider.strip().lower()
    if clean_provider != "ollama" and clean_provider not in ENV_VARS:
        raise ValueError(f"Unsupported provider: {clean_provider}")
    key = "" if clean_provider == "ollama" else (get_api_key(clean_provider, api_key) or "")
    if clean_provider != "ollama" and not key:
        return {"ok": False, "status": "missing", "models_count": 0}
    target = _probe_url_and_headers(clean_provider, key)
    if target is None:
        return {"ok": True, "status": "saved", "models_count": 0}
    url, headers = target
    try:
        with httpx.Client(trust_env=not is_loopback_url(url), follow_redirects=False, timeout=VERIFY_TIMEOUT_SECONDS) as client:
            response = client.get(url, headers=headers)
    except httpx.HTTPError:
        return {"ok": False, "status": "unreachable", "models_count": 0}
    code = int(response.status_code)
    if 200 <= code < 300:
        try:
            body: object = response.json()
        except ValueError:
            body = {}
        return {"ok": True, "status": "valid", "models_count": _count_models(clean_provider, body)}
    if code in {401, 403}:
        return {"ok": False, "status": "invalid", "http_status": code, "models_count": 0}
    if code == 429:
        return {"ok": True, "status": "rate_limited", "http_status": code, "models_count": 0}
    return {"ok": False, "status": "error", "http_status": code, "models_count": 0}
