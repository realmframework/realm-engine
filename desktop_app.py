"""Native desktop window launcher for packaged macOS and Windows REALM Engine apps."""

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
from urllib.request import urlopen

import uvicorn

from core.runtime import data_root, is_frozen, seed_starter_vault

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
WINDOW_BG = "#04060F"


def find_available_port(preferred: int = DEFAULT_PORT, host: str = DEFAULT_HOST) -> int:
    """Use preferred localhost port when free, otherwise allocate an ephemeral port."""
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
    """Redirect missing stdio handles in windowed bundles to a local diagnostic log."""
    if not is_frozen() or (sys.stdout is not None and sys.stderr is not None):
        return
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = (log_dir / "realm-engine.log").open("a", encoding="utf-8", buffering=1)
    if sys.stdout is None:
        sys.stdout = log_file
    if sys.stderr is None:
        sys.stderr = log_file


def wait_for_health(url: str, worker: threading.Thread, timeout: float = 30.0) -> None:
    """Poll /healthz until the embedded FastAPI server is ready to serve requests."""
    deadline = time.monotonic() + timeout
    health_url = f"{url.rstrip('/')}/healthz"
    while time.monotonic() < deadline:
        if not worker.is_alive():
            raise RuntimeError("Embedded REALM Engine server exited before becoming ready")
        try:
            with urlopen(health_url, timeout=0.5) as response:
                if response.status == 200:
                    return
        except (OSError, URLError):
            pass
        time.sleep(0.1)
    raise RuntimeError(f"Timed out waiting for local server at {health_url}")


def smoke_check(url: str) -> None:
    """Verify core HTML, healthz, bundled static CSS, and frozen WebView backend."""
    base = url.rstrip("/")
    for suffix, marker in (("/healthz", b"ok"), ("/", b"<html"), ("/static/ui.css", b"{")):
        with urlopen(f"{base}{suffix}", timeout=5.0) as response:
            body = response.read(8192)
            if response.status != 200 or marker not in body.lower():
                raise RuntimeError(f"Smoke check failed for {suffix}: status={response.status}")
    if is_frozen():
        importlib.import_module("webview")
        backend = "webview.platforms.cocoa" if sys.platform == "darwin" else "webview.platforms.edgechromium"
        importlib.import_module(backend)


def open_native_window(url: str, title: str = "REALM Engine") -> None:
    """Open the native macOS/Windows WebView window and block until the user closes it."""
    webview: Any = importlib.import_module("webview")
    webview.settings["ALLOW_DOWNLOADS"] = True
    webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True
    storage = data_root() / ".webview"
    storage.mkdir(parents=True, exist_ok=True)
    webview.create_window(
        title, url, width=1360, height=880, min_size=(960, 640),
        background_color=WINDOW_BG, text_select=True, zoomable=True,
    )
    webview.start(private_mode=False, storage_path=str(storage))


def load_asgi_app() -> Any:
    """Import FastAPI app lazily after REALM_DATA_DIR and starter vault are initialized."""
    return importlib.import_module("features.ui.app").app


def run_native_desktop(
    port: int = DEFAULT_PORT,
    title: str = "REALM Engine",
    smoke_only: bool = False,
    window_runner: Callable[[str, str], None] = open_native_window,
) -> int:
    """Start the local FastAPI server, run the native window (or smoke test), then stop cleanly."""
    bound_port = find_available_port(port, DEFAULT_HOST)
    url = f"http://{DEFAULT_HOST}:{bound_port}"
    server = uvicorn.Server(uvicorn.Config(load_asgi_app(), host=DEFAULT_HOST, port=bound_port, log_config=None))
    worker = threading.Thread(target=server.run, name="realm-desktop-server", daemon=True)
    worker.start()
    try:
        wait_for_health(url, worker)
        if smoke_only:
            smoke_check(url)
        else:
            window_runner(url, title)
    finally:
        server.should_exit = True
        worker.join(timeout=5)
    return bound_port


def main(argv: list[str] | None = None) -> None:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    cleaned = [arg for arg in raw_args if not arg.startswith("-psn_")]
    parser = argparse.ArgumentParser(description="REALM Engine Desktop App")
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
    directory = data_root()
    directory.mkdir(parents=True, exist_ok=True)
    configure_frozen_stdio(directory)
    seed_starter_vault(directory)
    run_native_desktop(port=args.port, title=args.title, smoke_only=args.smoke_test)


if __name__ == "__main__":
    main()
