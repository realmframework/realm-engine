"""Tests for cooperative and live TCP socket cancellation of in-flight AI generations."""

import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.cancellation import (
    begin_request,
    cancel_request,
    check_cancelled,
    end_request,
    post_cancellable,
)
from core.contracts import (
    KnowledgeChunk,
    SearchResult,
    TutorConfig,
    TutorResponse,
    WorkspaceConfig,
)
from features.tutor_agent.service import ask_tutor
from features.ui import chat_store, query_routes, workspace


def test_post_cancellable_closes_live_tcp_socket_immediately() -> None:
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    port = srv.getsockname()[1]
    srv.listen(1)
    connected = threading.Event()
    server_saw_close = threading.Event()

    def _serve() -> None:
        conn, _ = srv.accept()
        conn.recv(4096)
        connected.set()
        while conn.recv(1024):
            pass
        server_saw_close.set()
        conn.close()
        srv.close()

    threading.Thread(target=_serve, daemon=True).start()
    req_id = "test-live-cancel"
    token = begin_request(req_id)

    def _trigger_cancel() -> None:
        assert connected.wait(2.0)
        assert cancel_request(req_id) is True

    threading.Thread(target=_trigger_cancel, daemon=True).start()
    start = time.monotonic()
    try:
        with pytest.raises(InterruptedError):
            post_cancellable(f"http://127.0.0.1:{port}/api/chat", {"model": "qwen3:8b"}, timeout=30.0)
    finally:
        end_request(req_id, token)

    assert time.monotonic() - start < 2.0
    assert server_saw_close.wait(2.0)


def test_cancel_before_ask_tutor_propagates_without_fallback() -> None:
    req_id = "test-precancel"
    token = begin_request(req_id)
    try:
        assert cancel_request(req_id) is True
        with pytest.raises(InterruptedError):
            ask_tutor("Long question", [], TutorConfig(provider="ollama"))
    finally:
        end_request(req_id, token)
    assert cancel_request(req_id) is False


def test_cancel_endpoint_aborts_chat_turn_without_saving_ghost_turn(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    started = threading.Event()
    (tmp_path / "knowledge_base").mkdir()
    monkeypatch.setattr(workspace, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(chat_store, "CHATS_FILE", tmp_path / "chats.json")

    def slow_tutor(question: str, results: list[SearchResult], config: TutorConfig | None = None, history: list[tuple[str, str]] | None = None, temperature: float | None = None) -> TutorResponse:
        started.set()
        for _ in range(200):
            check_cancelled()
            time.sleep(0.01)
        return TutorResponse(answer="Should never complete", cited_titles=[], knowledge_gap_detected=False, recommended_topics=[])

    chunks = [KnowledgeChunk(id="c1", title="Test", file_path="test.md", content="Some content", tags=[])]
    app = FastAPI()
    app.include_router(
        query_routes.build_router(
            lambda: WorkspaceConfig(),
            lambda: chunks,
            lambda *_a, **_kw: {"label": "Exact", "intent": "lookup", "routed_query": "Huge question", "top_k": 5, "retrieval_mode": "lexical", "rrf_k": 60},
            lambda *_a, **_kw: [SearchResult(chunk=chunks[0], score=1.0)],
            lambda *_a, **_kw: [],
            slow_tutor,
        )
    )
    client = TestClient(app)
    req_id = "ui-stop-req-1"

    with ThreadPoolExecutor(max_workers=2) as pool:
        turn_future = pool.submit(
            client.post,
            "/api/chats/cancelled-chat/turn",
            json={"query": "Huge question", "ask_tutor": True, "retrieval_mode": "lexical"},
            headers={"x-request-id": req_id},
        )
        assert started.wait(2.0)
        cancel_resp = client.post(f"/api/requests/{req_id}/cancel")
        assert cancel_resp.status_code == 200 and cancel_resp.json() == {"cancelled": True}
        turn_resp = turn_future.result(timeout=3.0)

    assert turn_resp.status_code == 499
    assert chat_store.get_chat_session("cancelled-chat", chat_store.area_chat_path("knowledge_base")) is None
