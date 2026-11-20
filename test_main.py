"""Desktop launcher selection, readiness and lifecycle without real browser/provider calls."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import main as launcher


def test_app_mode_uses_detected_chromium_browser(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(launcher, "find_app_browser", lambda: "/browser/chrome")
    monkeypatch.setattr(launcher.subprocess, "Popen", lambda command, **_kw: calls.append(command))
    assert launcher.open_desktop_window("http://127.0.0.1:8123")
    assert calls == [["/browser/chrome", "--app=http://127.0.0.1:8123"]]


def test_browser_fallback_and_existing_server_reuse(monkeypatch: pytest.MonkeyPatch) -> None:
    opened: list[str] = []
    monkeypatch.setattr(launcher, "find_app_browser", lambda: None)
    monkeypatch.setattr(launcher.webbrowser, "open", lambda url, **_kw: opened.append(url) or True)
    monkeypatch.setattr(launcher, "server_ready", lambda _url: True)
    launcher.run_desktop("127.0.0.1", 8123)
    assert opened == ["http://127.0.0.1:8123"]


def test_failed_app_launch_uses_browser_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(launcher, "find_app_browser", lambda: "/missing/browser")
    def failed(*_args: object, **_kwargs: object) -> None:
        raise OSError("not executable")
    monkeypatch.setattr(launcher.subprocess, "Popen", failed)
    monkeypatch.setattr(launcher.webbrowser, "open", lambda *_a, **_kw: True)
    assert launcher.open_desktop_window("http://127.0.0.1:8123")


def test_desktop_stops_its_owned_server_on_interrupt(monkeypatch: pytest.MonkeyPatch) -> None:
    state: dict[str, Any] = {"started": False, "joins": []}
    server = SimpleNamespace(run=lambda: None, should_exit=False)
    monkeypatch.setattr(launcher.uvicorn, "Server", lambda _cfg: server)
    def thread(**_kwargs: object) -> SimpleNamespace:
        def join(timeout: int | None = None) -> None:
            state["joins"].append(timeout)
        return SimpleNamespace(start=lambda: state.update(started=True), is_alive=lambda: True, join=join)
    def interrupted(_seconds: float) -> None:
        raise KeyboardInterrupt
    monkeypatch.setattr(launcher.time, "sleep", interrupted)
    monkeypatch.setattr(launcher.threading, "Thread", thread)
    monkeypatch.setattr(launcher, "server_ready", lambda _url: state["started"])
    monkeypatch.setattr(launcher, "open_desktop_window", lambda _url: True)
    launcher.run_desktop("127.0.0.1", 8123)
    assert server.should_exit and state["joins"] == [5]


def test_main_places_runtime_data_outside_application_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(launcher.uvicorn, "run", lambda _app, **kwargs: calls.append(kwargs))
    monkeypatch.setenv("REALM_DATA_DIR", str(tmp_path))
    launcher.main(["--data-dir", str(tmp_path), "--port", "8123"])
    assert (tmp_path / "knowledge_base").is_dir()
    assert calls == [{"host": "127.0.0.1", "port": 8123}]


@pytest.mark.parametrize("arguments", [["--port", "0"], ["--desktop", "--host", "0.0.0.0"], ["--desktop", "--public"]])
def test_launcher_rejects_invalid_arguments(arguments: list[str]) -> None:
    with pytest.raises(SystemExit):
        launcher.main(arguments)


def test_public_flag_sets_public_mode_without_creating_knowledge_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(launcher.uvicorn, "run", lambda _app, **kwargs: calls.append(kwargs))
    monkeypatch.delenv("REALM_MODE", raising=False)
    launcher.main(["--public", "--data-dir", str(tmp_path), "--port", "8124"])
    assert not (tmp_path / "knowledge_base").exists()
    assert calls == [{"host": "127.0.0.1", "port": 8124}]


def test_build_index_cli_prebuilds_json_without_starting_server(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    vault = tmp_path / "ai-engineering"
    vault.mkdir()
    (vault / "guide.md").write_text("---\ntitle: Build Test\ntags: [rag]\n---\n\n## Intro\nIndexed offline.\n", encoding="utf-8")
    monkeypatch.setenv("REALM_PUBLIC_AREAS", "ai-engineering")
    monkeypatch.setattr(launcher.uvicorn, "run", lambda *_a, **_kw: pytest.fail("server should not start"))
    launcher.main(["--build-index", "--data-dir", str(tmp_path)])
    assert (vault / "index.json").is_file() and "Indexed offline." in (vault / "index.json").read_text(encoding="utf-8")


@pytest.mark.parametrize(("platform", "expected"), [
    ("darwin", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    ("win32", "/programs/Microsoft/Edge/Application/msedge.exe"),
    ("linux", "/usr/bin/chromium"),
])
def test_detects_platform_app_browsers(platform: str, expected: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(launcher.sys, "platform", platform)
    monkeypatch.setenv("PROGRAMFILES", "/programs")
    monkeypatch.setattr(launcher.shutil, "which", lambda name: expected if platform == "linux" and name == "chromium" else None)
    monkeypatch.setattr(launcher.Path, "is_file", lambda path: str(path) == expected)
    assert launcher.find_app_browser() == expected
