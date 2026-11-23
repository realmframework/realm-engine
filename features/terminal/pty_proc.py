"""Low-level OS shell process helpers (POSIX PTY + Windows pipe fallback)."""

from __future__ import annotations

import os
import shutil
import signal
import struct
import subprocess
import sys
from contextlib import suppress
from pathlib import Path

if sys.platform != "win32":
    import fcntl
    import pty
    import termios


def default_shell() -> tuple[list[str], str]:
    if sys.platform == "win32":
        exe = shutil.which("pwsh") or shutil.which("powershell.exe") or os.environ.get("COMSPEC") or "cmd.exe"
        args = [exe, "-NoLogo"] if "powershell" in exe.lower() or "pwsh" in exe.lower() else [exe]
        return args, Path(exe).name
    exe = os.environ.get("SHELL") or ("/bin/zsh" if Path("/bin/zsh").exists() else "/bin/sh")
    return [exe, "-i"], Path(exe).name


def set_winsize(fd: int, cols: int, rows: int) -> None:
    if sys.platform != "win32":
        with suppress(OSError):
            fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))


def spawn_shell(cwd: Path, cols: int, rows: int) -> tuple[subprocess.Popen[bytes], int | None, str]:
    argv, shell_name = default_shell()
    env = {**os.environ, "TERM": "xterm-256color", "COLORTERM": "truecolor", "CLICOLOR": "1", "FORCE_COLOR": "1", "REALM_WORKSPACE": str(cwd)}
    if sys.platform != "win32":
        master_fd, slave_fd = pty.openpty()
        set_winsize(master_fd, cols, rows)
        try:
            proc = subprocess.Popen(argv, cwd=str(cwd), env=env, stdin=slave_fd, stdout=slave_fd, stderr=slave_fd, start_new_session=True, close_fds=True)
        except Exception:
            os.close(master_fd)
            os.close(slave_fd)
            raise
        os.close(slave_fd)
        return proc, master_fd, shell_name
    proc = subprocess.Popen(argv, cwd=str(cwd), env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
    return proc, None, shell_name


def resize_proc(proc: subprocess.Popen[bytes], master_fd: int | None, cols: int, rows: int) -> None:
    if master_fd is not None:
        set_winsize(master_fd, cols, rows)
        if sys.platform != "win32":
            with suppress(OSError):
                os.killpg(proc.pid, signal.SIGWINCH)


def terminate_proc(proc: subprocess.Popen[bytes], master_fd: int | None) -> None:
    if proc.poll() is None:
        if sys.platform != "win32":
            with suppress(OSError):
                os.killpg(proc.pid, signal.SIGTERM)
        else:
            with suppress(OSError):
                proc.terminate()
        with suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=1.0)
        if proc.poll() is None:
            with suppress(OSError):
                proc.kill()
    if master_fd is not None:
        with suppress(OSError):
            os.close(master_fd)
