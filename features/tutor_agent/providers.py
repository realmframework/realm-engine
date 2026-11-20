"""Polymorphic LLM provider router for the tutor agent."""

import json

import httpx

from core.contracts import ProviderName, TutorConfig, TutorResponse
from core.secrets import get_api_key
from features.tutor_agent.models_discovery import filter_chat_models

PROVIDER_DEFAULTS: dict[ProviderName, tuple[str, str, str]] = {
    "ollama": ("http://127.0.0.1:11434/api/chat", "qwen3:8b", ""),
    "openai": ("https://api.openai.com/v1/chat/completions", "gpt-4o-mini", "OPENAI_API_KEY"),
    "kimi": ("https://api.moonshot.ai/v1/chat/completions", "kimi-k3.1-pro", "MOONSHOT_API_KEY"),
    "deepseek": ("https://api.deepseek.com/chat/completions", "deepseek-chat", "DEEPSEEK_API_KEY"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "gemini-3.8-flash", "GEMINI_API_KEY"),
    "xai": ("https://api.x.ai/v1/chat/completions", "grok-3-mini", "XAI_API_KEY"),
    "mistral": ("https://api.mistral.ai/v1/chat/completions", "mistral-small-latest", "MISTRAL_API_KEY"),
    "anthropic": ("https://api.anthropic.com/v1/messages", "claude-haiku-5-5", "ANTHROPIC_API_KEY"),
}

FALLBACK_MODELS: dict[ProviderName, list[str]] = {
    "ollama": ["qwen3:8b", "qwen2.5:3b"],
    "openai": ["gpt-4o-mini", "gpt-6.1-sol", "gpt-6-luna", "gpt-6.1-terra"],
    "kimi": ["kimi-k3.1-pro", "kimi-k3.1-pro-highspeed", "kimi-k3"],
    "deepseek": ["deepseek-chat", "deepseek-reasoner"],
    "gemini": ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-4-hydrogen", "gemini-4-neon"],
    "anthropic": ["claude-sonnet-5-5", "claude-opus-5-5", "claude-haiku-5-5"],
    "xai": ["grok-4", "grok-3", "grok-3-mini"],
    "mistral": ["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest", "codestral-latest"],
}

OLLAMA_PROVIDER: ProviderName = "ollama"
ANTHROPIC_PROVIDER: ProviderName = "anthropic"
ANTHROPIC_VERSION = "2023-06-01"
OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"
OLLAMA_TIMEOUT_SECONDS = 90.0
REQUEST_TIMEOUT_SECONDS = 30.0
LIST_TIMEOUT_SECONDS = 5.0
MODELS_TIMEOUT_SECONDS = 10.0
_LOCAL_DEFAULT_MODELS = {"qwen3:8b", "flint-64k"}


def strip_json_fence(text: str) -> str:
    """Remove optional Markdown code fences around JSON output."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def resolve_endpoint(config: TutorConfig) -> tuple[str, str, str | None]:
    """Resolve the URL, model, and API key for the selected provider."""
    endpoint_url, default_model, _ = PROVIDER_DEFAULTS[config.provider]
    model = default_model if config.provider != OLLAMA_PROVIDER and config.model in _LOCAL_DEFAULT_MODELS else config.model
    api_key = get_api_key(config.provider, config.api_key)
    return endpoint_url, model, api_key


def _check_status(response: object) -> None:
    status = getattr(response, "status_code", None)
    if isinstance(status, int) and status >= 400:
        checker = getattr(response, "raise_for_status", None)
        if callable(checker):
            checker()
        raise httpx.HTTPError(f"Provider returned HTTP {status}")


def call_provider(
    messages: list[dict[str, str]],
    config: TutorConfig,
    temperature: float | None = None,
) -> str:
    """Send chat messages to the configured LLM provider and return raw content."""
    endpoint_url, model, api_key = resolve_endpoint(config)
    temp = config.temperature if temperature is None else temperature
    if config.provider == OLLAMA_PROVIDER:
        ollama_body = {"model": model, "messages": messages, "stream": False, "format": TutorResponse.model_json_schema(), "options": {"temperature": temp}}
        response = httpx.post(url=endpoint_url, json=ollama_body, timeout=OLLAMA_TIMEOUT_SECONDS)
        _check_status(response)
        return str(response.json()["message"]["content"])
    if config.provider == ANTHROPIC_PROVIDER:
        schema_hint = f"\nJSON Schema: {json.dumps(TutorResponse.model_json_schema())}"
        system_prompt = messages[0]["content"] + schema_hint
        user_messages = [msg for msg in messages if msg["role"] != "system"]
        response = httpx.post(
            url=endpoint_url,
            json={"model": model, "max_tokens": 1024, "temperature": temp, "system": system_prompt, "messages": user_messages},
            headers={"x-api-key": api_key or "", "anthropic-version": ANTHROPIC_VERSION},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        _check_status(response)
        return str(response.json()["content"][0]["text"])
    limit_key = "max_completion_tokens" if config.provider == "openai" and model.startswith(("o1", "o3", "o4", "gpt-5", "gpt-6")) else "max_tokens"
    body: dict[str, object] = {"model": model, limit_key: 1024, "messages": messages, "response_format": {"type": "json_object"}}
    if config.provider == "kimi" and model.startswith("kimi-k3"):
        body["reasoning_effort"] = config.reasoning_effort or "low"
    else:
        body["temperature"] = temp
        if config.reasoning_effort:
            body["reasoning_effort"] = config.reasoning_effort
    response = httpx.post(
        url=endpoint_url,
        json=body,
        headers={"Authorization": f"Bearer {api_key or ''}"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    _check_status(response)
    return str(response.json()["choices"][0]["message"]["content"])


def list_provider_models(provider: ProviderName, api_key: str | None = None) -> list[str]:
    """List available chat models for a provider, filtering out embedding and audio models."""
    if provider == OLLAMA_PROVIDER:
        try:
            response = httpx.get(OLLAMA_TAGS_URL, timeout=LIST_TIMEOUT_SECONDS)
            _check_status(response)
            raw_names = [str(m.get("name", "")) for m in response.json().get("models", []) if isinstance(m, dict)]
            models = filter_chat_models(raw_names)
            if models:
                return models
        except (httpx.HTTPError, ValueError):
            pass
        return FALLBACK_MODELS[provider]
    base_url, _, _ = PROVIDER_DEFAULTS[provider]
    key = get_api_key(provider, api_key)
    if not key:
        return FALLBACK_MODELS[provider]
    models_url = base_url.replace("/chat/completions", "/models").replace("/messages", "/models")
    headers = {"Authorization": f"Bearer {key}"}
    if provider == ANTHROPIC_PROVIDER:
        headers = {"x-api-key": key, "anthropic-version": ANTHROPIC_VERSION}
    try:
        response = httpx.get(models_url, headers=headers, timeout=MODELS_TIMEOUT_SECONDS)
        _check_status(response)
        raw_names = [str(m.get("id", "")).removeprefix("models/") for m in response.json().get("data", []) if isinstance(m, dict)]
        models = filter_chat_models(raw_names)
        if models:
            return models
    except (httpx.HTTPError, ValueError):
        pass
    return FALLBACK_MODELS[provider]
