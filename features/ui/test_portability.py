"""Regression tests for Batch 6 portability, Windows path safety, locking, and packaging."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

import pytest

import desktop_app
from core import runtime
from features.ui import folders, model_routes

REPO = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("bad", ["CON", "prn", "Aux", "nul", "COM1", "lpt9", "con.txt", "nested/NUL", "trailing.", "trailing ", "nested/dir."])
def test_folders_reject_windows_reserved_and_trailing_dot_space_names(tmp_path: Path, bad: str) -> None:
    with pytest.raises(ValueError):
        folders.contained_path(tmp_path, bad)
    with pytest.raises(ValueError):
        folders.resolve_subfolder(tmp_path, bad, create=True)


def test_folders_reject_ntfs_junctions_when_supported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sub = tmp_path / "linked"
    sub.mkdir()
    monkeypatch.setattr(os.path, "isjunction", lambda p: Path(p) == sub, raising=False)
    with pytest.raises(ValueError, match="Symbolic links"):
        folders.contained_path(tmp_path, "linked/note.md")


def test_resolve_document_matches_uppercase_extensions_case_insensitively(tmp_path: Path) -> None:
    guide = tmp_path / "architecture.MD"
    guide.write_text("# Arch\n", encoding="utf-8")
    resolved = folders.resolve_document(tmp_path, "architecture")
    assert resolved.resolve() == guide.resolve()


def test_ollama_host_env_override_and_pull_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    assert runtime.ollama_base_url() == "http://127.0.0.1:11434"
    assert model_routes.pull_url() == "http://127.0.0.1:11434/api/pull"

    monkeypatch.setenv("OLLAMA_HOST", "127.0.0.1:11435")
    assert runtime.ollama_base_url() == "http://127.0.0.1:11435"
    assert model_routes.pull_url() == "http://127.0.0.1:11435/api/pull"
    assert runtime.is_loopback_url(model_routes.pull_url()) is True

    monkeypatch.setenv("OLLAMA_HOST", "http://ollama.internal:11434/")
    assert runtime.ollama_base_url() == "http://ollama.internal:11434"
    assert runtime.is_loopback_url(model_routes.pull_url()) is False


def test_instance_lock_prevents_duplicate_desktop_launch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[int] = []
    monkeypatch.setattr(desktop_app, "run_native_desktop", lambda **_kw: called.append(1) or 8000)
    with runtime.instance_lock(tmp_path) as first:
        assert first is True
        with runtime.instance_lock(tmp_path) as second:
            assert second is False
        desktop_app.main(["--data-dir", str(tmp_path), "--smoke-test"])
    assert called == []
    with runtime.instance_lock(tmp_path) as after_release:
        assert after_release is True


def test_packaging_config_and_scripts_are_hardened() -> None:
    pyproject = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    wheel = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]
    assert "core" in wheel["packages"] and "features" in wheel["packages"]
    assert "main.py" in wheel["force-include"]
    assert "examples/starter_vault/welcome.md" in wheel["force-include"]
    assert "ruff" in pyproject["tool"] and "pyright" in pyproject["tool"]

    dockerfile = (REPO / "Dockerfile").read_text(encoding="utf-8")
    assert "fonts-dejavu-core" in dockerfile
    assert "examples/starter_vault" in dockerfile
    assert "ProxyHandler({})" in dockerfile

    macos_sh = (REPO / "packaging" / "build_macos.sh").read_text(encoding="utf-8")
    assert 'VERSION="$(uv run python -c' in macos_sh

    win_ps1 = (REPO / "packaging" / "build_windows.ps1").read_text(encoding="utf-8")
    assert "PyInstaller failed with exit code $LASTEXITCODE" in win_ps1
    assert "Inno Setup failed with exit code $LASTEXITCODE" in win_ps1
