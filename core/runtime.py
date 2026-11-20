"""Configurable runtime mode, bundle asset root, and local data directory."""

import os
import shutil
import sys
from pathlib import Path
from typing import Literal

AppMode = Literal["local", "public"]
APP_DIR_NAME = "REALM Engine"


def is_frozen() -> bool:
    """Return True when running inside a packaged PyInstaller desktop app."""
    return bool(getattr(sys, "frozen", False))


def bundle_root() -> Path:
    """Return the root directory containing packaged source and static assets."""
    meipass = getattr(sys, "_MEIPASS", None)
    if is_frozen() and isinstance(meipass, str) and meipass:
        return Path(meipass).resolve()
    return Path(__file__).resolve().parents[1]


def desktop_data_dir(platform: str | None = None) -> Path:
    """Return the OS-standard per-user data folder for installed desktop apps."""
    current = platform or sys.platform
    if current == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_DIR_NAME
    if current == "win32":
        base = os.environ.get("APPDATA", "").strip()
        root = Path(base) if base else Path.home() / "AppData" / "Roaming"
        return root / APP_DIR_NAME
    xdg = os.environ.get("XDG_DATA_HOME", "").strip()
    root = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return root / "realm-engine"


def data_root() -> Path:
    """Resolve the active data root (REALM_DATA_DIR -> desktop OS dir -> ./data)."""
    override = os.environ.get("REALM_DATA_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    if is_frozen():
        return desktop_data_dir().expanduser().resolve()
    return (Path(__file__).resolve().parents[1] / "data").resolve()


def seed_starter_vault(root: Path) -> Path:
    """Create knowledge_base/ and copy welcome.md once for brand-new desktop vaults."""
    vault = root / "knowledge_base"
    fresh = not vault.exists()
    vault.mkdir(parents=True, exist_ok=True)
    starter = bundle_root() / "examples" / "starter_vault" / "welcome.md"
    target = vault / "welcome.md"
    if fresh and starter.is_file() and not target.exists():
        shutil.copy2(starter, target)
    return vault


def app_mode() -> AppMode:
    return "public" if os.environ.get("REALM_MODE", "local").strip().lower() == "public" else "local"
