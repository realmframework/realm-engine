"""Native desktop window launcher for packaged macOS, Windows, and Linux REALM Engine apps."""

import argparse
import importlib
import os
import socket
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.error import URLError

import uvicorn

from core import desktop_support, logging_config, runtime, secrets
from core.version import APP_VERSION

DEFAULT_HOST, DEFAULT_PORT, WINDOW_BG = "127.0.0.1", 8000, "#04060F"
_ACTIVE_CLOSING: Callable[[], None] | None = None


def find_available_port(preferred: int = DEFAULT_PORT, host: str = DEFAULT_HOST) -> int:
    for candidate in (preferred, 0):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, candidate))
                return int(sock.getsockname()[1])
            except OSError:
                if candidate == 0:
                    raise
    return preferred

def configure_frozen_stdio(log_dir: Path) -> None:
    desktop_support.configure_desktop_logging(log_dir)

def wait_for_health(url: str, worker: threading.Thread, timeout: float = 30.0) -> None:
    deadline, health_url = time.monotonic() + timeout, f"{url.rstrip('/')}/healthz"
    while time.monotonic() < deadline:
        if not worker.is_alive():
            raise RuntimeError("Embedded REALM Engine server exited before becoming ready")
        try:
            with runtime.urlopen_loopback(health_url, timeout=0.5) as response:
                if response.status == 200:
                    return
        except (OSError, URLError):
            pass
        time.sleep(0.1)
    raise RuntimeError(f"Timed out waiting for local server at {health_url}")

def smoke_check(url: str) -> None:
    base = url.rstrip("/")
    for suffix, marker in (("/healthz", b"ok"), ("/", b"<html"), ("/static/ui.css", b"{")):
        with runtime.urlopen_loopback(f"{base}{suffix}", timeout=5.0) as response:
            body = response.read(8192)
            if response.status != 200 or marker not in body.lower():
                raise RuntimeError(f"Smoke check failed for {suffix}: status={response.status}")
    if runtime.is_frozen():
        importlib.import_module("webview")
        if sys.platform in {"darwin", "win32"}:
            importlib.import_module("webview.platforms.cocoa" if sys.platform == "darwin" else "webview.platforms.edgechromium")

def open_native_window(url: str, title: str = "REALM Engine") -> None:
    if sys.platform == "win32" and not desktop_support.has_windows_webview2():
        logging_config.get_logger("desktop").warning("WebView2 runtime missing; launching browser fallback")
        desktop_support.run_browser_fallback(url)
        return
    try:
        webview: Any = importlib.import_module("webview")
        webview.settings["ALLOW_DOWNLOADS"], webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True, True
        storage = runtime.data_root() / ".webview"
        storage.mkdir(parents=True, exist_ok=True)
        win = webview.create_window(title, url, width=1360, height=880, min_size=(960, 640), background_color=WINDOW_BG, text_select=True, zoomable=True)
        if _ACTIVE_CLOSING is not None and hasattr(win, "events") and hasattr(win.events, "closing"):
            win.events.closing += _ACTIVE_CLOSING
        webview.start(private_mode=False, storage_path=str(storage), gui="edgechromium" if sys.platform == "win32" else None)
    except Exception as exc:
        if sys.platform in {"linux", "win32"}:
            logging_config.get_logger("desktop").warning("Native WebView unavailable (%s); falling back to browser", type(exc).__name__)
            desktop_support.run_browser_fallback(url)
            return
        raise

def load_asgi_app() -> Any:
    return importlib.import_module("features.ui.app").app

def run_native_desktop(port: int = DEFAULT_PORT, title: str = "REALM Engine", smoke_only: bool = False, window_runner: Callable[[str, str], None] = open_native_window) -> int:
    global _ACTIVE_CLOSING
    bound_port = find_available_port(port, DEFAULT_HOST)
    url = f"http://{DEFAULT_HOST}:{bound_port}"
    server = uvicorn.Server(uvicorn.Config(load_asgi_app(), host=DEFAULT_HOST, port=bound_port, log_config=None, timeout_graceful_shutdown=3))
    worker = threading.Thread(target=server.run, name="realm-desktop-server", daemon=True)
    worker.start()
    def _on_closing() -> None:
        server.should_exit = True
        desktop_support.clear_active_url(runtime.data_root())
    _ACTIVE_CLOSING = _on_closing
    try:
        wait_for_health(url, worker)
        desktop_support.record_active_url(runtime.data_root(), url)
        smoke_check(url) if smoke_only else window_runner(url, title)
    finally:
        _ACTIVE_CLOSING = None
        desktop_support.clear_active_url(runtime.data_root())
        server.should_exit = True
        worker.join(timeout=5)
    return bound_port

def main(argv: list[str] | None = None) -> None:
    cleaned = [arg for arg in (sys.argv[1:] if argv is None else argv) if not arg.startswith("-psn_")]
    if cleaned and cleaned[0] in {"ask", "mcp"}:
        secrets.load_dotenv_files()
        from core.cli_commands import dispatch_cli_subcommand
        dispatch_cli_subcommand(cleaned, runtime.data_root)
        return
    parser = argparse.ArgumentParser(description="REALM Engine Desktop App")
    parser.add_argument("--version", action="version", version=f"REALM Engine {APP_VERSION}")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--data-dir", type=Path, help="Override the local vault and settings folder")
    parser.add_argument("--title", default="REALM Engine")
    parser.add_argument("--smoke-test", action="store_true", help="Verify startup and static assets without opening a window")
    args = parser.parse_args(cleaned)
    if not 1 <= args.port <= 65535:
        parser.error("Port must be between 1 and 65535")
    os.environ["REALM_MODE"] = "local"
    if args.data_dir:
        os.environ["REALM_DATA_DIR"] = str(args.data_dir.expanduser().resolve())
    secrets.load_dotenv_files()
    directory = runtime.data_root()
    directory.mkdir(parents=True, exist_ok=True)
    configure_frozen_stdio(directory)
    try:
        with runtime.instance_lock(directory) as acquired:
            if not acquired:
                if not args.smoke_test:
                    desktop_support.focus_existing_instance(directory)
                print("REALM Engine is already running for this data directory.")
                return
            runtime.seed_starter_vault(directory)
            run_native_desktop(port=args.port, title=args.title, smoke_only=args.smoke_test)
    except Exception as exc:
        logging_config.get_logger("desktop").exception("Fatal desktop startup error")
        if runtime.is_frozen() and not args.smoke_test:
            desktop_support.show_native_error("REALM Engine could not start", f"{exc}\n\nDiagnostic log:\n{logging_config.log_file_path(directory)}")
        raise

if __name__ == "__main__":
    main()
