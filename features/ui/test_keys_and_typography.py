"""Regression tests for live API key verification, per-provider removal, and global typography."""

from __future__ import annotations

import re
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from core.contracts import WorkspaceConfig
from features.ui import app as ui_app
from features.ui.template import HTML_PAGE

UI_DIR = Path(__file__).resolve().parent


def test_api_key_verify_respects_local_lock_and_handles_auth_outcomes(
    area_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    class _FakeClient:
        def __init__(self, status: int, body: object | None = None, err: Exception | None = None) -> None:
            self._status, self._body, self._err = status, body, err

        def __enter__(self) -> _FakeClient:
            return self

        def __exit__(self, *_a: object) -> None:
            return None

        def get(self, url: str, **_kw: object) -> httpx.Response:
            calls.append(url)
            if self._err is not None:
                raise self._err
            return httpx.Response(self._status, json=self._body)

    area_client.post("/api/keys", json={"provider": "kimi", "api_key": "sk-kimi-secret-V2f3"})
    area_client.post("/api/keys", json={"provider": "openai", "api_key": "sk-openai-secret-9999"})

    # Local-only lock blocks outbound verify before network
    monkeypatch.setattr(ui_app, "WORKSPACE_CONFIG", WorkspaceConfig(strict_local_only=True))
    blocked = area_client.post("/api/keys/verify", json={"provider": "kimi"})
    assert blocked.status_code == 403 and calls == []

    # Unlock cloud APIs and verify valid 200 response
    monkeypatch.setattr(ui_app, "WORKSPACE_CONFIG", WorkspaceConfig(strict_local_only=False))
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **_kw: _FakeClient(200, {"data": [{"id": "kimi-k2.5"}, {"id": "kimi-k2-thinking"}, {"id": "text-embedding-3"}]}),
    )
    ok = area_client.post("/api/keys/verify", json={"provider": "kimi"})
    assert ok.status_code == 200 and ok.headers["cache-control"] == "no-store"
    assert ok.json() == {"provider": "kimi", "ok": True, "status": "valid", "models_count": 2}
    assert "sk-kimi-secret-V2f3" not in ok.text and calls == ["https://api.moonshot.ai/v1/models"]

    # Invalid 401 key
    monkeypatch.setattr(httpx, "Client", lambda **_kw: _FakeClient(401, {"error": "bad key"}))
    bad = area_client.post("/api/keys/verify", json={"provider": "kimi"})
    assert bad.status_code == 200 and bad.json()["ok"] is False and bad.json()["status"] == "invalid"

    # Unreachable network error
    monkeypatch.setattr(
        httpx, "Client", lambda **_kw: _FakeClient(0, err=httpx.ConnectError("offline"))
    )
    down = area_client.post("/api/keys/verify", json={"provider": "kimi"})
    assert down.status_code == 200 and down.json()["ok"] is False and down.json()["status"] == "unreachable"

    # Single-provider DELETE removes only kimi and preserves openai
    removed = area_client.delete("/api/keys?provider=kimi")
    assert removed.status_code == 200
    keys = removed.json()["keys"]
    assert keys["kimi"]["configured"] is False and keys["openai"]["configured"] is True


def test_global_typography_has_zero_micro_px_classes_and_modern_key_ui_markers() -> None:
    for py_file in sorted(UI_DIR.glob("*.py")):
        if py_file.name.startswith("test_"):
            continue
        src = py_file.read_text(encoding="utf-8")
        assert not re.search(r"text-\[\d+(?:\.\d+)?px\]", src), f"Hardcoded px font class found in {py_file.name}"
    css = (UI_DIR / "static" / "ui.css").read_text(encoding="utf-8")
    assert ".text-2xs{font-size:calc(.8125rem*var(--ui-scale, 1))" in css
    assert ".text-xs{font-size:calc(.875rem*var(--ui-scale, 1))" in css
    assert ".text-sm{font-size:calc(.9375rem*var(--ui-scale, 1))" in css
    assert not re.search(r"\.text-\\\[\d+(?:\.\d+)?px\\\]", css)
    for marker in (
        '<meta name="text-scale" content="scale" />',
        'id="api-key-connected-card"',
        'id="test-api-key-btn"',
        'id="replace-api-key-btn"',
        'id="remove-api-key-btn"',
        'id="toggle-api-key-visibility"',
        'id="api-key-get-link"',
    ):
        assert marker in HTML_PAGE
