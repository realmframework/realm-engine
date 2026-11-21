"""Regression tests for Batch 4: route authorization, scope lock, concurrency & state integrity."""

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.contracts import (
    ChatSession,
    ChatTurn,
    KnowledgeChunk,
    TutorResponse,
    WorkspaceConfig,
)
from core.db import save_chunks
from core.linked_vaults import link_folder
from features.ui import app as ui_app
from features.ui import areas, chat_store, synthesize_routes, workspace


def _seed_session(chat_id: str, area: str = "knowledge_base", **extra: Any) -> ChatSession:
    turns = [
        ChatTurn(query=f"Q{i}", tutor=TutorResponse(answer=f"A{i}", cited_titles=[], knowledge_gap_detected=False, recommended_topics=[]), created_at="2026-01-01T00:00:00Z", subfolder=extra.get("subfolder"), doc_id=extra.get("doc_id"))
        for i in range(3)
    ]
    sess = ChatSession(chat_id=chat_id, title="Test", updated_at="2026-01-01T00:00:00Z", area=area, active_dirs=[area], turns=turns, **extra)
    return chat_store.save_chat_session(sess, chat_store.area_chat_path(area))


def test_cross_area_and_empty_workspace_guards_on_context_fork_pdf_and_stream(area_client: TestClient) -> None:
    _seed_session("c-area")
    bad_hdr = {"x-knowledge-area": "other_area"}
    assert area_client.get("/api/chats/c-area/context", headers=bad_hdr).status_code == 409
    assert area_client.post("/api/chats/c-area/clear-context", json={}, headers=bad_hdr).status_code == 409
    assert area_client.post("/api/chats/c-area/fork", json={"turn_index": 0}, headers=bad_hdr).status_code == 409
    assert area_client.post("/api/export/pdf", json={"chat_id": "c-area"}, headers=bad_hdr).status_code == 409

    ui_app.WORKSPACE_CONFIG = WorkspaceConfig(knowledge_dir="", active_dirs=[])
    assert area_client.post("/api/chats/c-none/turn/stream", json={"query": "hi", "ask_tutor": False}).status_code == 400
    assert area_client.post("/api/chats/c-none/clear-context", json={}).status_code == 400
    assert area_client.post("/api/chats/c-none/fork", json={"turn_index": 0}).status_code == 400


def test_fork_clamps_cleared_context_and_rejects_bad_inputs(area_client: TestClient) -> None:
    _seed_session("c-fork", context_cleared_at=2, compacted_summary="Summary of turns 0-2")
    assert area_client.post("/api/chats/c-fork/fork", json={"turn_index": "not-an-int"}).status_code == 400
    assert area_client.post("/api/chats/c-fork/fork", content="{bad", headers={"content-type": "application/json"}).status_code == 400
    res = area_client.post("/api/chats/c-fork/fork", json={"turn_index": 0})
    assert res.status_code == 200
    forked = res.json()["session"]
    assert forked["context_cleared_at"] == 1 and forked["compacted_summary"] == ""


def test_synthesize_preserves_scope_lock_and_malformed_json_returns_400(area_client: TestClient) -> None:
    async def _fake_stream(*_a: Any, **_kw: Any) -> AsyncIterator[dict[str, object]]:
        yield {"type": "token", "delta": "# Exec Brief\nDone."}

    _seed_session("c-scope", subfolder="guides", doc_id="guides/spec")
    mini = FastAPI()
    mini.include_router(synthesize_routes.build_router(lambda: ui_app.WORKSPACE_CONFIG, _fake_stream))
    res = TestClient(mini).post("/api/chats/c-scope/synthesize", json={"format_id": "exec_4w"})
    assert res.status_code == 200
    updated = chat_store.get_chat_session("c-scope", chat_store.area_chat_path("knowledge_base"))
    assert updated is not None and updated.subfolder == "guides" and updated.doc_id == "guides/spec"
    assert updated.turns[-1].subfolder == "guides" and updated.turns[-1].doc_id == "guides/spec"
    assert area_client.post("/api/search/xray", content="{bad", headers={"content-type": "application/json"}).status_code == 400
    assert area_client.post("/api/search/xray", json={"query": "hi", "top_k": "nan"}).status_code == 422


def test_knowledge_base_identity_changes_on_recreate_and_cache_invalidates_deleted_file(tmp_path: Path) -> None:
    areas.area_path("knowledge_base", tmp_path, create=True)
    id1 = areas.area_identity("knowledge_base", tmp_path)
    areas.delete_area("knowledge_base", tmp_path)
    kb2 = areas.area_path("knowledge_base", tmp_path, create=True)
    assert areas.area_identity("knowledge_base", tmp_path) != id1

    f1, f2 = kb2 / "a.md", kb2 / "b.md"
    f1.write_text("# A\nBody A\n", encoding="utf-8")
    f2.write_text("# B\nBody B\n", encoding="utf-8")
    cache = kb2 / "index.json"
    save_chunks([KnowledgeChunk(id="a#1", title="A", content="Body A", tags=[], file_path=str(f1)), KnowledgeChunk(id="b#1", title="B", content="Body B", tags=[], file_path=str(f2))], cache)
    f2.unlink()
    reingested = []
    areas._cached_area_chunks(kb2, lambda d: reingested.append(d) or [], tmp_path)
    assert reingested == [kb2]


def test_linked_vault_blocks_upload_create_clip_import_and_child_self_import(area_client: TestClient, tmp_path: Path) -> None:
    ext = tmp_path.parent / f"ext_ro_{tmp_path.name}"
    ext.mkdir(exist_ok=True)
    (ext / "note.md").write_text("# Ext\nBody\n", encoding="utf-8")
    slug, _ = link_folder(ext, workspace.REPO_ROOT, label="Ext RO")
    ui_app.activate_workspace(WorkspaceConfig(knowledge_dir=slug, active_dirs=[slug]))

    assert area_client.post("/api/guides/create", json={"title": "New", "content": "Body"}).status_code == 403
    assert area_client.post("/api/upload", json={"files": [{"filename": "a.md", "content": "# A"}]}).status_code == 403
    assert area_client.post("/api/guides/clip-url", json={"url": "https://example.com"}).status_code == 403
    assert area_client.post("/api/workspace/import-native-folder", json={"source_path": str(ext)}).status_code == 403

    ui_app.activate_workspace(WorkspaceConfig(knowledge_dir="knowledge_base", active_dirs=["knowledge_base"]))
    child = workspace.REPO_ROOT / "knowledge_base" / "sub"
    child.mkdir(parents=True, exist_ok=True)
    (child / "x.md").write_text("# X\nBody\n", encoding="utf-8")
    assert area_client.post("/api/workspace/import-native-folder", json={"source_path": str(child)}).status_code == 400
