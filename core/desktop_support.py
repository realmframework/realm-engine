"""Cross-platform desktop diagnostics, native error alerts, WebView2 checks, and browser fallback."""

import os
import subprocess
import sys
import webbrowser
from contextlib import suppress
from pathlib import Path

from core.logging_config import configure_logging, log_file_path
from core.runtime import is_frozen

ACTIVE_URL_FILE = ".realm-active-url"


def _is_devnull_stream(stream: object) -> bool:
    if stream is None:
        return True
    try:
        fileno = getattr(stream, "fileno", None)
        if callable(fileno):
            fd = int(str(fileno()))
            return os.path.samefile(f"/dev/fd/{fd}", os.devnull) if sys.platform == "darwin" else False
    except (OSError, ValueError):
        return False
    return False


def configure_desktop_logging(data_dir: Path) -> Path:
    """Configure rotating 0600 logs and redirect missing/devnull frozen stdio handles."""
    configure_logging(data_dir)
    target = log_file_path(data_dir)
    if not is_frozen():
        return target
    if not _is_devnull_stream(sys.stdout) and not _is_devnull_stream(sys.stderr):
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or target.parent.is_symlink():
        return target
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(target, flags, 0o600)
        handle = os.fdopen(fd, "a", encoding="utf-8", buffering=1)
        if _is_devnull_stream(sys.stdout):
            sys.stdout = handle
        if _is_devnull_stream(sys.stderr):
            sys.stderr = handle
    except OSError:
        pass
    return target


def show_native_error(title: str, message: str) -> None:
    """Display a native OS alert when a windowed desktop build hits a fatal startup error."""
    safe_title, safe_msg = title.replace("\x00", "").strip()[:120] or "REALM Engine", message.replace("\x00", "").strip()[:900]
    try:
        if sys.platform == "darwin":
            cmd = ["osascript", "-e", "on run argv", "-e", 'display dialog (item 2 of argv) with title (item 1 of argv) buttons {"OK"} default button "OK" with icon stop', "-e", "end run", "--", safe_title, safe_msg]
            subprocess.run(cmd, capture_output=True, timeout=30, check=False)
            return
        if sys.platform == "win32":
            import ctypes
            if (user32 := getattr(getattr(ctypes, "windll", None), "user32", None)) is not None:
                user32.MessageBoxW(0, safe_msg, safe_title, 0x10)
                return
        for cmd in (["zenity", "--error", f"--title={safe_title}", f"--text={safe_msg}"], ["kdialog", "--error", safe_msg, "--title", safe_title]):
            try:
                subprocess.run(cmd, capture_output=True, timeout=30, check=False)
                return
            except FileNotFoundError:
                continue
    except (OSError, subprocess.SubprocessError):
        pass
    sys.stderr.write(f"{safe_title}: {safe_msg}\n")


def has_windows_webview2() -> bool:
    """Check whether Microsoft Edge WebView2 Runtime is installed on Windows."""
    if sys.platform != "win32":
        return True
    try:
        import winreg

        guid = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
        roots = [
            (winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{guid}"),
            (winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{guid}"),
            (winreg.HKEY_CURRENT_USER, rf"Software\Microsoft\EdgeUpdate\Clients\{guid}"),
        ]
        for hive, subkey in roots:
            try:
                with winreg.OpenKey(hive, subkey) as key:
                    val, _ = winreg.QueryValueEx(key, "pv")
                    if str(val).strip() and str(val).strip() != "0.0.0.0":
                        return True
            except OSError:
                continue
    except ImportError:
        return True
    return False


def record_active_url(data_dir: Path, url: str) -> None:
    path = data_dir / ACTIVE_URL_FILE
    if not path.is_symlink():
        with suppress(OSError):
            path.write_text(url.strip() + "\n", encoding="utf-8")
            if os.name != "nt":
                os.chmod(path, 0o600)

def clear_active_url(data_dir: Path) -> None:
    from core.local_ai_sidecar import shutdown_sidecar

    with suppress(Exception):
        shutdown_sidecar()
    path = data_dir / ACTIVE_URL_FILE
    if not path.is_symlink():
        with suppress(OSError):
            path.unlink(missing_ok=True)

def focus_existing_instance(data_dir: Path) -> bool:
    """Bring an already-running desktop app to front or open its active local URL."""
    path = data_dir / ACTIVE_URL_FILE
    url = ""
    if path.is_file() and not path.is_symlink():
        with suppress(OSError):
            cand = path.read_text(encoding="utf-8").strip()
            if cand.startswith(("http://127.0.0.1:", "http://localhost:")):
                url = cand
    if sys.platform == "darwin" and is_frozen():
        with suppress(OSError, subprocess.SubprocessError):
            subprocess.run(["osascript", "-e", 'tell application "REALM Engine" to activate'], capture_output=True, timeout=3, check=False)
            return True
    if url:
        with suppress(Exception):
            webbrowser.open(url, new=1)
            return True
    return False


def run_browser_fallback(url: str) -> None:
    """Open local URL in browser app mode and block cleanly until interrupted."""
    import time

    import main as launcher

    launcher.open_desktop_window(url)
    with suppress(KeyboardInterrupt):
        while True:
            time.sleep(0.5)
