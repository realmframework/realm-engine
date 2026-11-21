"""Configurable runtime mode, bundle asset root, and local data directory."""

import os
import shutil
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse
from urllib.request import ProxyHandler, build_opener

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


def _is_installed_package() -> bool:
    return bool({"site-packages", "dist-packages"} & {p.lower() for p in Path(__file__).resolve().parts})
def data_root() -> Path:
    """Resolve the active data root (REALM_DATA_DIR -> desktop/wheel OS dir -> ./data)."""
    override = os.environ.get("REALM_DATA_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    if is_frozen() or _is_installed_package():
        return desktop_data_dir().expanduser().resolve()
    return (Path(__file__).resolve().parents[1] / "data").resolve()


STARTER_MARKER = ".realm-initialized"


def copy_starter_welcome(target: Path) -> Path | None:
    """Copy the bundled welcome guide into ``target`` when available."""
    starter = bundle_root() / "examples" / "starter_vault" / "welcome.md"
    target.mkdir(parents=True, exist_ok=True)
    dest = target / "welcome.md"
    if starter.is_file() and not dest.exists() and not dest.is_symlink():
        shutil.copy2(starter, dest)
        return dest
    return None


def seed_starter_vault(root: Path) -> Path:
    """Seed knowledge_base/ with welcome.md once for brand-new vaults; never recreate if deleted."""
    vault = root / "knowledge_base"
    marker = root / STARTER_MARKER
    if marker.exists() or (root / "workspace.json").exists() or (root / "linked_vaults.json").exists():
        return vault
    fresh = not vault.exists()
    vault.mkdir(parents=True, exist_ok=True)
    if fresh:
        copy_starter_welcome(vault)
    if not marker.is_symlink():
        marker.write_text("1\n", encoding="utf-8")
    return vault


def app_mode() -> AppMode:
    return "public" if os.environ.get("REALM_MODE", "local").strip().lower() == "public" else "local"


def ollama_base_url() -> str:
    """Resolve the local Ollama base URL from OLLAMA_HOST or default 127.0.0.1:11434."""
    from core.net_security import is_blocked_metadata_host
    raw = os.environ.get("OLLAMA_HOST", "").strip()
    if not raw or any(ord(c) < 32 or ord(c) == 127 for c in raw):
        return "http://127.0.0.1:11434"
    parsed = urlparse(raw if "://" in raw else f"http://{raw}")
    if parsed.scheme in {"http", "https"} and parsed.netloc and parsed.hostname and not parsed.username and not parsed.password and not is_blocked_metadata_host(parsed.hostname):
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
    return "http://127.0.0.1:11434"

def is_loopback_url(url: str) -> bool:
    """Return True when ``url`` targets loopback so proxy env vars can be bypassed."""
    host = (urlparse(url).hostname or "").lower().strip("[]")
    return host in {"127.0.0.1", "localhost", "::1"}

def urlopen_loopback(url: str, timeout: float = 0.5) -> Any:
    """Open a loopback HTTP URL bypassing system/environment HTTP_PROXY variables."""
    return build_opener(ProxyHandler({})).open(url, timeout=timeout)


def _lock_fd(handle: Any, lock_path: Path, unlock: bool = False) -> None:
    if sys.platform == "win32":
        import msvcrt

        handle.seek(0)
        if not unlock and lock_path.stat().st_size == 0:
            handle.write(b"0")
            handle.flush()
            handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK if unlock else msvcrt.LK_NBLCK, 1)
    else:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_UN if unlock else (fcntl.LOCK_EX | fcntl.LOCK_NB))


@contextmanager
def instance_lock(root: Path) -> Iterator[bool]:
    """Acquire a non-blocking cross-platform single-instance lock under ``root``."""
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / ".realm-desktop.lock"
    if lock_path.is_symlink():
        raise ValueError(f"Lock file cannot be a symbolic link: {lock_path}")
    handle = lock_path.open("a+b")
    acquired = False
    try:
        _lock_fd(handle, lock_path, unlock=False)
        acquired = True
    except OSError:
        acquired = False
    try:
        yield acquired
    finally:
        if acquired:
            try:
                _lock_fd(handle, lock_path, unlock=True)
            except OSError:
                pass
        handle.close()
