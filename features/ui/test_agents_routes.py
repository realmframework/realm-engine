"""Integration tests for Agent Team API, persona.md CRUD, and mid-chat agent switching."""

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from features.ui import app as ui_app


def test_agent_team_api_crud_and_ui_shell(area_client: TestClient, tmp_path: Path) -> None:
    listed = area_client.get("/api/agents")
    assert listed.status_code == 200
    body = listed.json()
    assert body["active_agent"] == "saga" and body["sync_agent_palette"] is True
    ids = [a["id"] for a in body["agents"]]
    assert ids[:8] == ["saga", "lisbeth", "blomkvist", "plague", "milton", "erika", "annika", "palmgren"]
    assert "raw_markdown" in body["agents"][0] and "## Signature Moves" in body["agents"][0]["raw_markdown"]

    # Select Lisbeth & toggle palette sync off
    sel = area_client.post("/api/agents/select", json={"agent_id": "lisbeth", "sync_agent_palette": False})
    assert sel.status_code == 200 and sel.json()["active_agent"] == "lisbeth" and sel.json()["sync_agent_palette"] is False

    # Create a custom agent
    created = area_client.post(
        "/api/agents",
        json={"name": "Startup CFO", "role": "Finance Advisor", "tagline": "Unit economics & burn rate.", "palette": "wasp", "temperature": 0.15, "instructions": "## Analytical Lens\nFocus on margin and runway."},
    )
    assert created.status_code == 200 and created.json()["agent"]["id"] == "startup_cfo"
    assert (tmp_path / "agents" / "startup_cfo" / "persona.md").is_file()

    # Delete built-in + restore defaults
    assert area_client.delete("/api/agents/erika").json()["deleted"] is True
    assert area_client.get("/api/agents").json()["has_missing_defaults"] is True
    assert area_client.post("/api/agents/restore-defaults").json()["has_missing_defaults"] is False
    assert area_client.delete("/api/agents/startup_cfo").json()["deleted"] is True

    # UI exposes Agent Studio controls without cluttering the hero canvas
    html = area_client.get("/").text
    for marker in ('id="sidebar-agents-btn"', 'id="sidebar-agent-badge"', 'id="agent-studio-modal"', 'id="agent-sync-palette-toggle"', 'id="onboarding-sync-agent-palette"', "Your Agents", "exportMenuHtml", "persona.md", "openAgentStudio"):
        assert marker in html
    assert "Team Roster" not in html


def test_mid_chat_agent_switching_stamps_turns_and_injects_persona(
    area_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen_personas: list[str] = []

    async def fake_stream_tutor(*_args: object, free_chat: bool = False, persona_instruction: str = "", **_kwargs: object) -> AsyncIterator[dict[str, object]]:
        assert free_chat is True
        seen_personas.append(persona_instruction)
        yield {"type": "token", "delta": "Structured response."}
        yield {"type": "meta", "provider": "ollama", "model": "qwen3:8b", "prompt_tokens": 140, "completion_tokens": 12, "thinking_tokens": 0, "duration_ms": 80, "tokens_per_sec": 150.0}

    monkeypatch.setattr(ui_app, "stream_tutor_events", fake_stream_tutor)
    fresh = TestClient(ui_app._build_local_app())

    r1 = fresh.post("/api/chats/team-chat-1/turn/stream", json={"query": "Draft spec", "free_chat": True, "ask_tutor": True, "agent_id": "saga"})
    assert r1.status_code == 200 and "event: done" in r1.text

    r2 = fresh.post("/api/chats/team-chat-1/turn/stream", json={"query": "Find threat vectors", "free_chat": True, "ask_tutor": True, "agent_id": "milton"})
    assert r2.status_code == 200 and "event: done" in r2.text

    assert "[ACTIVE AGENT PERSONA: Saga" in seen_personas[0]
    assert "[ACTIVE AGENT PERSONA: Milton" in seen_personas[1]

    session = fresh.get("/api/chats/team-chat-1?free_chat=true").json()
    assert session["last_agent_id"] == "milton"
    assert [(t["agent_id"], t["agent_name"]) for t in session["turns"]] == [("saga", "Saga"), ("milton", "Milton")]

    ctx = fresh.get("/api/chats/team-chat-1/context?free_chat=true").json()
    assert ctx["context_usage"]["persona_tokens"] > 0

    # Explicit mid-chat agent switch persists last_agent_id WITHOUT rewriting past turns' agent_name
    switched = fresh.post("/api/chats/team-chat-1/agent", json={"agent_id": "lisbeth", "free_chat": True})
    assert switched.status_code == 200 and switched.json()["last_agent_id"] == "lisbeth"
    after_switch = fresh.get("/api/chats/team-chat-1?free_chat=true").json()
    assert after_switch["last_agent_id"] == "lisbeth"
    assert [(t["agent_id"], t["agent_name"]) for t in after_switch["turns"]] == [("saga", "Saga"), ("milton", "Milton")]

    # Non-streaming /turn endpoint also stamps agent_id, agent_name and last_agent_id
    r_non_stream = fresh.post("/api/chats/vault-agent-chat/turn", json={"query": "hello", "ask_tutor": False, "agent_id": "plague"})
    assert r_non_stream.status_code == 200
    ns_body = r_non_stream.json()
    assert ns_body["last_agent_id"] == "plague"
    assert ns_body["turns"][0]["agent_id"] == "plague" and ns_body["turns"][0]["agent_name"] == "Plague"

    # Context endpoint honors explicit agent_id override and session last_agent_id
    ctx_override = fresh.get("/api/chats/team-chat-1/context?free_chat=true&agent_id=plague").json()
    assert ctx_override["context_usage"]["persona_tokens"] > 0

    # Frontend never falls back to live activeAgentName() on finished historical turns
    html = fresh.get("/").text
    assert "escapeHtml(turnAuthorName(turn))" in html
    assert "turn.agent_name || activeAgentName()" not in html
    assert "resolveSessionAgentId" in html
