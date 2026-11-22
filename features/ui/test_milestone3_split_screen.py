"""Integration tests for True-DRY VS Code 4-Zone Split Workbench & Same-Origin Embed Security."""

from pathlib import Path

from fastapi.testclient import TestClient

from core.contracts import ChatTurn, WorkspaceConfig
from features.ui import app as ui_app
from features.ui import chat_store, workspace


def _client(tmp_path: Path, monkeypatch: object) -> TestClient:
    mp = monkeypatch  # type: ignore[assignment]
    area = tmp_path / "split_ws"
    area.mkdir(parents=True, exist_ok=True)
    (area / "guide.md").write_text("# Architecture\n\nSplit pane details.\n", encoding="utf-8")
    cfg = WorkspaceConfig(app_title="Split Test", knowledge_dir="split_ws", active_dirs=["split_ws"], strict_local_only=True)
    mp.setattr(workspace, "REPO_ROOT", tmp_path)  # type: ignore[attr-defined]
    mp.setattr(workspace, "WORKSPACE_FILE", tmp_path / "workspace.json")  # type: ignore[attr-defined]
    mp.setattr(chat_store, "REPO_ROOT", tmp_path)  # type: ignore[attr-defined]
    mp.setattr(chat_store, "CHATS_FILE", tmp_path / "chats.json")  # type: ignore[attr-defined]
    workspace.save_workspace_config(cfg, tmp_path / "workspace.json")
    mp.setattr(ui_app, "WORKSPACE_CONFIG", cfg)  # type: ignore[attr-defined]
    mp.setattr(ui_app, "INDEX", [])  # type: ignore[attr-defined]
    mp.setattr(ui_app, "_INDEX_KEY", None)  # type: ignore[attr-defined]
    return TestClient(ui_app._build_local_app())


def test_true_dry_four_zone_workbench_and_embed_framing_headers(tmp_path: Path, monkeypatch: object) -> None:
    client = _client(tmp_path, monkeypatch)
    res = client.get("/")
    assert res.status_code == 200
    assert res.headers.get("x-frame-options") == "SAMEORIGIN"
    csp = res.headers.get("content-security-policy", "")
    assert "frame-ancestors 'self'" in csp and "frame-src 'self'" in csp
    api_res = client.get("/api/workspace")
    assert api_res.headers.get("x-frame-options") == "DENY"
    html = res.text
    for needle in (
        'id="workbench-grid"',
        'id="center-tabbar"',
        'id="center-tablist"',
        'id="center-split-btn"',
        'id="center-split-resizer"',
        'role="separator"',
        'id="center-split-pane"',
        'id="center-split-frame"',
        'id="bottom-panel-resizer"',
        'id="bottom-panel"',
        'id="bottom-panel-frame"',
        'id="bottom-panel-more-menu"',
        'id="right-sidebar-resizer"',
        'id="inspector-sidebar"',
        'id="right-panel-inspector"',
        'id="wb-tf-ask-chat"',
        "e.isComposing || e.keyCode === 229",
        "resetSplitOnAreaChange",
    ):
        assert needle in html
    for removed in (
        'id="split-toggle-btn"',
        'id="split-mode-menu"',
        'id="wb-split-chat-btn"',
        'id="split-chat-body"',
        'id="split-tasks-body"',
        'id="split-focus-body"',
        'id="split-impact-body"',
        'id="split-guide-body"',
    ):
        assert removed not in html


def test_parallel_chat_threads_stay_isolated_in_store(tmp_path: Path, monkeypatch: object) -> None:
    client = _client(tmp_path, monkeypatch)
    chat_path = chat_store.area_chat_path("split_ws")
    chat_store.append_chat_turn(
        "pane-a-chat",
        ChatTurn(query="Left pane question", ask_tutor=False, created_at=chat_store.utc_now_iso(), agent_id="saga", agent_name="Saga"),
        chat_path,
        area="split_ws",
    )
    chat_store.append_chat_turn(
        "pane-b-chat",
        ChatTurn(query="Right pane critique", ask_tutor=False, created_at=chat_store.utc_now_iso(), agent_id="lisbeth", agent_name="Lisbeth"),
        chat_path,
        area="split_ws",
    )
    a_res = client.get("/api/chats/pane-a-chat")
    b_res = client.get("/api/chats/pane-b-chat")
    assert a_res.status_code == 200 and b_res.status_code == 200
    assert a_res.json()["turns"][0]["query"] == "Left pane question"
    assert a_res.json()["last_agent_id"] == "saga"
    assert b_res.json()["turns"][0]["query"] == "Right pane critique"
    assert b_res.json()["last_agent_id"] == "lisbeth"
