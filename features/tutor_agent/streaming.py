"""Live token + thinking streaming and telemetry for Ollama and Cloud LLM providers."""

import asyncio
import json
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from core.cancellation import attach_current_task, check_cancelled
from core.contracts import SearchResult, TutorConfig
from core.logging_config import get_logger
from core.model_routing import async_ollama_slot
from core.runtime import is_loopback_url
from features.tutor_agent import prompt_builder as _pb
from features.tutor_agent import providers as _prov
from features.tutor_agent.budget import check_and_record_budget, estimate_usage
from features.tutor_agent.service import fallback_tutor_response

MAX_STREAM_SECONDS, MAX_STREAM_CHARS = 300.0, 131_072
_LOG = get_logger("streaming")


def _build_stream_request(messages: list[dict[str, str]], config: TutorConfig, temperature: float, max_tokens: int = 2048) -> tuple[str, dict[str, Any], dict[str, str], float]:
    url, model, api_key = _prov.resolve_endpoint(config)
    if config.provider == _prov.OLLAMA_PROVIDER:
        keep_alive = "60s" if config.reasoning_effort == "low" else "90s"
        return url, {"model": model, "messages": messages, "stream": True, "keep_alive": keep_alive, "options": {"temperature": temperature, "num_predict": max_tokens}}, {}, _prov.OLLAMA_TIMEOUT_SECONDS
    if config.provider == _prov.ANTHROPIC_PROVIDER:
        sys_parts = [m["content"] for m in messages if m.get("role") == "system" and m.get("content")]
        body: dict[str, Any] = {"model": model, "max_tokens": max_tokens, "temperature": temperature, "stream": True, "system": "\n\n".join(sys_parts), "messages": [m for m in messages if m.get("role") != "system"]}
        return url, body, {"x-api-key": api_key or "", "anthropic-version": _prov.ANTHROPIC_VERSION}, _prov.REQUEST_TIMEOUT_SECONDS
    is_oai_reasoning = config.provider == "openai" and model.lower().startswith(("o1", "o3", "o4", "gpt-5", "gpt-6"))
    limit_key = "max_completion_tokens" if is_oai_reasoning else "max_tokens"
    cap = max(max_tokens, 4096) if is_oai_reasoning else max_tokens
    body = {"model": model, limit_key: cap, "messages": messages, "stream": True}
    if config.provider in {"openai", "deepseek"}:
        body["stream_options"] = {"include_usage": True}
    if _prov.supports_temperature(config.provider, model):
        body["temperature"] = temperature
    if config.provider == "kimi" and model.lower().startswith("kimi-k3"):
        body["reasoning_effort"] = config.reasoning_effort or "low"
    elif config.reasoning_effort and _prov.supports_reasoning_effort(config.provider, model):
        body["reasoning_effort"] = config.reasoning_effort
    return url, body, {"Authorization": f"Bearer {api_key or ''}"}, _prov.REQUEST_TIMEOUT_SECONDS


