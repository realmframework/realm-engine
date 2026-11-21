"""Tests for Phase 3: Chat Branching (Fork), Cross-Examine markup, and Contradiction / Gap Scan."""

from fastapi.testclient import TestClient

from core.contracts import KnowledgeChunk
from core.vault_analysis import analyze_workspace_gaps


def test_vault_gap_analyzer_detects_conflicts_duplicates_and_orphans() -> None:
    shared_body = (
        "Deployment architecture details cover regional failover clusters, automated database snapshots, "
        "TLS certificate rotation schedules, observability dashboards, incident response runbooks, "
        "container image provenance checks, zero downtime canary deployments, and audit log retention."
    )
    chunks = [
        KnowledgeChunk(id="a-1", doc_id="plan_a", title="Plan A — Budget", file_path="plan_a.md", content=f"Budget: $50,000\nLaunch Year: 2025\n{shared_body}", tags=["security", "roadmap"]),
        KnowledgeChunk(id="b-1", doc_id="plan_b", title="Plan B — Budget", file_path="plan_b.md", content=f"Budget: $85,000\nLaunch Year: 2026\n{shared_body}", tags=["security", "roadmap"]),
        KnowledgeChunk(id="c-1", doc_id="ops_c", title="Ops Notes — Details", file_path="ops_c.md", content="Runbook checklist for incident recovery and monitoring.", tags=["security"]),
    ]
    report = analyze_workspace_gaps(chunks)
    conflicts = report["conflicts"]
    duplicates = report["duplicates"]
    orphans = report["orphan_topics"]
    assert isinstance(conflicts, list) and any(c["field"] == "Budget" for c in conflicts)
    assert isinstance(duplicates, list) and len(duplicates) == 1 and duplicates[0]["similarity"] >= 65
    assert isinstance(orphans, list) and any(o["topic"].lower() == "security" for o in orphans)


def test_chat_fork_and_gap_scan_endpoints(area_client: TestClient) -> None:
    assert area_client.post("/api/chats/orig/turn", json={"query": "Turn one", "ask_tutor": False}).status_code == 200
    assert area_client.post("/api/chats/orig/turn", json={"query": "Turn two", "ask_tutor": False}).status_code == 200
    forked = area_client.post("/api/chats/orig/fork", json={"turn_index": 0})
    assert forked.status_code == 200
    session = forked.json()["session"]
    assert session["chat_id"] != "orig" and len(session["turns"]) == 1 and session["turns"][0]["query"] == "Turn one"
    assert "(Branch)" in session["title"]
    assert area_client.get(f"/api/chats/{session['chat_id']}").status_code == 200
    assert len(area_client.get("/api/chats/orig").json()["turns"]) == 2
    assert area_client.post("/api/chats/orig/fork", json={"turn_index": 99}).status_code == 400

    # Gap scan route works cleanly on active workspace and rejects 0-workspace cleanly
    scan = area_client.post("/api/workspace/analyze-gaps")
    assert scan.status_code == 200 and scan.json()["total_guides"] >= 1
    assert area_client.delete("/api/workspace/knowledge_base").status_code == 200
    assert area_client.post("/api/workspace/analyze-gaps").status_code == 400
    html = area_client.get("/").text
    for marker in ('id="cross-examine-modal" closedby="any"', 'id="gap-analysis-modal" closedby="any"', "data-review-turn=", "data-fork-turn="):
        assert marker in html


def test_cross_examine_agent_override_and_instruction_prefix(area_client: TestClient) -> None:
    assert area_client.post("/api/agents/select", json={"agent_id": "plague"}).status_code == 200
    t1 = area_client.post("/api/chats/cx/turn", json={"query": "First question", "ask_tutor": False})
    assert t1.status_code == 200 and t1.json()["turns"][0]["agent_id"] == "plague"
    assert t1.json()["turns"][0]["agent_name"] == "Plague"
    t2 = area_client.post(
        "/api/chats/cx/turn",
        json={
            "query": "Second opinion from Annika — First question",
            "agent_id": "annika",
            "instruction_prefix": "Critically verify Plague's previous answer.",
            "ask_tutor": False,
        },
    )
    assert t2.status_code == 200
    turns = t2.json()["turns"]
    assert turns[0]["agent_name"] == "Plague"
    assert turns[1]["agent_id"] == "annika" and turns[1]["agent_name"] == "Annika"
    assert turns[1]["query"] == "Second opinion from Annika — First question"
    assert "Critically verify" not in turns[1]["query"]
