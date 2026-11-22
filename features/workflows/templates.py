"""Four built-in ready-to-use local workflow templates for solo knowledge & project work."""

from core.workflow_contracts import WorkflowDefinition, WorkflowEdge, WorkflowNode


def starter_templates(now: str) -> list[WorkflowDefinition]:
    return [
        WorkflowDefinition(
            id="tpl_report_to_slides",
            name="Report -> Fact-Check (Lisbeth) -> Executive Slides & Tasks",
            description="Search your documents, verify key claims with Lisbeth, generate an executive .pptx deck, and add action items to your Kanban Board.",
            enabled=True,
            trigger_kind="manual",
            schedule_minutes=0,
            nodes=[
                WorkflowNode(id="n1", kind="trigger", label="Start with Topic or Report", x=24, y=126, config={"trigger_kind": "manual"}),
                WorkflowNode(id="n2", kind="vault_search", label="Search Workspace Vault", x=246, y=126, config={"query": "{{input}}", "top_k": 5}),
                WorkflowNode(id="n3", kind="run_agent", label="Fact-Check & Distill (Lisbeth)", x=468, y=126, config={"agent_id": "lisbeth", "prompt": "Fact-check and distill the strongest executive points and concrete next steps from this context:\n\n{{prev}}"}),
                WorkflowNode(id="n4", kind="generate_slides", label="Generate Executive Slides (.pptx)", x=694, y=42, config={"title": "Executive Brief: {{input}}", "output_format": "pptx"}),
                WorkflowNode(id="n5", kind="extract_tasks", label="Add Action Tasks to Board", x=694, y=212, config={"project_id": ""}),
            ],
            edges=[
                WorkflowEdge(id="e1", source="n1", target="n2"),
                WorkflowEdge(id="e2", source="n2", target="n3"),
                WorkflowEdge(id="e3", source="n3", target="n4"),
                WorkflowEdge(id="e4", source="n3", target="n5"),
            ],
            created_at=now,
            updated_at=now,
        ),
        WorkflowDefinition(
            id="tpl_weekly_review",
            name="Weekly Review -> Wirksamkeit & ROI Draft",
            description="Gather notes from the week, synthesize accomplishments with Saga, save a Weekly Review guide, and record a draft Wirksamkeit impact entry.",
            enabled=True,
            trigger_kind="schedule",
            schedule_minutes=10080,
            nodes=[
                WorkflowNode(id="n1", kind="trigger", label="Weekly Schedule Trigger", x=24, y=126, config={"trigger_kind": "schedule", "interval_minutes": 10080}),
                WorkflowNode(id="n2", kind="vault_search", label="Gather Recent Workspace Notes", x=246, y=126, config={"query": "{{input}} weekly progress outcomes", "top_k": 6}),
                WorkflowNode(id="n3", kind="run_agent", label="Synthesize Outcomes (Saga)", x=468, y=126, config={"agent_id": "saga", "prompt": "Summarize what was accomplished this week, what concrete effect it created, and what to prioritize next:\n\n{{prev}}"}),
                WorkflowNode(id="n4", kind="log_impact", label="Log Draft Wirksamkeit Entry", x=694, y=42, config={"outcome_tag": "milestone"}),
                WorkflowNode(id="n5", kind="save_guide", label="Save Weekly Review Guide", x=694, y=212, config={"title": "Weekly Review Summary", "subfolder": "reviews"}),
            ],
            edges=[
                WorkflowEdge(id="e1", source="n1", target="n2"),
                WorkflowEdge(id="e2", source="n2", target="n3"),
                WorkflowEdge(id="e3", source="n3", target="n4"),
                WorkflowEdge(id="e4", source="n3", target="n5"),
            ],
            created_at=now,
            updated_at=now,
        ),
        WorkflowDefinition(
            id="tpl_meeting_notes",
            name="Meeting Notes -> Summary Guide & Kanban Tasks",
            description="Turn raw meeting notes into a crisp structured summary saved to your Library plus actionable Kanban cards automatically.",
            enabled=True,
            trigger_kind="file_imported",
            schedule_minutes=0,
            nodes=[
                WorkflowNode(id="n1", kind="trigger", label="On Meeting Notes Added", x=36, y=120, config={"trigger_kind": "file_imported"}),
                WorkflowNode(id="n2", kind="run_agent", label="Structure Decisions & Follow-Ups", x=310, y=120, config={"agent_id": "saga", "prompt": "Turn these meeting notes into: 1) Key Decisions, 2) Open Questions, 3) Clear Action Items with next steps:\n\n{{input}}"}),
                WorkflowNode(id="n3", kind="save_guide", label="Save Meeting Summary Guide", x=590, y=46, config={"title": "Meeting Summary", "subfolder": "meetings"}),
                WorkflowNode(id="n4", kind="extract_tasks", label="Create Follow-Up Kanban Tasks", x=590, y=206, config={"project_id": ""}),
            ],
            edges=[
                WorkflowEdge(id="e1", source="n1", target="n2"),
                WorkflowEdge(id="e2", source="n2", target="n3"),
                WorkflowEdge(id="e3", source="n2", target="n4"),
            ],
            created_at=now,
            updated_at=now,
        ),
        WorkflowDefinition(
            id="tpl_research_debate",
            name="Research Deep-Dive -> Multi-Agent Debate -> Dossier",
            description="Retrieve workspace sources, then chain Saga (synthesis) -> Plague (critical review) -> Lisbeth (evidence check) into a final dossier.",
            enabled=True,
            trigger_kind="manual",
            schedule_minutes=0,
            nodes=[
                WorkflowNode(id="n1", kind="trigger", label="Research Question", x=36, y=120, config={"trigger_kind": "manual"}),
                WorkflowNode(id="n2", kind="vault_search", label="Retrieve Vault Passages", x=255, y=120, config={"query": "{{input}}", "top_k": 6}),
                WorkflowNode(id="n3", kind="run_agent", label="1. Draft Analysis (Saga)", x=474, y=46, config={"agent_id": "saga", "prompt": "Write a structured first-pass analysis on '{{input}}' using these passages:\n\n{{prev}}"}),
                WorkflowNode(id="n4", kind="run_agent", label="2. Stress-Test & Gaps (Plague)", x=474, y=214, config={"agent_id": "plague", "prompt": "Critique this analysis for blind spots, edge cases, and practical risks:\n\n{{prev}}"}),
                WorkflowNode(id="n5", kind="run_agent", label="3. Final Evidence Check (Lisbeth)", x=710, y=120, config={"agent_id": "lisbeth", "prompt": "Synthesize the strongest verified conclusions into a clean executive dossier:\n\n{{prev}}"}),
                WorkflowNode(id="n6", kind="save_guide", label="Save Research Dossier", x=940, y=120, config={"title": "Research Dossier", "subfolder": "research"}),
            ],
            edges=[
                WorkflowEdge(id="e1", source="n1", target="n2"),
                WorkflowEdge(id="e2", source="n2", target="n3"),
                WorkflowEdge(id="e3", source="n3", target="n4"),
                WorkflowEdge(id="e4", source="n4", target="n5"),
                WorkflowEdge(id="e5", source="n5", target="n6"),
            ],
            created_at=now,
            updated_at=now,
        ),
    ]


def template_catalog(now: str) -> list[dict[str, object]]:
    return [
        {
            "id": tpl.id,
            "name": tpl.name,
            "description": tpl.description,
            "trigger_kind": tpl.trigger_kind,
            "node_count": len(tpl.nodes),
        }
        for tpl in starter_templates(now)
    ]
