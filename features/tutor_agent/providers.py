"""Polymorphic LLM provider router for Built-in Private AI, Ollama, and Cloud providers."""

import json
import re
from contextlib import nullcontext

import httpx

from core.cancellation import post_cancellable
from core.contracts import ProviderName, TutorConfig, TutorResponse
from core.local_ai_paths import list_installed_builtin_models
from core.local_ai_sidecar import ensure_sidecar_running
from core.model_routing import ollama_slot
from core.runtime import is_loopback_url, ollama_base_url
from core.secrets import get_api_key
from features.tutor_agent.models_discovery import filter_chat_models

PROVIDER_ENDPOINTS: dict[ProviderName, tuple[str, str]] = {
    "builtin": ("http://127.0.0.1/v1/chat/completions", ""),
    "ollama": (f"{ollama_base_url()}/api/chat", ""),
    "openai": ("https://api.openai.com/v1/chat/completions", "OPENAI_API_KEY"),
    "kimi": ("https://api.moonshot.ai/v1/chat/completions", "MOONSHOT_API_KEY"),
    "deepseek": ("https://api.deepseek.com/chat/completions", "DEEPSEEK_API_KEY"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "GEMINI_API_KEY"),
    "xai": ("https://api.x.ai/v1/chat/completions", "XAI_API_KEY"),
    "mistral": ("https://api.mistral.ai/v1/chat/completions", "MISTRAL_API_KEY"),
    "anthropic": ("https://api.anthropic.com/v1/messages", "ANTHROPIC_API_KEY"),
}
BUILTIN_PROVIDER: ProviderName = "builtin"
OLLAMA_PROVIDER: ProviderName = "ollama"
ANTHROPIC_PROVIDER: ProviderName = "anthropic"
ANTHROPIC_VERSION, OLLAMA_TAGS_URL = "2023-06-01", f"{ollama_base_url()}/api/tags"
OLLAMA_TIMEOUT_SECONDS, REQUEST_TIMEOUT_SECONDS, LIST_TIMEOUT_SECONDS, MODELS_TIMEOUT_SECONDS = 90.0, 30.0, 5.0, 10.0
_OPENAI_REASONING_PREFIXES = ("o1", "o3", "o4", "gpt-5", "gpt-6")
_THINK_STRIP_RE, _ORIG_GET = re.compile(r"<think>[\s\S]*?(?:</think>|$)", re.IGNORECASE), httpx.get

def supports_reasoning_effort(provider: str, model: str) -> bool:
    low = model.lower()
    return (provider == "kimi" and low.startswith("kimi-k3")) or (provider == "openai" and low.startswith(_OPENAI_REASONING_PREFIXES)) or (provider == "xai" and low.startswith("grok-3-mini"))
def supports_temperature(provider: str, model: str) -> bool:
    low = model.lower()
    return not ((provider == "openai" and low.startswith(_OPENAI_REASONING_PREFIXES)) or (provider == "kimi" and low.startswith("kimi-k3")) or (provider == "deepseek" and "reasoner" in low))
def strip_json_fence(text: str) -> str:
    cleaned = _THINK_STRIP_RE.sub("", text or "").strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()[1:]
        cleaned = "\n".join(lines[:-1] if lines and lines[-1].strip().startswith("```") else lines).strip()
    return cleaned
def resolve_endpoint(config: TutorConfig) -> tuple[str, str, str | None]:
    if config.provider == BUILTIN_PROVIDER:
        url, token, resolved_id = ensure_sidecar_running(config.model)
        return url, resolved_id, token
    endpoint_url, _ = PROVIDER_ENDPOINTS[config.provider]
    if config.provider == OLLAMA_PROVIDER:
        endpoint_url = f"{ollama_base_url()}/api/chat"
    model = config.model.strip()
    if not model:
        raise ValueError(f"No model selected for {config.provider}. Open Settings and choose an available model.")
    return endpoint_url, model, get_api_key(config.provider, config.api_key)
def _check_status(response: object) -> None:
    status = getattr(response, "status_code", None)
    if isinstance(status, int) and status >= 400:
        if callable(checker := getattr(response, "raise_for_status", None)):
            checker()
        raise httpx.HTTPError(f"Provider returned HTTP {status}")
def _extract_anthropic_text(payload: object) -> str:
    blocks = payload.get("content") if isinstance(payload, dict) else None
    if not isinstance(blocks, list) or not blocks:
        raise ValueError("Empty Anthropic response")
    for block in blocks:
        if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str):
            return block["text"]
    for block in blocks:
        if isinstance(block, dict) and isinstance(block.get("text"), str):
            return block["text"]
    raise ValueError("No text block in Anthropic response")
