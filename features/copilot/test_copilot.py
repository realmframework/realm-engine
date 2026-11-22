"""Unit & integration tests for the Context-Aware REALM Copilot slice."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core import agent_personas
from core.contracts import WorkspaceConfig
from core.copilot_contracts import CopilotChatRequest, CopilotContext, CopilotMessage
from features.copilot import router as copilot_router
from features.copilot import service


def test_parse_copilot_document_patch_and_readonly_guard() -> None:
    doc = "# API Reference\n\n## Endpoints\n- GET /api/guides\n"
    raw = (
        "I can add a rate-limiting section to **API.md**.\n\n"
        '<copilot_action>{"kind":"update_document","title":"Add Rate Limits to API.md","summary":"Appends rate limit section.","payload":{"doc_id":"doku/API","append_text":"## Rate Limits\\n100 req/min per client."}}</copilot_action>'
    )
    editable_ctx = CopilotContext(view="file", doc_id="doku/API", filename="API.md", doc_content=doc, doc_readonly=False)
    reply, actions = service.parse_copilot_response(raw, editable_ctx)
    assert "<copilot_action>" not in reply and "rate-limiting" in reply
    assert len(actions) == 1
    assert actions[0].kind == "update_document"
    assert "## Rate Limits" in str(actions[0].payload["content"])
    assert "## Rate Limits" in actions[0].diff_after

    patch_raw = (
        "Updated endpoint description.\n"
        '<copilot_action>{"kind":"update_document","title":"Clarify endpoint","summary":"Refines bullet.","payload":{"find_text":"- GET /api/guides","replace_text":"- GET /api/guides (returns indexed guides)"}}</copilot_action>'
    )
    _, patch_actions = service.parse_copilot_response(patch_raw, editable_ctx)
    assert len(patch_actions) == 1
    assert patch_actions[0].diff_before == "- GET /api/guides"
    assert "(returns indexed guides)" in patch_actions[0].diff_after

    ro_ctx = editable_ctx.model_copy(update={"doc_readonly": True})
    _, ro_actions = service.parse_copilot_response(raw, ro_ctx)
    assert ro_actions == []


def test_parse_copilot_task_agent_and_workflow_actions() -> None:
    raw = (
        "Proposed 4 updates.\n"
        '<copilot_action>{"kind":"create_task","title":"Create QA task","summary":"Adds QA task.","payload":{"title":"Run E2E tests","priority":"critical","due_date":"2026-12-01"}}</copilot_action>'
        '<copilot_action>{"kind":"create_event","title":"Schedule Review","summary":"Adds event.","payload":{"title":"API Sync","date":"2026-12-02","kind":"meeting"}}</copilot_action>'
        '<copilot_action>{"kind":"upsert_agent","title":"Create Auditor","summary":"Adds security auditor.","payload":{"name":"Auditor","role":"Security","palette":"invalid_pal","instructions":"Check secrets."}}</copilot_action>'
        '<copilot_action>{"kind":"upsert_workflow","title":"Build Triage Flow","summary":"Adds gateway workflow.","payload":{"name":"Triage","nodes":[{"id":"n1","kind":"trigger","label":"Start"},{"id":"n2","kind":"condition","label":"Urgent?"}],"edges":[{"source":"n1","target":"n2","branch":"default"}]}}</copilot_action>'
        '<copilot_action>{not valid json}</copilot_action>'
    )
    reply, actions = service.parse_copilot_response(raw, CopilotContext(view="work"))
    assert "Proposed 4 updates." in reply
    assert [a.kind for a in actions] == ["create_task", "create_event", "upsert_agent", "upsert_workflow"]
    assert actions[0].payload["priority"] == "medium"
    assert actions[1].payload["kind"] == "event"
    assert actions[2].payload["palette"] == "realm"
    assert len(actions[3].payload["nodes"]) == 2  # type: ignore[arg-type]


def test_copilot_stream_route_hides_action_xml_and_emits_done(tmp_path: Path) -> None:
    cfg = WorkspaceConfig(app_title="Copilot Test", knowledge_dir="", active_dirs=[], strict_local_only=True)
    agent_personas.save_agent(
        tmp_path,
        name="Security Hawk",
        role="Auditor",
        palette="lisbeth",
        model_provider="ollama",
        model_name="qwen3.5:9b",
        temperature=0.1,
        instructions="Always highlight threat models first.",
    )
    captured_sys: list[str] = []
    captured_models: list[str] = []

    async def fake_stream(msgs: list[dict[str, str]], tcfg: object, **_kw: object) -> AsyncIterator[dict[str, object]]:
        captured_sys.append(msgs[0]["content"])
        captured_models.append(str(getattr(tcfg, "model", "")))
        chunks = [
            "Here is a ",
            "proposed task.\n<copi",
            'lot_action>{"kind":"create_task","title":"Add Review Task","summary":"Creates a review item.","payload":{"title":"Review API spec","priority":"high"}}</copilot_action>',
        ]
        for ch in chunks:
            yield {"type": "token", "delta": ch}

    app = FastAPI()
    app.include_router(copilot_router.build_router(lambda: cfg, fake_stream, lambda: tmp_path))
    client = TestClient(app)
    req = CopilotChatRequest(
        messages=[CopilotMessage(role="user", content="Add a task to review the API spec")],
        context=CopilotContext(view="file", doc_id="API", filename="API.md", doc_content="# API\n"),
        provider="ollama",
        model="qwen3:8b",
        agent_id="security_hawk",
        format_id="executive_brief",
    )
    res = client.post("/api/copilot/chat/stream", json=req.model_dump())
    assert res.status_code == 200
    events: list[tuple[str, dict[str, object]]] = []
    cur_ev = ""
    for line in res.text.splitlines():
        if line.startswith("event: "):
            cur_ev = line.removeprefix("event: ").strip()
        elif line.startswith("data: "):
            events.append((cur_ev, json.loads(line.removeprefix("data: "))))
    token_text = "".join(str(d.get("delta") or "") for ev, d in events if ev == "token")
    assert "<copilot_action>" not in token_text and "proposed task." in token_text
    assert captured_models == ["qwen3.5:9b"]
    assert "Security Hawk" in captured_sys[0] and "threat models" in captured_sys[0]
    meta = next(d for ev, d in events if ev == "meta")
    assert meta["agent_name"] == "Security Hawk" and meta["model"] == "qwen3.5:9b" and meta["model_pinned"] is True
    done = next(d for ev, d in events if ev == "done")
    actions = done["actions"]
    assert isinstance(actions, list) and len(actions) == 1 and actions[0]["kind"] == "create_task"
