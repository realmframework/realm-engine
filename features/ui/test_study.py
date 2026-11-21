"""Tests for Phase 4: Active Recall Flashcards and spaced-repetition persistence."""

from pathlib import Path

from fastapi.testclient import TestClient

from core.contracts import KnowledgeChunk
from core.study_cards import extract_study_cards


def test_extract_study_cards_handles_definitions_qa_and_sections() -> None:
    chunks = [
        KnowledgeChunk(
            id="s-1",
            doc_id="rag_101",
            title="RAG 101 — Hybrid Search",
            file_path="rag_101.md",
            content="**RRF**: Reciprocal Rank Fusion merges lexical BM25 and dense cosine rankings.\nQ: Why cache embeddings?\nA: To avoid recomputing vectors for unchanged Markdown files.",
            tags=["rag"],
        )
    ]
    cards = extract_study_cards(chunks)
    assert len(cards) >= 3
    assert any("RRF" in str(c["front"]) for c in cards)
    assert any("Why cache embeddings?" in str(c["front"]) for c in cards)


def test_study_deck_and_spaced_review_endpoints(area_client: TestClient, tmp_path: Path) -> None:
    assert area_client.post(
        "/api/guides/create",
        json={
            "title": "Biology Notes",
            "content": "## Cell Basics\n**Mitochondria**: Generates most of the cell's supply of ATP energy.\n\nQ: What controls genetic expression?\nA: DNA stored in the cell nucleus.\n",
            "tags": "study",
        },
    ).status_code == 200
    deck = area_client.get("/api/study/deck", params={"doc_id": "biology_notes"})
    assert deck.status_code == 200
    cards = deck.json()["cards"]
    assert len(cards) >= 2 and deck.json()["due_count"] == len(cards)
    cid = cards[0]["id"]
    rev = area_client.post("/api/study/review", json={"card_id": cid, "rating": "easy"})
    assert rev.status_code == 200 and rev.json()["review"]["box"] >= 2
    assert (tmp_path / "knowledge_base/study_progress.json").is_file()
    updated = area_client.get("/api/study/deck", params={"doc_id": "biology_notes"}).json()
    assert updated["due_count"] == len(cards) - 1
    assert area_client.post("/api/study/review", json={"card_id": cid, "rating": "invalid"}).status_code == 422
    assert 'id="study-modal" closedby="any"' in area_client.get("/").text

    # Add & delete custom cards + AI deck parser
    added = area_client.post("/api/study/cards", json={"doc_id": "biology_notes", "front": "What does ATP stand for?", "back": "Adenosine triphosphate."})
    assert added.status_code == 200 and added.json()["deck_mode"] == "ai"
    custom_id = added.json()["cards"][0]["id"]
    assert added.json()["cards"][0]["front"] == "What does ATP stand for?"
    deleted = area_client.delete(f"/api/study/cards/{custom_id}", params={"doc_id": "biology_notes"})
    assert deleted.status_code == 200 and all(c["id"] != custom_id for c in deleted.json()["cards"])


def test_ai_flashcard_parser_and_generate_endpoint(area_client: TestClient, monkeypatch: object) -> None:
    from collections.abc import AsyncIterator

    from core.study_ai import parse_generated_cards
    from features.ui import app as ui_app

    parsed = parse_generated_cards(
        '```json\n[{"front": "Why use RRF?", "back": "It combines BM25 and vector ranks without score calibration."}]\n```',
        scope="doc:rag",
        source_label="RAG Guide",
    )
    assert len(parsed) == 1 and parsed[0]["front"] == "Why use RRF?"

    async def fake_stream(*_args: object, **_kwargs: object) -> AsyncIterator[dict[str, object]]:
        yield {"type": "token", "delta": '[{"front": "What is hybrid search?", "back": "Combining lexical BM25 with semantic embeddings."}, {"front": "Why keep data local?", "back": "To guarantee privacy and offline speed."}]'}

    import pytest
    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    monkeypatch.setattr(ui_app, "stream_messages_events", fake_stream)
    # Build local client using patched stream_messages_events
    local = ui_app._build_local_app()
    local_client = TestClient(local)
    gen = local_client.post("/api/study/generate", json={"count": 5, "style": "exam", "provider": "ollama", "model": "qwen3:8b"})
    assert gen.status_code == 200
    data = gen.json()
    assert data["deck_mode"] == "ai" and len(data["cards"]) == 2
    assert data["cards"][0]["front"] == "What is hybrid search?"
