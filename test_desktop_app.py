"""Unit tests for the native desktop app launcher without opening a real GUI window."""

import socket
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import desktop_app


def test_find_available_port_falls_back_when_preferred_is_busy() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen(1)
        busy_port = int(occupied.getsockname()[1])
        chosen = desktop_app.find_available_port(preferred=busy_port)
        assert chosen != busy_port and 1 <= chosen <= 65535


def test_run_native_desktop_opens_window_and_stops_server_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    server = SimpleNamespace(run=lambda: events.append("run"), should_exit=False)
    monkeypatch.setattr(desktop_app, "find_available_port", lambda *_a, **_kw: 8765)
    monkeypatch.setattr(desktop_app, "load_asgi_app", lambda: object())
    monkeypatch.setattr(desktop_app.uvicorn, "Server", lambda _cfg: server)
    monkeypatch.setattr(desktop_app, "wait_for_health", lambda url, _worker: events.append(f"health:{url}"))

    def fake_thread(**_kw: object) -> SimpleNamespace:
        return SimpleNamespace(
            start=lambda: events.append("start"),
            is_alive=lambda: True,
            join=lambda timeout=None: events.append(f"join:{timeout}"),
        )

    monkeypatch.setattr(desktop_app.threading, "Thread", fake_thread)

    def fake_window(url: str, title: str) -> None:
        events.append(f"window:{title}@{url}")

    port = desktop_app.run_native_desktop(port=8000, title="REALM Engine", window_runner=fake_window)
    assert port == 8765
    assert server.should_exit is True
    assert events == ["start", "health:http://127.0.0.1:8765", "window:REALM Engine@http://127.0.0.1:8765", "join:5"]


def test_main_ignores_macos_psn_arg_and_seeds_starter_vault(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[dict[str, Any]] = []
    monkeypatch.setattr(desktop_app, "run_native_desktop", lambda **kw: seen.append(kw) or 8000)
    desktop_app.main(["-psn_0_123456", "--data-dir", str(tmp_path), "--smoke-test"])
    assert (tmp_path / "knowledge_base" / "welcome.md").is_file()
    assert seen == [{"port": 8000, "title": "REALM Engine", "smoke_only": True}]


def test_main_rejects_invalid_port() -> None:
    with pytest.raises(SystemExit):
        desktop_app.main(["--port", "0"])
