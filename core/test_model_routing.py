"""Tests for per-agent model pinning, Local-Only Lock enforcement, Ollama RAM unloading, and context fitting."""

from pathlib import Path

import pytest
from fastapi import HTTPException

from core import agent_personas, model_routing
from core.agent_presets import AgentPersona
from core.contracts import WorkspaceConfig


def test_persona_round_trips_pinned_provider_and_model(tmp_path: Path) -> None:
    saved = agent_personas.save_agent(
        tmp_path,
        agent_id="erika",
        name="Erika",
        role="Editorial Strategist",
        model_provider="gemini",
        model_name="gemini-3.8-flash",
        instructions="## Analytical Lens\nSharp synthesis.",
    )
    assert saved.model_provider == "gemini" and saved.model_name == "gemini-3.8-flash" and saved.customized is True
    reloaded = agent_personas.get_agent(tmp_path, "erika")
    assert reloaded.model_provider == "gemini" and reloaded.model_name == "gemini-3.8-flash"


def test_resolve_agent_model_blocks_cloud_under_strict_local_lock() -> None:
    erika = AgentPersona(id="erika", name="Erika", model_provider="anthropic", model_name="claude-opus-5-5")
    with pytest.raises(HTTPException) as exc:
        model_routing.resolve_agent_model(erika, WorkspaceConfig(strict_local_only=True), "ollama", "qwen3:8b", None)
    assert exc.value.status_code == 403 and "Local-Only Lock" in str(exc.value.detail)


def test_resolve_agent_model_fallback_without_key_and_isolates_provider_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    erika = AgentPersona(id="erika", name="Erika", model_provider="anthropic", model_name="claude-sonnet-5-5")
    seen: list[tuple[str, str | None]] = []

    def fake_get_key(provider: str, override: str | None = None) -> str | None:
        seen.append((provider, override))
        return "sk-ant-real" if provider == "anthropic" else None

    # No key configured -> falls back cleanly without leaking OpenAI key to Anthropic
    monkeypatch.setattr(model_routing, "get_api_key", lambda p, o=None: (seen.append((p, o)), None)[1])
    prov, mdl, key, pinned, notice = model_routing.resolve_agent_model(
        erika, WorkspaceConfig(strict_local_only=False), "openai", "gpt-4o-mini", "sk-openai-secret"
    )
    assert (prov, mdl, key, pinned) == ("openai", "gpt-4o-mini", "sk-openai-secret", False)
    assert seen == [("anthropic", None)] and "no saved API key" in notice

    # Key configured -> genuinely routes to Anthropic with Anthropic's own key
    seen.clear()
    monkeypatch.setattr(model_routing, "get_api_key", fake_get_key)
    prov, mdl, key, pinned, notice = model_routing.resolve_agent_model(
        erika, WorkspaceConfig(strict_local_only=False), "ollama", "qwen3:8b", None
    )
    assert (prov, mdl, key, pinned, notice) == ("anthropic", "claude-sonnet-5-5", "sk-ant-real", True, "")


def test_ollama_ram_guard_unloads_previous_local_model_and_trims_history(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(model_routing, "_LAST_OLLAMA_MODEL", "")
    monkeypatch.setattr(
        model_routing.httpx,
        "post",
        lambda url, json, timeout: (calls.append((url, dict(json))), type("R", (), {"status_code": 404})())[1],
    )
    assert model_routing.maybe_unload_previous_ollama("ollama", "qwen3:8b") is None
    assert calls == []
    assert model_routing.maybe_unload_previous_ollama("ollama", "qwen3:8b") is None
    assert calls == []
    assert model_routing.maybe_unload_previous_ollama("ollama", "llama3.3:latest") == "qwen3:8b"
    assert calls == [(model_routing.OLLAMA_CHAT_URL, {"model": "qwen3:8b", "keep_alive": 0})]

    big_history = [(f"Question {i}", "x" * 20000) for i in range(6)]
    trimmed = model_routing.trim_history_for_model(big_history, "ollama", "phi3:mini")
    assert 1 <= len(trimmed) < len(big_history) and trimmed[-1] == big_history[-1]
