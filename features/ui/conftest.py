"""Isolated synthetic vaults for endpoint isolation, public API, and deletion tests."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core import model_routing, secrets
from core.contracts import WorkspaceConfig
from features.ui import app as ui_app
from features.ui import chat_store, workspace

_FIXTURE_GUIDES: dict[str, str] = {
    "ai_first_architecture.md": (
        "# AI-First Software Architecture\nTags: architecture, vertical-slice, agents\n\n"
        "## Vertical Slice Isolation\nVertical slice boundaries keep feature context local and auditable.\n\n"
        "## Contract-First Schemas\nShared Pydantic models live in core contracts with strict validation.\n"
    ),
    "hybrid_retrieval_and_local_llms.md": (
        "# Hybrid Search and Local MoE Models\nTags: rag, search, local-llms\n\n"
        "## BM25 Keyword Search vs Dense Embeddings\nHybrid search fuses BM25 lexical scoring with dense vectors via Reciprocal Rank Fusion (RRF).\n\n"
        "## Reranking Strategies\nRRF combines lexical and dense ranks cleanly without scale calibration.\n"
    ),
    "pgvector.md": (
        "# PostgreSQL pgvector\nTags: rag, database, embeddings\n\n"
        "## HNSW and IVFFlat Indexes\npgvector stores dense embeddings directly inside Postgres for hybrid SQL and vector search.\n"
    ),
}


@pytest.fixture(autouse=True)
def default_test_workspace(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep test configuration completely isolated from the local ./data/ vaults and Ollama."""
    root = tmp_path_factory.mktemp("default_workspace")
    kb = root / "knowledge_base"
    kb.mkdir(parents=True)
    for name, body in _FIXTURE_GUIDES.items():
        (kb / name).write_text(body, encoding="utf-8")
    monkeypatch.setattr(workspace, "REPO_ROOT", root)
    monkeypatch.setattr(workspace, "WORKSPACE_FILE", root / "workspace.json")
    monkeypatch.setattr(chat_store, "CHATS_FILE", root / "chats.json")
    monkeypatch.setattr(ui_app, "WORKSPACE_CONFIG", WorkspaceConfig())
    monkeypatch.setattr(ui_app, "INDEX", [])
    monkeypatch.setattr(ui_app, "AUTO_EMBED", False)
    monkeypatch.setattr(ui_app.budget, "BUDGET_FILE", root / "budget_state.json")
    monkeypatch.setattr(secrets, "SECRETS_FILE", root / "secrets.json")
    monkeypatch.setattr(model_routing, "_LAST_OLLAMA_MODEL", "")


@pytest.fixture
def area_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    kb = tmp_path / "knowledge_base"
    kb.mkdir(exist_ok=True)
    (kb / "shared.md").write_text("# Shared Guide\nTags: base\n\n## Overview\nDefault universe marker.\n", encoding="utf-8")
    monkeypatch.setattr(workspace, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(workspace, "WORKSPACE_FILE", tmp_path / "workspace.json")
    monkeypatch.setattr(chat_store, "CHATS_FILE", tmp_path / "chats.json")
    monkeypatch.setattr(ui_app, "WORKSPACE_CONFIG", WorkspaceConfig())
    monkeypatch.setattr(ui_app, "INDEX", [])
    monkeypatch.setattr(ui_app, "AUTO_EMBED", False)
    monkeypatch.setattr(secrets, "SECRETS_FILE", tmp_path / "secrets.json")
    yield TestClient(ui_app.app)
