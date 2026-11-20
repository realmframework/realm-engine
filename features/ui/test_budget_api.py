"""Cloud admission across answers, embeddings, speech and owner controls."""

from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from core.contracts import WorkspaceConfig
from features.ui import app as ui_app
from features.ui import audio_routes


def test_cloud_answer_is_blocked_before_network_and_local_stays_free(area_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    area_client.get("/api/guides")
    monkeypatch.setattr(ui_app, "WORKSPACE_CONFIG", WorkspaceConfig(strict_local_only=False, daily_cloud_request_limit=0))
    calls: list[str] = []

    def denied(url: str, **_kwargs: object) -> httpx.Response:
        calls.append(url)
        raise httpx.ConnectError("Synthetic offline provider")

    monkeypatch.setattr(httpx, "post", denied)
    payload = {"query": "Default", "ask_tutor": True, "provider": "openai", "model": "gpt-4o-mini", "api_key": "synthetic", "retrieval_mode": "lexical"}
    response = area_client.post("/api/chats/capped/turn", json=payload)
    assert response.status_code == 200 and "Cloud Budget Guardrail" in response.json()["turns"][0]["tutor"]["answer"]
    assert calls == [] and area_client.get("/api/budget").json()["cloud_requests_today"] == 0
    response = area_client.post("/api/chats/local/turn", json={**payload, "provider": "ollama", "model": "small-local"})
    assert response.status_code == 200 and calls == ["http://127.0.0.1:11434/api/chat"]
    assert area_client.get("/api/budget").json()["estimated_cost_usd"] == 0.0


def test_embeddings_and_voice_share_admission_before_dispatch(area_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    area_client.get("/api/guides")
    monkeypatch.setattr(ui_app, "INDEX", [c.model_copy(update={"embedding": [1.0, 0.0]}) for c in ui_app.INDEX])
    monkeypatch.setattr(ui_app, "WORKSPACE_CONFIG", WorkspaceConfig(strict_local_only=False, daily_cloud_request_limit=0))
    calls: list[str] = []
    monkeypatch.setattr(ui_app, "embed_text", lambda *_args, **_kw: calls.append("embedding") or [1.0, 0.0])
    monkeypatch.setattr(audio_routes.httpx, "post", lambda *_args, **_kw: calls.append("speech"))
    result = area_client.get("/api/search", params={"q": "Default", "provider": "openai", "model": "gpt-4o-mini"})
    assert result.status_code == 429 and "Cloud Budget Guardrail" in result.json()["detail"]
    for model in ("openai:tts-1", "elevenlabs:tts"):
        response = area_client.post("/api/audio/speak", json={"text": "Synthetic speech", "model": model, "api_key": "synthetic"})
        assert response.status_code == 429
    lexical = area_client.get("/api/search", params={"q": "Default", "provider": "openai", "retrieval_mode": "lexical"})
    assert lexical.status_code == 200 and calls == []
    monkeypatch.setattr(ui_app, "WORKSPACE_CONFIG", WorkspaceConfig(strict_local_only=True, daily_cloud_request_limit=50))
    assert area_client.post("/api/audio/speak", json={"text": "Text", "model": "openai:tts-1"}).status_code == 403
    assert calls == []


def test_limits_persist_reset_is_explicit_and_stale_tabs_fail(area_client: TestClient, tmp_path: Path) -> None:
    payload = {"knowledge_dir": "knowledge_base", "daily_cloud_request_limit": 7, "daily_budget_usd_limit": 0.5, "run_mode": "search"}
    response = area_client.post("/api/workspace", json=payload)
    assert response.status_code == 200 and response.json()["config"]["run_mode"] == "search"
    assert '"daily_cloud_request_limit": 7' in (tmp_path / "workspace.json").read_text()
    assert area_client.get("/api/budget").json()["daily_cloud_request_limit"] == 7
    assert ui_app.budget.check_and_record_budget("openai") is None
    for invalid in ({"confirm": False}, {}):
        assert area_client.post("/api/budget/reset", json=invalid).status_code == 400
    assert area_client.post("/api/budget/reset", data={"confirm": "true"}).status_code == 422
    stale = {"x-knowledge-area": "other"}
    assert area_client.get("/api/budget", headers=stale).status_code == 409
    assert area_client.post("/api/budget/reset", headers=stale, json={"confirm": True}).status_code == 409
    assert area_client.get("/api/budget").json()["cloud_requests_today"] == 1
    assert area_client.post("/api/workspace", json={"knowledge_dir": "another"}).status_code == 200
    assert area_client.get("/api/budget").json()["cloud_requests_today"] == 1


@pytest.mark.parametrize("field,value", [("daily_cloud_request_limit", -1), ("daily_cloud_request_limit", 1.2), ("daily_budget_usd_limit", -0.1)])
def test_invalid_budget_limits_rejected(area_client: TestClient, field: str, value: float) -> None:
    assert area_client.post("/api/workspace", json={field: value}).status_code == 422


def test_app_level_api_keys_persist_across_browsers_and_never_leak_raw_secret(area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from core import secrets

    initial = area_client.get("/api/keys/status")
    assert initial.status_code == 200 and initial.headers["cache-control"] == "no-store"
    assert initial.json()["keys"]["openai"]["configured"] is False

    saved = area_client.post("/api/keys", json={"provider": "openai", "api_key": "sk-test-secret-9876"})
    assert saved.status_code == 200 and "sk-test-secret-9876" not in saved.text
    assert saved.json()["keys"]["openai"] == {"configured": True, "source": "app", "hint": "…9876"}
    assert (tmp_path / "secrets.json").stat().st_mode & 0o777 == 0o600
    assert secrets.get_api_key("openai") == "sk-test-secret-9876"

    # Backup ZIP must never contain secrets.json
    backup = area_client.get("/api/backup/export")
    assert backup.status_code == 200 and b"sk-test-secret-9876" not in backup.content

    # .env fallback works when app storage has no key for a provider
    dotenv = tmp_path / ".env"
    dotenv.write_text('GEMINI_API_KEY="gem-from-dotenv-4321"\n', encoding="utf-8")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    secrets.load_dotenv_files([dotenv])
    assert secrets.get_api_key("gemini") == "gem-from-dotenv-4321"
    assert area_client.get("/api/keys/status").json()["keys"]["gemini"] == {"configured": True, "source": "env", "hint": "…4321"}

    cleared = area_client.delete("/api/keys")
    assert cleared.status_code == 200 and cleared.json()["keys"]["openai"]["configured"] is False
    assert area_client.post("/api/keys", json={"provider": "invalid", "api_key": "x"}).status_code == 400
