"""Lightweight, dependency-free incremental file-mtime watcher for local & linked vaults."""

import os
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from core.logging_config import get_logger

WATCHED_EXTENSIONS = {".md", ".txt", ".html", ".pdf", ".docx", ".csv", ".tsv", ".xlsx", ".pptx"}
_SYNC_STATE: dict[str, object] = {"watching": False, "last_sync_at": "", "last_changed_files": [], "sync_version": 0, "owner": 0}
_SYNC_LOCK = threading.Lock()
_WATCHER_THREADS: dict[int, threading.Thread] = {}
_LOG = get_logger("watcher")
FileStamp = tuple[int, int]


def scan_directory_mtimes(directory: Path) -> dict[str, FileStamp] | None:
    """Return {rel_posix: (mtime_ns, size)} or None on directory error so drives never false-delete."""
    if not directory.is_dir() or directory.is_symlink():
        return None
    found: dict[str, FileStamp] = {}
    try:
        resolved_root = directory.resolve()
        for cur_root, dirnames, filenames in os.walk(directory, followlinks=False):
            root_path = Path(cur_root)
            dirnames[:] = [d for d in dirnames if not d.startswith(".") and not (root_path / d).is_symlink()]
            for fname in filenames:
                if fname.startswith("."):
                    continue
                path = root_path / fname
                if path.suffix.lower() not in WATCHED_EXTENSIONS or path.is_symlink():
                    continue
                try:
                    if not path.resolve().is_relative_to(resolved_root):
                        continue
                    st = path.stat()
                    found[path.relative_to(directory).as_posix()] = (st.st_mtime_ns, st.st_size)
                except OSError:
                    continue
    except OSError:
        return None
    return found


def diff_snapshots(previous: dict[str, FileStamp], current: dict[str, FileStamp]) -> tuple[list[str], list[str], list[str]]:
    added = sorted(p for p in current if p not in previous)
    removed = sorted(p for p in previous if p not in current)
    modified = sorted(p for p, stamp in current.items() if p in previous and previous[p] != stamp)
    return added, modified, removed

def poll_watch_cycle(dirs: dict[str, Path], snapshots: dict[str, dict[str, FileStamp]], *, commit: bool = True) -> dict[str, list[str]]:
    changes: dict[str, list[str]] = {}
    pending: dict[str, dict[str, FileStamp]] = {}
    for stale in [k for k in snapshots if k not in dirs]:
        snapshots.pop(stale, None)
    for name, directory in dirs.items():
        current = scan_directory_mtimes(directory)
        if current is None:
            continue
        if name not in snapshots:
            snapshots[name] = current
            continue
        added, modified, removed = diff_snapshots(snapshots[name], current)
        if added or modified or removed:
            pending[name] = current
            changes[name] = [*added, *modified, *removed]
    if commit:
        snapshots.update(pending)
    return changes

def record_sync_event(changed_files: list[str]) -> None:
    with _SYNC_LOCK:
        _SYNC_STATE["last_sync_at"] = datetime.now(UTC).isoformat()
        _SYNC_STATE["last_changed_files"] = list(changed_files[:12])
        _SYNC_STATE["sync_version"] = int(str(_SYNC_STATE.get("sync_version") or 0)) + 1

def get_sync_status() -> dict[str, object]:
    with _SYNC_LOCK:
        raw_files = _SYNC_STATE.get("last_changed_files")
        return {"watching": bool(_SYNC_STATE.get("watching")), "last_sync_at": str(_SYNC_STATE.get("last_sync_at") or ""), "last_changed_files": [str(f) for f in raw_files] if isinstance(raw_files, list) else [], "sync_version": int(str(_SYNC_STATE.get("sync_version") or 0))}


def start_vault_watcher(
    get_dirs: Callable[[], dict[str, Path]],
    on_changes: Callable[[dict[str, list[str]]], None],
    interval_sec: float = 4.0,
) -> threading.Event:
    """Start a low-overhead background daemon polling (mtime, size); returns stop_event."""
    stop_event = threading.Event()
    if os.environ.get("REALM_DISABLE_WATCHER") == "1" or os.environ.get("PYTEST_CURRENT_TEST"):
        return stop_event
    snapshots: dict[str, dict[str, FileStamp]] = {}

    def _loop() -> None:
        with _SYNC_LOCK:
            owner_id = int(str(_SYNC_STATE.get("owner") or 0)) + 1
            _SYNC_STATE["owner"] = owner_id
            _SYNC_STATE["watching"] = True
        try:
            try:
                poll_watch_cycle(get_dirs(), snapshots)
            except Exception as exc:
                _LOG.warning("Initial vault watcher scan failed: %s", type(exc).__name__)
            while not stop_event.wait(interval_sec):
                try:
                    dirs = get_dirs()
                    next_snaps = {k: dict(v) for k, v in snapshots.items()}
                    changes = poll_watch_cycle(dirs, next_snaps)
                    if changes:
                        flat = [f"{area}/{p}" for area, paths in changes.items() for p in paths]
                        on_changes(changes)
                        snapshots.clear()
                        snapshots.update(next_snaps)
                        record_sync_event(flat)
                    else:
                        snapshots.clear()
                        snapshots.update(next_snaps)
                except Exception as exc:
                    _LOG.warning("Vault watcher cycle error: %s", type(exc).__name__)
        finally:
            with _SYNC_LOCK:
                if _SYNC_STATE.get("owner") == owner_id:
                    _SYNC_STATE["watching"] = False
                _WATCHER_THREADS.pop(id(stop_event), None)

    thread = threading.Thread(target=_loop, name="realm-file-watcher", daemon=True)
    with _SYNC_LOCK:
        _WATCHER_THREADS[id(stop_event)] = thread
    thread.start()
    return stop_event


def join_vault_watcher(stop_event: threading.Event, timeout: float = 2.0) -> None:
    """Signal and join a vault watcher thread cleanly on server shutdown."""
    stop_event.set()
    with _SYNC_LOCK:
        thread = _WATCHER_THREADS.get(id(stop_event))
    if thread is not None and thread.is_alive():
        thread.join(timeout=timeout)
