"""Concurrent requests cannot merge distinct document scopes into one session."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi.testclient import TestClient

from core.contracts import TutorResponse
from features.ui import app as ui_app


def test_concurrent_scope_creation_preserves_one_scope(area_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    assert area_client.post("/api/upload", json={"filename": "other.md", "content": "# Other\nTags: base\n\n## Overview\nDefault marker."}).status_code == 200
    barrier = Barrier(2)

    def tutor(*args: object, **kwargs: object) -> TutorResponse:
        barrier.wait(timeout=5)
        return TutorResponse(answer="Synthetic", cited_titles=[], knowledge_gap_detected=False, recommended_topics=[])

    monkeypatch.setattr(ui_app, "run_tutor", tutor)
    with ThreadPoolExecutor(max_workers=2) as pool:
        requests = [pool.submit(area_client.post, "/api/chats/race/turn", json={"query": "Default", "doc_id": doc}) for doc in ("shared", "other")]
        assert sorted(p.result(timeout=5).status_code for p in requests) == [200, 409]
    session = area_client.get("/api/chats/race").json()
    assert len(session["turns"]) == 1
    assert {r["chunk"]["doc_id"] for r in session["turns"][0]["results"]} == {session["doc_id"]}
