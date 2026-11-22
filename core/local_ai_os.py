"""Cross-platform OS helpers for Built-in Private AI sidecar safety, cores & cleanup."""

from __future__ import annotations

import ctypes
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any

_CACHED_CORES: int | None = None
_JOB_LIMIT_KILL_ON_CLOSE = 0x00002000
_JOB_EXTENDED_LIMIT_INFO = 9
_WIN_CREATE_NO_WINDOW = 0x08000000
_WIN_BELOW_NORMAL_PRIORITY = 0x00004000


def detect_physical_cores() -> int:
    """Return physical performance cores (Apple Silicon P-cores aware, safe fallback)."""
    global _CACHED_CORES
    if not os.environ.get("PYTEST_CURRENT_TEST") and _CACHED_CORES is not None:
        return _CACHED_CORES
    detected = 0
    if sys.platform == "darwin":
        for key in ("hw.perflevel0.physicalcpu", "hw.physicalcpu"):
            try:
                out = subprocess.run(["sysctl", "-n", key], capture_output=True, text=True, timeout=1, check=True)
                if (val := int(out.stdout.strip())) > 0:
                    detected = val
                    break
            except (OSError, ValueError, subprocess.SubprocessError):
                continue
    if detected <= 0:
        detected = max(2, (os.cpu_count() or 4) // 2)
    if not os.environ.get("PYTEST_CURRENT_TEST"):
        _CACHED_CORES = detected
    return detected


def popen_platform_kwargs() -> dict[str, Any]:
    """Return subprocess kwargs that hide console windows and lower CPU priority."""
    if sys.platform == "win32":
        return {"creationflags": _WIN_CREATE_NO_WINDOW | _WIN_BELOW_NORMAL_PRIORITY}
    nice_fn = getattr(os, "nice", None)

    def _lower_priority() -> None:
        if callable(nice_fn):
            try:
                nice_fn(10)
            except OSError:
                pass

    return {"start_new_session": True, "preexec_fn": _lower_priority}


def attach_windows_job_object(proc_handle: int) -> int | None:
    """Bind a child process on Windows to a Job Object that kills it if REALM exits."""
    if sys.platform != "win32":
        return None
    loader = getattr(ctypes, "windll", None)
    if loader is None:
        return None
    try:
        k32 = loader.kernel32
        job = int(k32.CreateJobObjectW(None, None))
        if not job:
            return None
        # JOBOBJECT_EXTENDED_LIMIT_INFORMATION (144 bytes on 64-bit; LimitFlags at offset 16)
        buf = ctypes.create_string_buffer(144)
        ctypes.c_uint32.from_buffer(buf, 16).value = _JOB_LIMIT_KILL_ON_CLOSE
        ok = k32.SetInformationJobObject(ctypes.c_void_p(job), _JOB_EXTENDED_LIMIT_INFO, buf, len(buf))
        if not ok or not k32.AssignProcessToJobObject(ctypes.c_void_p(job), ctypes.c_void_p(proc_handle)):
            k32.CloseHandle(ctypes.c_void_p(job))
            return None
        return job
    except (OSError, AttributeError, ValueError):
        return None


def close_windows_job_object(job_handle: int | None) -> None:
    if sys.platform != "win32" or not job_handle:
        return
    loader = getattr(ctypes, "windll", None)
    if loader is not None:
        try:
            loader.kernel32.CloseHandle(ctypes.c_void_p(job_handle))
        except (OSError, AttributeError):
            pass


def _pid_is_llama_server(pid: int) -> bool:
    if pid <= 1:
        return False
    try:
        if sys.platform == "win32":
            res = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True, timeout=2, check=False)
            return "llama-server" in res.stdout.lower()
        res = subprocess.run(["ps", "-p", str(pid), "-o", "comm="], capture_output=True, text=True, timeout=2, check=False)
        return "llama-server" in res.stdout.lower()
    except (OSError, subprocess.SubprocessError):
        return False


def write_pid_file(pid_path: Path, pid: int) -> None:
    if pid_path.is_symlink():
        return
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text(f"{pid}\n", encoding="utf-8")


def reap_stale_sidecar(data_dir: Path) -> bool:
    """Terminate an orphaned llama-server process left over from a previous crash."""
    pid_path = data_dir / "runtime" / "local_ai" / "llama-server.pid"
    if not pid_path.is_file() or pid_path.is_symlink():
        return False
    killed = False
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
        if _pid_is_llama_server(pid):
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=3, check=False)
            else:
                os.kill(pid, signal.SIGTERM)
            killed = True
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    finally:
        pid_path.unlink(missing_ok=True)
    return killed


def terminate_process(proc: subprocess.Popen[Any] | None, pid_path: Path | None = None, job_handle: int | None = None, timeout: float = 4.0) -> None:
    """Gracefully terminate a child process with hard-kill fallback and handle cleanup."""
    if proc is not None and proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=timeout)
        except (OSError, subprocess.TimeoutExpired):
            try:
                proc.kill()
                proc.wait(timeout=2.0)
            except (OSError, subprocess.SubprocessError):
                pass
    close_windows_job_object(job_handle)
    if pid_path is not None and not pid_path.is_symlink():
        pid_path.unlink(missing_ok=True)
