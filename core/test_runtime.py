"""Tests for runtime data directory resolution, frozen bundle paths, and starter seeding."""

from pathlib import Path

import pytest

from core import runtime


def test_data_root_uses_dev_data_folder_when_not_frozen(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REALM_DATA_DIR", raising=False)
    monkeypatch.delattr(runtime.sys, "frozen", raising=False)
    assert runtime.is_frozen() is False
    assert runtime.data_root().name == "data"


def test_data_root_uses_os_app_support_when_frozen(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("REALM_DATA_DIR", raising=False)
    monkeypatch.setattr(runtime.sys, "frozen", True, raising=False)
    monkeypatch.setattr(runtime.Path, "home", classmethod(lambda _cls: tmp_path))
    monkeypatch.setattr(runtime.sys, "platform", "darwin")
    assert runtime.data_root() == (tmp_path / "Library" / "Application Support" / "REALM Engine").resolve()


def test_desktop_data_dir_supports_windows_and_linux(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    assert runtime.desktop_data_dir("win32") == tmp_path / "Roaming" / "REALM Engine"
    assert runtime.desktop_data_dir("linux") == tmp_path / "xdg" / "realm-engine"


def test_bundle_root_resolves_meipass_when_frozen(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(runtime.sys, "frozen", True, raising=False)
    monkeypatch.setattr(runtime.sys, "_MEIPASS", str(tmp_path), raising=False)
    assert runtime.bundle_root() == tmp_path.resolve()


def test_seed_starter_vault_seeds_once_without_overwriting_existing(tmp_path: Path) -> None:
    vault = runtime.seed_starter_vault(tmp_path)
    welcome = vault / "welcome.md"
    assert welcome.is_file()
    welcome.write_text("# Custom User Edit\n", encoding="utf-8")
    runtime.seed_starter_vault(tmp_path)
    assert welcome.read_text(encoding="utf-8") == "# Custom User Edit\n"
