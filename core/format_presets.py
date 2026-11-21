"""Curated Requirements Engineering, Investigation, and Executive output format blueprints."""

from pydantic import Field

from core.contracts import StrictModel


class OutputFormat(StrictModel):
    id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=80)
    category: str = Field(default="Custom", max_length=32)
    description: str = Field(default="", max_length=220)
    sections: list[str] = Field(default_factory=list, min_length=1, max_length=16)
    instructions: str = Field(default="", max_length=1200)
    builtin: bool = False


BUILTIN_FORMATS: tuple[OutputFormat, ...] = (
    OutputFormat(
        id="ireb_srs",
        name="Requirements Spec (IEEE / IREB SRS)",
        category="Requirements",
        description="Structured software requirements with EARS syntax, priorities, NFRs, and open gaps.",
        sections=[
            "1. Context & Scope",
            "2. Stakeholders & User Roles",
            "3. Functional Requirements (ID · Priority · EARS Statement)",
            "4. Non-Functional Requirements (Security, Performance, Usability, Compliance)",
            "5. Constraints & Assumptions",
            "6. Open Questions & Missing Information",
        ],
        instructions="Assign sequential IDs (FR-01, NFR-01) and MoSCoW priorities. Write functional requirements using EARS syntax ('When <trigger>, the system shall <behavior>'). Flag missing details explicitly instead of inventing facts.",
        builtin=True,
    ),
    OutputFormat(
        id="user_stories",
        name="Agile User Stories & Gherkin AC",
        category="Requirements",
        description="Sprint-ready User Stories with Given/When/Then acceptance criteria and edge cases.",
        sections=["Epic Overview", "Target Personas", "User Stories (As a / I want / So that)", "Acceptance Criteria (Given / When / Then)", "Edge Cases & Negative Scenarios", "Definition of Done & Dependencies"],
        instructions="Group stories logically, write concrete testable Gherkin scenarios (Given / When / Then) for each story, and call out edge cases or ambiguities.",
        builtin=True,
    ),
    OutputFormat(
        id="moscow",
        name="MoSCoW Scope & Priority Matrix",
        category="Requirements",
        description="Prioritize scope cleanly into Must, Should, Could, and Won't Have with trade-offs.",
        sections=["Objective & Release Goal", "Must Have", "Should Have", "Could Have", "Won't Have (This Release)", "Dependencies & Trade-off Risks"],
        instructions="Present priorities concisely using bulleted items or a Markdown table with rationale for each classification.",
        builtin=True,
    ),
    OutputFormat(
        id="adr",
        name="Architecture Decision Record (ADR)",
        category="Engineering",
        description="Capture context, architectural decision, evaluated alternatives, and consequences.",
        sections=["Status & Date", "Context & Problem Statement", "Decision", "Alternatives Considered", "Positive & Negative Consequences", "Follow-up Actions"],
        instructions="Be objective and concrete. Compare at least two alternatives with clear trade-offs grounded in the conversation.",
        builtin=True,
    ),
    OutputFormat(
        id="lisbeth_dossier",
        name="Lisbeth's Investigation Dossier (5W1H)",
        category="Investigation",
        description="Forensic synthesis: entities, timeline, verified evidence, contradictions, and leads.",
        sections=["Executive Summary", "Key Entities (Who · What · Where · When)", "Chronological Timeline", "Verified Evidence & Source Trail", "Contradictions & Knowledge Gaps", "Next Leads to Investigate"],
        instructions="Adopt a sharp, factual investigative analyst tone. Separate confirmed facts from assumptions and explicitly mark contradictions or unverified claims.",
        builtin=True,
    ),
    OutputFormat(
        id="blomkvist_article",
        name="Blomkvist's Investigative Article",
        category="Editorial",
        description="Publication-ready deep-dive report turning raw notes and sources into clear journalism.",
        sections=["Headline & Standfirst", "The Core Story (What Happened & Why It Matters)", "Verified Facts & Source Evidence", "Key Voices & Perspectives", "Counterarguments & Context", "Impact & Open Questions"],
        instructions="Write with crisp, credible investigative journalism clarity. Ground every claim in the provided material, avoid hype, and separate confirmed facts from open questions.",
        builtin=True,
    ),
    OutputFormat(
        id="milton_security",
        name="Milton Security Threat & Risk Assessment",
        category="Security",
        description="Threat model, risk register table, GDPR/DSGVO checkpoints, and concrete mitigations.",
        sections=["Assets & Scope Protected", "Threat Actors & Attack Surface", "Risk Matrix (ID · Threat · Likelihood · Impact · Mitigation)", "Security & Privacy Controls (GDPR / DSGVO)", "Residual Risks & Hardening Plan"],
        instructions="Render the Risk Matrix as a Markdown table with columns | ID | Threat / Risk | Likelihood | Impact | Mitigation |. Prioritize concrete, testable defenses.",
        builtin=True,
    ),
    OutputFormat(
        id="erika_brief",
        name="Erika's Editorial & Stakeholder Brief",
        category="Strategy",
        description="Executive positioning memo with core thesis, proof points, objections, and rollout plan.",
        sections=["Strategic Thesis & Bottom Line", "Target Audience & Stakeholder Impact", "Key Narrative Pillars & Proof Points", "Anticipated Objections & Responses", "Rollout Plan & Approval Decisions"],
        instructions="Adopt a decisive executive-editor tone. Lead with the core thesis, substantiate claims with evidence from the chat, and frame decisions clearly.",
        builtin=True,
    ),
    OutputFormat(
        id="annika_legal",
        name="Annika's Contract & Legal Review Memo",
        category="Legal",
        description="Structured issue-spotting brief for contracts, policies, SLAs, red flags, and redlines.",
        sections=["Matter Summary & Context", "Key Obligations & Deadlines", "Red Flags, Liability & Ambiguities", "Data Protection & Compliance Checkpoints", "Recommended Redlines & Negotiation Points", "Questions for Legal Counsel"],
        instructions="Write in clear, structured legal-review memo style. Flag ambiguous clauses, asymmetric risks, or missing obligations. End with a one-line note that this is analytical preparation, not formal legal advice.",
        builtin=True,
    ),
    OutputFormat(
        id="plague_postmortem",
        name="Plague's Root-Cause & Incident Postmortem",
        category="Engineering",
        description="Blameless technical debugging report with timeline, 5-Whys root cause, and fixes.",
        sections=["Incident / Issue Summary & Impact", "Detection & Timeline", "Root Cause Analysis (5 Whys)", "Immediate Fix & Workaround", "Permanent Corrective Actions (Owner · Priority)", "Verification & Prevention Checklist"],
        instructions="Keep the tone blameless, deeply technical, and evidence-driven. Separate surface symptoms from true root causes and list concrete, verifiable follow-ups.",
        builtin=True,
    ),
    OutputFormat(
        id="palmgren_review",
        name="Palmgren's Structured Review & Mentoring Plan",
        category="Advisory",
        description="Candid strengths/gaps critique, strategic options, and step-by-step improvement plan.",
        sections=["Overall Assessment & Strengths", "Critical Gaps & Blind Spots", "Strategic Options & Trade-offs", "Step-by-Step Improvement Roadmap", "Key Questions to Prepare For"],
        instructions="Adopt a calm, fair, incisive mentor voice. Balance genuine strengths with honest gap analysis and actionable next steps.",
        builtin=True,
    ),
    OutputFormat(
        id="exec_4w",
        name="Executive Brief (When / Who / What / How Much)",
        category="Business",
        description="Decision-ready 1-page summary covering Who, What, When, How Much, and Risks.",
        sections=["Executive Summary", "Who (Owner & Stakeholders)", "What (Scope & Deliverables)", "When (Timeline & Milestones)", "How Much (Cost, Effort & Resources)", "Key Risks & Next Steps"],
        instructions="Keep every section crisp and scannable for leadership. Mark any unknown numbers or dates as 'TBD — needs confirmation'.",
        builtin=True,
    ),
    OutputFormat(
        id="meeting_actions",
        name="Meeting Notes → Decisions & Actions",
        category="Product",
        description="Distill raw notes into TL;DR, locked decisions, action-item table, and open items.",
        sections=["TL;DR", "Key Decisions Made", "Action Items (Owner · Task · Due Date)", "Open Questions & Parking Lot"],
        instructions="Render Action Items as a clean Markdown table with columns | Owner | Action | Due Date | Status |.",
        builtin=True,
    ),
)
