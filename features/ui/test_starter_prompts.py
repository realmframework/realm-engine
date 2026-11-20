"""Starter suggestions stay natural for redacted PDFs, empty workspaces and topic fallbacks."""

import re
from pathlib import Path

from fastapi.testclient import TestClient

from core.contracts import KnowledgeChunk
from features.ui.starter_prompts import DEFAULT_IDEAS, build_starter_prompts


def chunk(title: str) -> KnowledgeChunk:
    return KnowledgeChunk(id=title, title=title, file_path="synthetic.md", content="Synthetic content", tags=["finance"])


def test_pdf_pages_and_redacted_titles_use_clean_topic_ideas() -> None:
    chunks = [chunk("CV [REDACTED_NAME] — Page 1"), chunk("CV [REDACTED_NAME] — Page 2"), chunk("Notes — Page 3"), chunk("Page 4 — Overview")]
    prompts = build_starter_prompts(chunks, ["finance", "[REDACTED_NAME]", "Page 5", "context-engineering"])
    assert prompts[:3] == [DEFAULT_IDEAS[0], "What are the main topics covered in finance?", DEFAULT_IDEAS[1]]
    assert "What are the main topics covered in context engineering?" in prompts
    assert not any(re.search(r"\[REDACTED_|\bpage\s+\d+\b", idea, re.IGNORECASE) for idea in prompts)


def test_normal_headings_remain_specific_deduplicated_and_bounded() -> None:
    chunks = [chunk("Architecture — 1. Boundary Design"), chunk("Architecture — 1. Boundary Design"), chunk("Engineering — Overview")]
    prompts = build_starter_prompts(chunks, [])
    assert prompts[:2] == ["Explain Boundary Design in Architecture", "Summarize Engineering"]
    assert len(prompts) == len(set(prompts))
    assert len(build_starter_prompts([chunk(f"Guide — Section {i}") for i in range(30)], [])) == 12
    assert build_starter_prompts([], []) == list(DEFAULT_IDEAS)
    assert build_starter_prompts([chunk("[REDACTED_EMAIL — Overview")], []) == list(DEFAULT_IDEAS)


def test_home_ideas_skip_navigation_and_prefer_different_guides() -> None:
    navigation = chunk("Reading Guide — Reading order").model_copy(update={"tags": ["Navigation"]})
    chunks = [
        navigation,
        chunk("Retrieval — Candidate recall"),
        chunk("Retrieval — Reranking"),
        chunk("Prompting — Output contracts"),
        chunk("Serving — KV cache"),
    ]
    assert build_starter_prompts(chunks, ["navigation"]) == [
        "Explain Candidate recall in Retrieval",
        "Explain Output contracts in Prompting",
        "Explain KV cache in Serving",
        "Explain Reranking in Retrieval",
    ]
    assert build_starter_prompts([navigation], ["navigation"]) == list(DEFAULT_IDEAS)


def test_workspace_payload_uses_sanitized_ideas_without_editing_guides(area_client: TestClient, tmp_path: Path) -> None:
    directory = tmp_path / "knowledge_base"
    original = "# CV [REDACTED_NAME] [REDACTED_NAME]\nTags: finance\n\n## Page 1\nSynthetic content.\n\n## Page 2\nMore synthetic content.\n"
    guide = directory / "redacted.md"
    guide.write_text(original)
    assert area_client.post("/api/workspace", json={"knowledge_dir": "knowledge_base"}).status_code == 200
    response = area_client.get("/api/workspace")
    assert response.status_code == 200
    prompts = response.json()["starter_prompts"]
    assert any("finance" in prompt for prompt in prompts)
    assert all(not re.search(r"\[REDACTED_|\bpage\s+\d+\b", prompt, re.IGNORECASE) for prompt in prompts)
    assert guide.read_text() == original
