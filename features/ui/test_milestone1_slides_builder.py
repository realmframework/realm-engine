"""Integration tests for Milestone 1: Interactive Agent Builder and Workspace Slide Export."""

from collections.abc import AsyncIterator
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from pptx import Presentation

from features.ui import agent_builder_routes
from features.ui import app as ui_app


def test_export_slides_from_workspace_guide_and_raw_markdown(area_client: TestClient) -> None:
    guides = area_client.get("/api/guides").json()
    assert guides, "Expected seeded workspace guide"
    doc_id = guides[0]["doc_id"]

    res_pptx = area_client.post("/api/export/slides", json={"doc_id": doc_id, "format": "pptx"})
    assert res_pptx.status_code == 200 and res_pptx.content[:2] == b"PK"
    prs = Presentation(BytesIO(res_pptx.content))
    assert len(prs.slides) >= 2

    res_pdf = area_client.post("/api/export/slides", json={"doc_id": doc_id, "format": "pdf"})
    assert res_pdf.status_code == 200 and res_pdf.content.startswith(b"%PDF-")

    formats = area_client.get("/api/formats").json()["formats"]
    assert any(f["id"] == "presentation_deck" for f in formats)


def test_interactive_agent_builder_drafts_validates_lock_and_saves(area_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    # Local-only lock blocks cloud provider in Agent Builder
    blocked = area_client.post(
        "/api/agents/builder/chat",
        json={"messages": [{"role": "user", "content": "Help me manage projects"}], "provider": "openai"},
    )
    assert blocked.status_code == 403

    # Mock LLM stream to return a structured <agent_draft>
    async def fake_stream(messages: list[dict[str, str]], *_a: object, **_kw: object) -> AsyncIterator[dict[str, object]]:
        yield {
            "type": "token",
            "delta": (
                "Great! Here is your personal Project Clarity Coach.\n\n"
                '<agent_draft>{"name":"Clara","role":"Project & Impact Coach","tagline":"Turns messy notes into clear plans and impact logs.",'
                '"palette":"harriet","default_format":"presentation_deck","temperature":0.25,'
                '"instructions":"## Analytical Lens\\nFocus on clarity and measurable outcomes.\\n\\n## Boundaries\\nNever invent metrics."}</agent_draft>'
            ),
        }

    # Build lightweight isolated app router using our fake_stream to test builder + save end-to-end
    from fastapi import FastAPI

    from features.ui import agent_routes

    mini = FastAPI()
    mini.include_router(agent_builder_routes.build_router(lambda: ui_app.WORKSPACE_CONFIG, fake_stream))
    mini.include_router(agent_routes.build_router(lambda: ui_app.WORKSPACE_CONFIG, ui_app._set_workspace_config))
    mini_client = TestClient(mini)

    res = mini_client.post(
        "/api/agents/builder/chat",
        json={"messages": [{"role": "user", "content": "Build me a friendly German/English project coach who turns notes into slides"}]},
    )
    assert res.status_code == 200
    body = res.json()
    assert "Project Clarity Coach" in body["reply"]
    draft = body["draft"]
    assert draft is not None and draft["name"] == "Clara" and draft["palette"] == "harriet" and draft["default_format"] == "presentation_deck"

    saved = mini_client.post("/api/agents", json=draft)
    assert saved.status_code == 200 and saved.json()["agent"]["name"] == "Clara"
    team = mini_client.get("/api/agents").json()["agents"]
    assert any(a["name"] == "Clara" for a in team)


def test_agent_builder_force_draft_falls_back_gracefully_when_offline() -> None:
    from fastapi import FastAPI

    async def failing_stream(*_a: object, **_kw: object) -> AsyncIterator[dict[str, object]]:
        yield {"type": "error", "code": 503, "detail": "Offline"}

    mini = FastAPI()
    mini.include_router(agent_builder_routes.build_router(lambda: ui_app.WORKSPACE_CONFIG, failing_stream))
    client = TestClient(mini)
    res = client.post(
        "/api/agents/builder/chat",
        json={"messages": [{"role": "user", "content": "Help me document project impact and ROI"}], "force_draft": True},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["fallback"] is True and body["draft"] is not None and body["draft"]["instructions"]


def test_ui_exposes_milestone1_agent_builder_and_slides_controls(area_client: TestClient) -> None:
    html = area_client.get("/").text
    for marker in (
        'id="agent-tab-builder"',
        'id="agent-builder-pane"',
        'id="agent-builder-input"',
        'id="ab-draft-btn"',
        "exportTurnSlides",
        "exportGuideSlides",
        "chat_exp_pptx",
        "chat_exp_slides_pdf",
    ):
        assert marker in html
