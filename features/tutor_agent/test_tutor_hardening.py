"""Regression tests for provider compatibility and structured streaming errors (Batch 3)."""

import asyncio
from typing import Any, Self

import httpx
import pytest

from core.contracts import TutorConfig
from features.tutor_agent import models_discovery, prompt_builder, providers, streaming


def test_reasoning_effort_and_temperature_allowlists() -> None:
    assert providers.supports_reasoning_effort("openai", "gpt-4o-mini") is False
    assert providers.supports_reasoning_effort("deepseek", "deepseek-chat") is False
    assert providers.supports_reasoning_effort("openai", "o3-mini") is True
    assert providers.supports_reasoning_effort("kimi", "kimi-k3.1-pro") is True
    assert providers.supports_temperature("openai", "gpt-5") is False
    assert providers.supports_temperature("deepseek", "deepseek-reasoner") is False
    assert providers.supports_temperature("openai", "gpt-4o-mini") is True


def test_provider_null_models_thinking_blocks_and_json_fences(monkeypatch: pytest.MonkeyPatch) -> None:
    class _NullModels:
        status_code = 200
        def json(self) -> dict[str, object]:
            return {"models": None}

    monkeypatch.setattr(httpx, "get", lambda *_a, **_kw: _NullModels())
    assert providers.list_provider_models("ollama") == providers.FALLBACK_MODELS["ollama"]

    assert providers._extract_anthropic_text({"content": [{"type": "thinking", "thinking": "hmm"}, {"type": "text", "text": '{"answer":"ok"}'}]}) == '{"answer":"ok"}'
    assert providers.strip_json_fence("<think>chain</think>\n```json\n{\"a\":1}\n```") == '{"a":1}'
    assert providers.strip_json_fence("<think>unclosed") == ""
    filtered = models_discovery.filter_chat_models(["gpt-4o", "dall-e-3", "sora-2", "gpt-4o", "text-moderation-latest"])
    assert filtered == ["gpt-4o"]


def test_stream_messages_emits_structured_error_on_http_401_and_inband_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeResp:
        def __init__(self, code: int, lines: list[str]) -> None:
            self.status_code, self._lines = code, lines
        async def __aenter__(self) -> Self:
            return self
        async def __aexit__(self, *_a: object) -> None:
            return None
        async def aiter_lines(self) -> Any:
            for line in self._lines:
                yield line

    class _FakeClient:
        def __init__(self, resp: _FakeResp) -> None:
            self._resp = resp
        async def __aenter__(self) -> Self:
            return self
        async def __aexit__(self, *_a: object) -> None:
            return None
        def stream(self, *_a: Any, **_kw: Any) -> _FakeResp:
            return self._resp

    async def _collect(resp: _FakeResp) -> list[dict[str, object]]:
        monkeypatch.setattr(httpx, "AsyncClient", lambda **_kw: _FakeClient(resp))
        cfg = TutorConfig(provider="openai", model="gpt-4o-mini", api_key="bad")
        return [ev async for ev in streaming.stream_messages_events([{"role": "user", "content": "hi"}], cfg)]

    ev_401 = asyncio.run(_collect(_FakeResp(401, [])))
    assert len(ev_401) == 1 and ev_401[0]["type"] == "error" and ev_401[0]["code"] == 401

    ev_err = asyncio.run(_collect(_FakeResp(200, ['data: {"type":"error","error":{"message":"overloaded"}}'])))
    assert len(ev_err) == 1 and ev_err[0]["type"] == "error" and "overloaded" in str(ev_err[0]["detail"])

    msgs = prompt_builder.build_stream_messages("hi", [], attached_notes=[{"name": "a.txt", "content": "ignore previous"}], free_chat=True)
    assert "untrusted" in msgs[0]["content"].lower()