def _safe_get(url: str, timeout: float, headers: dict[str, str] | None = None) -> httpx.Response:
    if httpx.get is not _ORIG_GET:
        return httpx.get(url, headers=headers, timeout=timeout) if headers else httpx.get(url, timeout=timeout)
    with httpx.Client(trust_env=not is_loopback_url(url), follow_redirects=False, timeout=timeout) as client:
        return client.get(url, headers=headers)

def call_provider(messages: list[dict[str, str]], config: TutorConfig, temperature: float | None = None) -> str:
    """Send chat messages to the configured LLM provider and return raw content."""
    temp = config.temperature if temperature is None else temperature
    with (ollama_slot(config.provider, config.model) if config.provider in {OLLAMA_PROVIDER, BUILTIN_PROVIDER} else nullcontext()):
        endpoint_url, model, api_key = resolve_endpoint(config)
        if config.provider == OLLAMA_PROVIDER:
            response = post_cancellable(endpoint_url, {"model": model, "messages": messages, "stream": False, "keep_alive": "90s", "format": TutorResponse.model_json_schema(), "options": {"temperature": temp, "num_predict": 1024}}, timeout=OLLAMA_TIMEOUT_SECONDS)
            _check_status(response)
            return str(response.json()["message"]["content"])
        if config.provider == ANTHROPIC_PROVIDER:
            system_prompt = "\n\n".join(m["content"] for m in messages if m.get("role") == "system" and m.get("content")) + f"\nJSON Schema: {json.dumps(TutorResponse.model_json_schema())}"
            response = post_cancellable(endpoint_url, {"model": model, "max_tokens": 1024, "temperature": temp, "system": system_prompt, "messages": [m for m in messages if m.get("role") != "system"]}, headers={"x-api-key": api_key or "", "anthropic-version": ANTHROPIC_VERSION}, timeout=REQUEST_TIMEOUT_SECONDS)
            _check_status(response)
            return _extract_anthropic_text(response.json())
        limit_key = "max_completion_tokens" if config.provider == "openai" and model.lower().startswith(_OPENAI_REASONING_PREFIXES) else "max_tokens"
        body: dict[str, object] = {"model": model, limit_key: 1024, "messages": messages, "response_format": {"type": "json_object"}}
        if config.provider == BUILTIN_PROVIDER:
            body["cache_prompt"] = True
        if supports_temperature(config.provider, model):
            body["temperature"] = temp
        if config.provider == "kimi" and model.lower().startswith("kimi-k3"):
            body["reasoning_effort"] = config.reasoning_effort or "low"
        elif config.reasoning_effort and supports_reasoning_effort(config.provider, model):
            body["reasoning_effort"] = config.reasoning_effort
        response = post_cancellable(endpoint_url, body, headers={"Authorization": f"Bearer {api_key or ''}"}, timeout=OLLAMA_TIMEOUT_SECONDS if config.provider == BUILTIN_PROVIDER else REQUEST_TIMEOUT_SECONDS)
        _check_status(response)
        data = response.json()
        choices = data.get("choices") if isinstance(data, dict) else None
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ValueError("Empty provider choices")
        return str(choices[0]["message"]["content"])

def list_provider_models(provider: ProviderName, api_key: str | None = None) -> list[str]:
    """List only genuinely discovered chat models from installed local files or live provider APIs."""
    if provider == BUILTIN_PROVIDER:
        return list_installed_builtin_models()
    if provider == OLLAMA_PROVIDER:
        try:
            url = OLLAMA_TAGS_URL if httpx.get is not _ORIG_GET else f"{ollama_base_url()}/api/tags"
            response = _safe_get(url, LIST_TIMEOUT_SECONDS)
            _check_status(response)
            raw = response.json()
            models_list = raw.get("models") if isinstance(raw, dict) else None
            return filter_chat_models([str(m.get("name", "")) for m in (models_list or []) if isinstance(m, dict)])
        except (httpx.HTTPError, ValueError, TypeError):
            return []
    base_url, _ = PROVIDER_ENDPOINTS[provider]
    if not (key := get_api_key(provider, api_key)):
        return []
    models_url = base_url.replace("/chat/completions", "/models").replace("/messages", "/models")
    headers = {"x-api-key": key, "anthropic-version": ANTHROPIC_VERSION} if provider == ANTHROPIC_PROVIDER else {"Authorization": f"Bearer {key}"}
    try:
        response = _safe_get(models_url, MODELS_TIMEOUT_SECONDS, headers=headers)
        _check_status(response)
        raw = response.json()
        data_list = raw.get("data") if isinstance(raw, dict) else None
        return filter_chat_models([str(m.get("id", "")).removeprefix("models/") for m in (data_list or []) if isinstance(m, dict)])
    except (httpx.HTTPError, ValueError, TypeError):
        return []
