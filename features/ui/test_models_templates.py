"""Recommended downloads stay local and templates preserve isolation and privacy policy."""

from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from features.ui import model_routes


@pytest.mark.parametrize("ram,model", [(0, "qwen2.5:3b"), (8, "qwen2.5:3b"), (16, "qwen3:8b"), (64, "qwen3:8b")])
def test_recommended_download_and_embedding_companion(area_client: TestClient, monkeypatch: pytest.MonkeyPatch, ram: int, model: str) -> None:
    monkeypatch.setattr(model_routes, "physical_ram_gb", lambda: ram)
    calls: list[dict[str, object]] = []
    actual_client = httpx.Client

    def respond(request: httpx.Request) -> httpx.Response:
        import json
        assert str(request.url) == "http://127.0.0.1:11434/api/pull"
        calls.append(json.loads(request.content))
        return httpx.Response(200, json={"status": "success"})

    def local_client(**kwargs: object) -> httpx.Client:
        assert kwargs["trust_env"] is False and kwargs["follow_redirects"] is False
        return actual_client(transport=httpx.MockTransport(respond), trust_env=False)

    monkeypatch.setattr(model_routes.httpx, "Client", local_client)
    result = area_client.post("/api/system/pull-model", json={"model": "recommended"})
    assert result.status_code == 200 and result.json()["installed_models"] == [model, "nomic-embed-text:v1.5"]
    assert calls == [{"name": name, "model": name, "stream": False} for name in (model, "nomic-embed-text:v1.5")]


def test_unapproved_models_and_duplicate_downloads_block_before_dispatch(area_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(model_routes, "physical_ram_gb", lambda: 8)
    for model in ("qwen3:8b", "https://remote/model", "../../bad", "huge-cloud", "arbitrary:70b"):
        assert area_client.post("/api/system/pull-model", json={"model": model}).status_code == 400
    with model_routes.PULL_LOCK:
        assert area_client.post("/api/system/pull-model", json={"model": "recommended"}).status_code == 409
    assert area_client.post("/api/system/pull-model", json={"model": "recommended"}, headers={"x-knowledge-area": "stale"}).status_code == 409


@pytest.mark.parametrize("failure,status", [("offline", 503), ("timeout", 504), ("server", 502), ("incomplete", 502), ("malformed", 502)])
def test_download_errors_are_clear_and_release_the_lock(area_client: TestClient, monkeypatch: pytest.MonkeyPatch, failure: str, status: int) -> None:
    actual_client = httpx.Client

    def respond(request: httpx.Request) -> httpx.Response:
        if failure == "offline":
            raise httpx.ConnectError("offline")
        if failure == "timeout":
            raise httpx.ReadTimeout("slow")
        return httpx.Response(500 if failure == "server" else 200, json=[] if failure == "malformed" else {"status": "pulling"})

    monkeypatch.setattr(model_routes.httpx, "Client", lambda **_kw: actual_client(transport=httpx.MockTransport(respond)))
    assert area_client.post("/api/system/pull-model", json={"model": "recommended"}).status_code == status
    assert not model_routes.PULL_LOCK.locked()


@pytest.mark.parametrize("template,folders,private", [("blank", set(), False), ("care", {"care_plans", "protocols", "daily_notes"}, True), ("finance", {"contracts", "invoices", "taxes"}, True), ("study", {"subjects", "notes", "assignments"}, False)])
def test_workspace_templates_create_folders_without_mixing_guides(area_client: TestClient, tmp_path: Path, template: str, folders: set[str], private: bool) -> None:
    area_client.post("/api/workspace", json={"strict_local_only": False, "run_mode": "cloud", "daily_cloud_request_limit": 3})
    result = area_client.post("/api/workspace/create", json={"name": "new_space", "template": template})
    assert result.status_code == 200
    assert {p.name for p in (tmp_path / "new_space").iterdir() if p.is_dir()} == folders
    assert result.json()["config"]["strict_local_only"] is private
    assert result.json()["config"]["daily_cloud_request_limit"] == 3
    assert result.json()["doc_count"] == 0 and area_client.get("/api/chats").json() == []
    if private:
        assert result.json()["config"]["run_mode"] == "local"
        assert area_client.get("/api/models?provider=openai").status_code == 403
    assert (tmp_path / "knowledge_base/shared.md").is_file()
    assert area_client.post("/api/workspace/create", json={"name": "new_space", "template": "care"}).status_code == 409


@pytest.mark.parametrize("name,template", [("../escape", "care"), ("features", "study"), ("safe", "unknown")])
def test_invalid_template_requests_leave_workspace_unchanged(area_client: TestClient, name: str, template: str) -> None:
    assert area_client.post("/api/workspace/create", json={"name": name, "template": template}).status_code == 400
    assert area_client.get("/api/workspace").json()["config"]["knowledge_dir"] == "knowledge_base"
