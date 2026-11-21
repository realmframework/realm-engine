"""Tests for live SSE token streaming, language-aware prompts, and UI feature markers."""

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.cancellation import check_cancelled
from core.contracts import (
    KnowledgeChunk,
    SearchResult,
    TutorConfig,
    WorkspaceConfig,
)
from features.ui import chat_store, query_routes, workspace


def test_stream_turn_emits_retrieval_tokens_done_and_persists_chat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "knowledge_base").mkdir()
    monkeypatch.setattr(workspace, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(chat_store, "CHATS_FILE", tmp_path / "chats.json")
    seen_lang: list[str] = []

    async def fake_stream(
        question: str,
        results: list[SearchResult],
        config: TutorConfig | None = None,
        history: list[tuple[str, str]] | None = None,
        temperature: float | None = None,
        request_id: str | None = None,
    ) -> AsyncIterator[str]:
        if config:
            seen_lang.append(config.response_language)
        for piece in ("Hallo ", "Welt!"):
            check_cancelled()
            await asyncio.sleep(0)
            yield piece

    chunks = [KnowledgeChunk(id="c1", title="Guide — Intro", file_path="guide.md", content="Intro text", tags=[])]
    app = FastAPI()
    app.include_router(
        query_routes.build_router(
            lambda: WorkspaceConfig(language="de"),
            lambda: chunks,
            lambda *_a, **_kw: {"label": "Exact", "intent": "lookup", "routed_query": "Intro", "top_k": 5, "retrieval_mode": "lexical", "rrf_k": 60},
            lambda *_a, **_kw: [SearchResult(chunk=chunks[0], score=0.9)],
            lambda *_a, **_kw: [],
            lambda *_a, **_kw: None,  # type: ignore[arg-type,return-value]
            fake_stream,
        )
    )
    client = TestClient(app)
    res = client.post("/api/chats/stream-1/turn/stream", json={"query": "Intro", "ask_tutor": True, "retrieval_mode": "lexical"})
    assert res.status_code == 200 and "text/event-stream" in res.headers["content-type"]
    body = res.text
    assert "event: retrieval" in body and "event: token" in body and "Hallo " in body and "event: done" in body
    assert seen_lang == ["de"]
    saved = chat_store.get_chat_session("stream-1", chat_store.area_chat_path("knowledge_base"))
    assert saved is not None and saved.turns[0].tutor is not None and saved.turns[0].tutor.answer == "Hallo Welt!"


def test_ui_exposes_streaming_voice_aurora_drag_drop_copy_and_web_search(area_client: TestClient) -> None:
    html = area_client.get("/").text
    for marker in (
        'id="global-drop-overlay"',
        'id="web-search-toggle"',
        'id="web-search-provider"',
        'id="web-search-chat-btn" type="button" hidden',
        'type="checkbox" switch',
        "appearance: base-select",
        "graph-zoom-in",
        "connectAmbientAudio",
        "copyTurnAnswer",
        "runStreamingTurn",
        "bindGlobalDrop",
    ):
        assert marker in html


def test_per_message_web_search_requires_explicit_chat_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    from core import web_search as ws_mod
    from core.contracts import ChatTurnRequest
    from features.ui import query_engine

    called: list[str] = []
    web_chunk = KnowledgeChunk(id="w1", title="Web — Live", file_path="https://example.com", url="https://example.com", content="Live snippet", tags=["web"])
    monkeypatch.setattr(query_engine, "search_web_context", lambda q, cfg: called.append(q) or [SearchResult(chunk=web_chunk, score=0.6)])
    policy = WorkspaceConfig(strict_local_only=False, web_search_enabled=True)
    def route(q: str, **_kw: object) -> dict[str, object]:
        return {"label": "Exact", "intent": "lookup", "routed_query": q, "top_k": 5, "retrieval_mode": "lexical", "rrf_k": 60}

    def local_search(*_a: object, **_kw: object) -> list[SearchResult]:
        return []

    def embed(*_a: object, **_kw: object) -> list[float]:
        return []

    _, off_res, _ = query_engine.retrieve(ChatTurnRequest(query="today news", use_web_search=False), [], [], route, local_search, embed, policy)
    assert off_res == [] and called == []

    _, on_res, _ = query_engine.retrieve(ChatTurnRequest(query="today news", use_web_search=True), [], [], route, local_search, embed, policy)
    assert len(on_res) == 1 and on_res[0].chunk.url == "https://example.com" and called == ["today news"]
    assert ws_mod.search_web_context("blocked", WorkspaceConfig(strict_local_only=True, web_search_enabled=True)) == []


def test_standalone_slash_recipe_with_history_and_agent_color_streaming_markers(area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "slash_area").mkdir()
    monkeypatch.setattr(workspace, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(chat_store, "CHATS_FILE", tmp_path / "chats_slash.json")
    chunks = [KnowledgeChunk(id="c1", title="Intro", file_path="intro.md", content="Hybrid search guide", tags=[])]
    calls: list[str] = []

    async def fake_stream(question: str, results: list[SearchResult], config: TutorConfig | None = None, history: list[tuple[str, str]] | None = None, **_kw: object) -> AsyncIterator[dict[str, object]]:
        calls.append(question)
        yield {"type": "token", "delta": "Question 1: What is hybrid search?"}

    app = FastAPI()
    app.include_router(
        query_routes.build_router(
            lambda: WorkspaceConfig(knowledge_dir="slash_area", active_dirs=["slash_area"]),
            lambda: chunks,
            lambda q, **_kw: {"label": "Exact", "intent": "lookup", "routed_query": q, "top_k": 5, "retrieval_mode": "lexical", "rrf_k": 60},
            lambda q, _c, **_kw: [SearchResult(chunk=chunks[0], score=0.9)] if "hybrid" in q.query.lower() else [],
            lambda *_a, **_kw: [],
            lambda *_a, **_kw: None,  # type: ignore[arg-type,return-value]
            fake_stream,
        )
    )
    client = TestClient(app)
    r1 = client.post("/api/chats/quiz-1/turn/stream", json={"query": "Explain hybrid search", "ask_tutor": True, "retrieval_mode": "lexical"})
    assert r1.status_code == 200 and "Question 1" in r1.text
    r2 = client.post("/api/chats/quiz-1/turn/stream", json={"query": "Quiz — our conversation above", "instruction_prefix": "Quiz me one question at a time: ", "ask_tutor": True, "retrieval_mode": "lexical"})
    assert r2.status_code == 200 and "Question 1" in r2.text and len(calls) == 2
    html = area_client.get("/").text
    for marker in ("turnAuthorColor", "turn-author-heading", "--turn-seed:", "md-body is-streaming", "standaloneRecipeQuery", '"/cards"', '"/gaps"'):
        assert marker in html
    assert "<span class='stream-cursor'" not in html