async def stream_messages_events(messages: list[dict[str, str]], config: TutorConfig, temperature: float | None = None, request_id: str | None = None, fallback_text: str = "", max_tokens: int = 2048) -> AsyncIterator[dict[str, object]]:
    """Yield live {type: 'thinking'|'token'|'meta'|'error'} dicts from the configured LLM provider."""
    check_cancelled()
    active_temp = config.temperature if temperature is None else temperature
    est_in, cost = estimate_usage(str(messages), output_tokens=max_tokens)
    if denied := check_and_record_budget(config.provider, est_in, config.daily_cloud_request_limit, config.daily_budget_usd_limit, cost):
        yield {"type": "error", "code": 429, "detail": denied}
        return
    url, body, headers, timeout = _build_stream_request(messages, config, active_temp, max_tokens=max_tokens)
    _, resolved_model, _ = _prov.resolve_endpoint(config)
    detach = attach_current_task(request_id)
    started, emitted_chars, think_chars, real_usage, failed = time.perf_counter(), 0, 0, {}, False
    try:
        async with async_ollama_slot(config.provider, resolved_model), httpx.AsyncClient(timeout=timeout, trust_env=not is_loopback_url(url), follow_redirects=False) as client, client.stream("POST", url, json=body, headers=headers) as response:
            if response.status_code in {401, 403}:
                yield {"type": "error", "code": response.status_code, "detail": f"AI provider rejected credentials (HTTP {response.status_code}). Check your API key in Settings or switch to Local Ollama."}
                return
            if response.status_code == 429:
                yield {"type": "error", "code": 429, "detail": "AI provider rate limit or quota reached (HTTP 429). Wait a moment or switch models."}
                return
            if response.status_code >= 400:
                if fallback_text:
                    emitted_chars = len(fallback_text)
                    yield {"type": "token", "delta": fallback_text}
                else:
                    yield {"type": "error", "code": response.status_code, "detail": f"AI provider returned HTTP {response.status_code}. Check model settings or try again."}
                    return
            else:
                async for raw_line in response.aiter_lines():
                    check_cancelled()
                    if time.perf_counter() - started > MAX_STREAM_SECONDS or emitted_chars + think_chars >= MAX_STREAM_CHARS:
                        break
                    line = raw_line.strip()
                    if not line:
                        continue
                    if config.provider != _prov.OLLAMA_PROVIDER:
                        if not line.startswith("data:"):
                            continue
                        line = line[5:].strip()
                        if not line or line == "[DONE]":
                            break
                    try:
                        chunk_json = json.loads(line)
                    except ValueError:
                        continue
                    if not isinstance(chunk_json, dict):
                        continue
                    if stream_err := _pb.extract_stream_error(chunk_json):
                        failed = True
                        yield {"type": "error", "code": 502, "detail": stream_err}
                        return
                    content, thinking, usage = _pb.extract_stream_chunk(config.provider, chunk_json)
                    real_usage.update(usage)
                    if thinking:
                        think_chars += len(thinking)
                        yield {"type": "thinking", "delta": thinking}
                    if content:
                        emitted_chars += len(content)
                        yield {"type": "token", "delta": content}
                    if config.provider == _prov.OLLAMA_PROVIDER and chunk_json.get("done"):
                        break
    except (asyncio.CancelledError, InterruptedError) as exc:
        raise InterruptedError("Generation stopped by user.") from exc
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        _LOG.warning("Provider stream interrupted (%s/%s): %s", config.provider, resolved_model, type(exc).__name__)
        if emitted_chars == 0 and fallback_text:
            emitted_chars = len(fallback_text)
            yield {"type": "token", "delta": fallback_text}
        else:
            failed = True
            yield {"type": "error", "code": 503, "detail": "Connection to the AI provider was interrupted before completion."}
            return
    finally:
        detach()
    if failed:
        return
    elapsed_ms = max(1, int((time.perf_counter() - started) * 1000))
    out_tokens = int(real_usage.get("completion_tokens") or max(1, (emitted_chars + 3) // 4))
    in_tokens = int(real_usage.get("prompt_tokens") or est_in)
    yield {
        "type": "meta", "provider": config.provider, "model": resolved_model,
        "prompt_tokens": in_tokens, "completion_tokens": out_tokens,
        "thinking_tokens": max(0, (think_chars + 3) // 4), "duration_ms": elapsed_ms,
        "tokens_per_sec": round(out_tokens / max(0.05, elapsed_ms / 1000.0), 1),
    }


async def stream_tutor_events(question: str, results: list[SearchResult], config: TutorConfig | None = None, history: list[tuple[str, str]] | None = None, temperature: float | None = None, request_id: str | None = None, compacted_summary: str = "", attached_notes: list[dict[str, str]] | None = None, format_instruction: str = "", free_chat: bool = False, persona_instruction: str = "", web_search_requested: bool = False) -> AsyncIterator[dict[str, object]]:
    tutor_config = config or TutorConfig()
    messages = _pb.build_stream_messages(question, results, history=history, response_language=tutor_config.response_language, compacted_summary=compacted_summary, attached_notes=attached_notes, format_instruction=format_instruction, free_chat=free_chat, persona_instruction=persona_instruction, web_search_requested=web_search_requested)
    fallback = "" if free_chat else fallback_tutor_response(question, results).answer
    async for ev in stream_messages_events(messages, tutor_config, temperature=temperature, request_id=request_id, fallback_text=fallback):
        yield ev


async def stream_tutor_tokens(question: str, results: list[SearchResult], config: TutorConfig | None = None, history: list[tuple[str, str]] | None = None, temperature: float | None = None, request_id: str | None = None) -> AsyncIterator[str]:
    async for ev in stream_tutor_events(question, results, config=config, history=history, temperature=temperature, request_id=request_id):
        if ev.get("type") == "token" and ev.get("delta"):
            yield str(ev["delta"])
