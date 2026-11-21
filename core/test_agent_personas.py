"""Unit tests for file-first persona.md Agent Team presets, codec, and safety boundaries."""

from pathlib import Path

import pytest

from core import agent_personas
from core.persona_codec import build_persona_prompt, parse_persona_md, render_persona_md


def test_default_team_seeds_eight_persona_md_files(tmp_path: Path) -> None:
    agents = agent_personas.list_agents(tmp_path)
    ids = [a.id for a in agents]
    assert ids == ["saga", "lisbeth", "blomkvist", "plague", "milton", "erika", "annika", "palmgren"]
    for agent in agents:
        pfile = tmp_path / "agents" / agent.id / "persona.md"
        assert pfile.is_file()
        raw = pfile.read_text(encoding="utf-8")
        assert f"id: {agent.id}" in raw and "## Analytical Lens" in raw
        reparsed = parse_persona_md(raw, agent.id, str(pfile))
        assert reparsed is not None and reparsed.name == agent.name and not reparsed.customized


def test_custom_agent_edit_raw_markdown_delete_and_restore(tmp_path: Path) -> None:
    created = agent_personas.save_agent(
        tmp_path,
        name="IREB Examiner",
        role="Requirements Reviewer",
        tagline="Tests EARS syntax and testable acceptance criteria.",
        palette="dragon",
        default_format="ireb_srs",
        temperature=0.15,
        instructions="## Analytical Lens\nCheck every requirement for ambiguity and testability.",
    )
    assert created.id == "ireb_examiner" and not created.builtin
    assert (tmp_path / "agents" / "ireb_examiner" / "persona.md").is_file()

    # Customize a built-in agent via raw persona.md
    lisbeth = agent_personas.get_agent(tmp_path, "lisbeth")
    edited_md = render_persona_md(lisbeth).replace("Forensic Analyst", "Lead Forensic Investigator")
    updated = agent_personas.save_agent(tmp_path, agent_id="lisbeth", raw_markdown=edited_md)
    assert updated.role == "Lead Forensic Investigator" and updated.customized is True

    # Reset restores original built-in persona.md
    reset = agent_personas.reset_agent(tmp_path, "lisbeth")
    assert reset.role == "Forensic Analyst" and reset.customized is False

    # Deleting a built-in keeps it removed until explicit Restore Default Team
    assert agent_personas.delete_agent(tmp_path, "blomkvist") is True
    assert "blomkvist" not in {a.id for a in agent_personas.list_agents(tmp_path)}
    restored = agent_personas.restore_default_team(tmp_path)
    restored_ids = {a.id for a in restored}
    assert "blomkvist" in restored_ids and "ireb_examiner" in restored_ids


def test_cannot_delete_last_agent_and_prompt_keeps_craft_guardrail(tmp_path: Path) -> None:
    for aid in ("lisbeth", "blomkvist", "plague", "milton", "erika", "annika", "palmgren"):
        assert agent_personas.delete_agent(tmp_path, aid) is True
    with pytest.raises(ValueError, match="at least one"):
        agent_personas.delete_agent(tmp_path, "saga")

    agent, prompt = agent_personas.active_persona_prompt(tmp_path, "saga")
    assert agent.id == "saga"
    assert "[ACTIVE AGENT PERSONA: Saga" in prompt
    assert "never break into fictional cosplay" in prompt
    assert build_persona_prompt(None) == ""
