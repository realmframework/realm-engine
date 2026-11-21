"""Unit tests for Output Formats Studio, Context Meter/Compaction, and Vector PDF Export."""

from pathlib import Path

import pytest

from core.context_meter import (
    active_history_for_session,
    build_compaction_messages,
    compute_context_usage,
)
from core.contracts import ChatSession, ChatTurn, TutorResponse
from core.output_formats import (
    build_format_instruction,
    delete_custom_format,
    get_format,
    list_formats,
    save_custom_format,
)
from core.pdf_export import render_chat_pdf, render_markdown_pdf


def test_builtin_and_custom_output_formats_crud(tmp_path: Path) -> None:
    builtins = list_formats(tmp_path)
    ids = {f.id for f in builtins}
    assert {"ireb_srs", "user_stories", "moscow", "adr", "lisbeth_dossier", "exec_4w", "meeting_actions"} <= ids

    created = save_custom_format(
        tmp_path,
        name="Stakeholder 4W Paper",
        sections=["When", "Who", "What", "How Much", "Risks"],
        category="Requirements",
        description="Compact 4W paper",
        instructions="Be crisp and factual.",
    )
    assert created.id == "stakeholder_4w_paper" and created.builtin is False
    assert get_format(tmp_path, created.id) is not None
    instr = build_format_instruction(created, extra_note="Focus on Q4 launch")
    assert "## When" in instr and "## How Much" in instr and "Q4 launch" in instr

    with pytest.raises(ValueError, match="Built-in"):
        delete_custom_format(tmp_path, "ireb_srs")
    assert delete_custom_format(tmp_path, created.id) is True
    assert get_format(tmp_path, created.id) is None


def test_context_meter_tracks_compaction_and_clear_boundaries() -> None:
    turns = [
        ChatTurn(query=f"Question {i} " + ("detail " * 25), created_at="2026-11-20T00:00:00Z", tutor=TutorResponse(answer="Answer " * 40, cited_titles=[], knowledge_gap_detected=False, recommended_topics=[]))
        for i in range(4)
    ]
    session = ChatSession(chat_id="c1", title="Req Session", updated_at="2026-11-20T00:00:00Z", turns=turns, attached_notes=[{"name": "notes.md", "content": "Note " * 60}])
    full = compute_context_usage(session, "openai", "gpt-4o-mini")
    assert full["max_tokens"] == 128_000 and int(str(full["used_tokens"])) > 400 and full["turns_in_context"] == 4

    msgs = build_compaction_messages(session, "de")
    assert "German" in msgs[0]["content"] and "notes.md" in msgs[1]["content"]

    compacted = session.model_copy(update={"compacted_summary": "Key decisions only.", "context_cleared_at": 3})
    summary, pairs, notes = active_history_for_session(compacted)
    assert summary == "Key decisions only." and len(pairs) == 1 and len(notes) == 1
    after = compute_context_usage(compacted, "openai", "gpt-4o-mini")
    assert int(str(after["used_tokens"])) < int(str(full["used_tokens"])) and after["is_compacted"] is True


def test_pdf_export_renders_unicode_markdown_tables_and_full_chats() -> None:
    md = (
        "# Anforderungsdokument — Überblick\n\n"
        "## Anforderungen\n"
        "- FR-01: Prüfung für **Müller** & Español `¿Cómo estás?`\n\n"
        "| ID | Priority | Owner |\n| --- | --- | --- |\n| FR-01 | Must | Lisbeth |\n\n"
        "```yaml\nstatus: approved\n```\n"
    )
    pdf = render_markdown_pdf("Requirements Spec", md, citations=["Handbook — RAG Architecture"])
    assert pdf.startswith(b"%PDF-") and len(pdf) > 900

    session = ChatSession(
        chat_id="c2", title="Interview Prep", updated_at="2026-11-20T12:00:00Z",
        turns=[ChatTurn(query="Draft requirements", created_at="2026-11-20T12:00:00Z", format_name="Requirements Spec", tutor=TutorResponse(answer=md, cited_titles=["Spec Guide"], knowledge_gap_detected=False, recommended_topics=[]))],
    )
    chat_pdf = render_chat_pdf(session)
    assert chat_pdf.startswith(b"%PDF-") and len(chat_pdf) > 900
