"""Live token + thinking streaming and telemetry for Ollama and Cloud LLM providers."""

import asyncio
import json
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from core.cancellation import attach_current_task, check_cancelled
from core.contracts import SearchResult, TutorConfig
from features.tutor_agent.budget import check_and_record_budget, estimate_usage
from features.tutor_agent.prompt_builder import (
    build_stream_messages,
    extract_stream_chunk,
)
from features.tutor_agent.providers import (
    ANTHROPIC_PROVIDER,
    ANTHROPIC_VERSION,
    OLLAMA_PROVIDER,
    OLLAMA_TIMEOUT_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    resolve_endpoint,
)
from features.tutor_agent.service import fallback_tutor_response


def _build_stream_request(messages: list[dict[str, str]], config: TutorConfig, temperature: float, max_tokens: int = 2048) -> tuple[str, dict[str, Any], dict[str, str], float]:
    url, model, api_key = resolve_endpoint(config)
    if config.provider == OLLAMA_PROVIDER:
        return url, {"model": model, "messages": messages, "stream": True, "options": {"temperature": temperature}}, {}, OLLAMA_TIMEOUT_SECONDS
    if config.provider == ANTHROPIC_PROVIDER:
        body: dict[str, Any] = {"model": model, "max_tokens": max_tokens, "temperature": temperature, "stream": True, "system": messages[0]["content"], "messages": [m for m in messages if m["role"] != "system"]}
        return url, body, {"x-api-key": api_key or "", "anthropic-version": ANTHROPIC_VERSION}, REQUEST_TIMEOUT_SECONDS
    limit_key = "max_completion_tokens" if config.provider == "openai" and model.startswith(("o1", "o3", "o4", "gpt-5", "gpt-6")) else "max_tokens"
    body = {"model": model, limit_key: max_tokens, "messages": messages, "stream": True}
    if config.provider in {"openai", "deepseek"}:
        body["stream_options"] = {"include_usage": True}
    if config.provider == "kimi" and model.startswith("kimi-k3"):
        body["reasoning_effort"] = config.reasoning_effort or "low"
    else:
        body["temperature"] = temperature
        if config.reasoning_effort:
            body["reasoning_effort"] = config.reasoning_effort
    return url, body, {"Authorization": f"Bearer {api_key or ''}"}, REQUEST_TIMEOUT_SECONDS


async def stream_messages_events(messages: list[dict[str, str]], config: TutorConfig, temperature: float | None = None, request_id: str | None = None, fallback_text: str = "", max_tokens: int = 2048) -> AsyncIterator[dict[str, object]]:
    """Yield live {type: 'thinking'|'token'|'meta'} dicts from the configured LLM provider."""
    active_temp = config.temperature if temperature is None else temperature
    est_in, cost = estimate_usage(str(messages))
    denied = check_and_record_budget(config.provider, est_in, config.daily_cloud_request_limit, config.daily_budget_usd_limit, cost)
    if denied:
        yield {"type": "token", "delta": denied}
        return
    url, body, headers, timeout = _build_stream_request(messages, config, active_temp, max_tokens=max_tokens)
    _, resolved_model, _ = resolve_endpoint(config)
    detach = attach_current_task(request_id)
    started = time.perf_counter()
    emitted_chars, think_chars, real_usage = 0, 0, {}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client, client.stream("POST", url, json=body, headers=headers) as response:
            if response.status_code in {401, 403}:
                yield {"type": "token", "delta": f"AI provider rejected credentials (HTTP {response.status_code}). Check your API key in Settings or switch to Local Ollama."}
                return
            if response.status_code == 429:
                yield {"type": "token", "delta": "AI provider rate limit or quota reached (HTTP 429). Wait a moment or switch models."}
                return
            if response.status_code >= 400:
                if fallback_text:
                    yield {"type": "token", "delta": fallback_text}
                return
            async for raw_line in response.aiter_lines():
                check_cancelled()
                line = raw_line.strip()
                if not line:
                    continue
                if config.provider != OLLAMA_PROVIDER:
                    if not line.startswith("data:"):
                        continue
                    line = line[5:].strip()
                    if not line or line == "[DONE]":
                        break
                try:
                    chunk_json = json.loads(line)
                except ValueError:
                    continue
                if isinstance(chunk_json, dict):
                    content, thinking, usage = extract_stream_chunk(config.provider, chunk_json)
                    real_usage.update(usage)
                    if thinking:
                        think_chars += len(thinking)
                        yield {"type": "thinking", "delta": thinking}
                    if content:
                        emitted_chars += len(content)
                        yield {"type": "token", "delta": content}
                    if config.provider == OLLAMA_PROVIDER and chunk_json.get("done"):
                        break
    except (asyncio.CancelledError, InterruptedError) as exc:
        raise InterruptedError("Generation stopped by user.") from exc
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        if emitted_chars == 0 and fallback_text:
            yield {"type": "token", "delta": fallback_text}
    finally:
        detach()
    elapsed_ms = max(1, int((time.perf_counter() - started) * 1000))
    out_tokens = int(real_usage.get("completion_tokens") or max(1, (emitted_chars + 3) // 4))
    in_tokens = int(real_usage.get("prompt_tokens") or est_in)
    yield {
        "type": "meta", "provider": config.provider, "model": resolved_model,
        "prompt_tokens": in_tokens, "completion_tokens": out_tokens,
        "thinking_tokens": max(0, (think_chars + 3) // 4), "duration_ms": elapsed_ms,
        "tokens_per_sec": round(out_tokens / max(0.05, elapsed_ms / 1000.0), 1),
    }


async def stream_tutor_events(question: str, results: list[SearchResult], config: TutorConfig | None = None, history: list[tuple[str, str]] | None = None, temperature: float | None = None, request_id: str | None = None, compacted_summary: str = "", attached_notes: list[dict[str, str]] | None = None, format_instruction: str = "", free_chat: bool = False) -> AsyncIterator[dict[str, object]]:
    tutor_config = config or TutorConfig()
    messages = build_stream_messages(question, results, history=history, response_language=tutor_config.response_language, compacted_summary=compacted_summary, attached_notes=attached_notes, format_instruction=format_instruction, free_chat=free_chat)
    fallback = "" if free_chat else fallback_tutor_response(question, results).answer
    async for ev in stream_messages_events(messages, tutor_config, temperature=temperature, request_id=request_id, fallback_text=fallback):
        yield ev


async def stream_tutor_tokens(question: str, results: list[SearchResult], config: TutorConfig | None = None, history: list[tuple[str, str]] | None = None, temperature: float | None = None, request_id: str | None = None) -> AsyncIterator[str]:
    async for ev in stream_tutor_events(question, results, config=config, history=history, temperature=temperature, request_id=request_id):
        if ev.get("type") == "token" and ev.get("delta"):
            yield str(ev["delta"])
