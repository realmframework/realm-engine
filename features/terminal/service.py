"""Local interactive terminal session registry and streaming buffer."""

from __future__ import annotations

import atexit
import os
import subprocess
import threading
from collections import deque
from contextlib import suppress
from pathlib import Path
from typing import Any
from uuid import uuid4

from core.terminal_contracts import TerminalSessionInfo
from features.terminal import pty_proc

MAX_SESSIONS = 6
MAX_HISTORY_EVENTS = 1500
_LOCK = threading.RLock()
_SESSIONS: dict[str, dict[str, Any]] = {}


def _session_info(entry: dict[str, Any]) -> TerminalSessionInfo:
    code = entry["proc"].poll()
    return TerminalSessionInfo(
        id=str(entry["id"]),
        label=str(entry["label"]),
        shell=str(entry["shell"]),
        cwd=str(entry["cwd"]),
        running=code is None,
        exit_code=code,
    )


def _reader_loop(entry: dict[str, Any]) -> None:
    cond: threading.Condition = entry["cond"]
    history: deque[tuple[int, str]] = entry["history"]
    master_fd: int | None = entry["master_fd"]
    proc: subprocess.Popen[bytes] = entry["proc"]
    try:
        while True:
            raw = os.read(master_fd, 4096) if master_fd is not None else (proc.stdout.read(4096) if proc.stdout is not None else b"")
            if not raw:
                break
            text = raw.decode("utf-8", errors="replace")
            with cond:
                entry["seq"] += 1
                history.append((entry["seq"], text))
                cond.notify_all()
    except OSError:
        pass
    finally:
        with suppress(Exception):
            proc.wait(timeout=0.5)
        with cond:
            entry["closed"] = True
            cond.notify_all()


def create_session(cwd: Path, label: str = "", cols: int = 100, rows: int = 24) -> TerminalSessionInfo:
    safe_cwd = cwd if cwd.is_dir() else Path.home()
    with _LOCK:
        if sum(1 for e in _SESSIONS.values() if e["proc"].poll() is None) >= MAX_SESSIONS:
            raise OverflowError(f"Maximum of {MAX_SESSIONS} active terminal sessions reached.")
        sid = f"term_{uuid4().hex[:8]}"
        proc, master_fd, shell_name = pty_proc.spawn_shell(safe_cwd, cols, rows)
        idx = len(_SESSIONS) + 1
        entry: dict[str, Any] = {
            "id": sid, "label": (label.strip() or f"{shell_name} #{idx}")[:48], "shell": shell_name, "cwd": str(safe_cwd),
            "proc": proc, "master_fd": master_fd, "history": deque(maxlen=MAX_HISTORY_EVENTS), "seq": 0, "cond": threading.Condition(), "closed": False,
        }
        _SESSIONS[sid] = entry
        threading.Thread(target=_reader_loop, args=(entry,), name=f"realm-{sid}", daemon=True).start()
        return _session_info(entry)


def list_sessions() -> list[TerminalSessionInfo]:
    with _LOCK:
        return [_session_info(e) for e in _SESSIONS.values()]


def get_session_entry(session_id: str) -> dict[str, Any] | None:
    with _LOCK:
        return _SESSIONS.get(session_id)


def write_input(session_id: str, data: str) -> None:
    entry = get_session_entry(session_id)
    if entry is None:
        raise KeyError("Terminal session not found")
    payload = data.encode("utf-8", errors="replace")
    if entry["master_fd"] is not None:
        os.write(entry["master_fd"], payload)
    elif entry["proc"].stdin is not None:
        entry["proc"].stdin.write(payload)
        entry["proc"].stdin.flush()


def send_signal(session_id: str, sig_name: str) -> None:
    entry = get_session_entry(session_id)
    if entry is None:
        raise KeyError("Terminal session not found")
    if entry["master_fd"] is not None:
        os.write(entry["master_fd"], b"\x03" if sig_name == "interrupt" else b"\x04")
    elif sig_name == "interrupt":
        with suppress(OSError):
            entry["proc"].terminate()


def resize_session(session_id: str, cols: int, rows: int) -> None:
    entry = get_session_entry(session_id)
    if entry is None:
        raise KeyError("Terminal session not found")
    pty_proc.resize_proc(entry["proc"], entry["master_fd"], cols, rows)


def close_session(session_id: str) -> bool:
    with _LOCK:
        entry = _SESSIONS.pop(session_id, None)
    if entry is None:
        return False
    pty_proc.terminate_proc(entry["proc"], entry["master_fd"])
    entry["master_fd"] = None
    with entry["cond"]:
        entry["closed"] = True
        entry["cond"].notify_all()
    return True


def close_all_sessions() -> None:
    with _LOCK:
        ids = list(_SESSIONS.keys())
    for sid in ids:
        close_session(sid)


atexit.register(close_all_sessions)
