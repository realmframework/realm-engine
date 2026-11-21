"""Local web server and optional Chromium desktop app window launcher."""

import argparse
import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib.error import URLError

import uvicorn

from core import secrets
from core.runtime import data_root, seed_starter_vault, urlopen_loopback
from core.version import APP_VERSION


def find_app_browser() -> str | None:
    """Find Chrome, Brave or Edge without requiring a desktop wrapper dependency."""
    candidates: list[Path] = []
    if sys.platform == "darwin":
        for directory in (Path("/Applications"), Path.home() / "Applications"):
            for app, binary in (("Google Chrome", "Google Chrome"), ("Brave Browser", "Brave Browser"), ("Microsoft Edge", "Microsoft Edge")):
                candidates.append(directory / f"{app}.app/Contents/MacOS/{binary}")
    elif sys.platform == "win32":
        for variable in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            if directory := os.environ.get(variable):
                candidates.extend(Path(directory) / path for path in (
                    "Google/Chrome/Application/chrome.exe", "BraveSoftware/Brave-Browser/Application/brave.exe",
                    "Microsoft/Edge/Application/msedge.exe",
                ))
    for name in ("google-chrome", "chromium", "chromium-browser", "brave-browser", "microsoft-edge", "chrome", "msedge", "brave"):
        if executable := shutil.which(name):
            candidates.append(Path(executable))
    return next((str(path) for path in candidates if path.is_file()), None)


def open_desktop_window(url: str) -> bool:
    if browser := find_app_browser():
        try:
            subprocess.Popen([browser, f"--app={url}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except OSError:
            pass
    return webbrowser.open(url, new=1)


def server_ready(url: str) -> bool:
    try:
        with urlopen_loopback(url, timeout=0.5) as response:
            return response.status == 200 and b"REALM Engine" in response.read(4096)
    except (OSError, URLError):
        return False


def run_desktop(host: str, port: int, reuse: bool = True) -> None:
    url = f"http://{host if host in {'127.0.0.1', 'localhost'} else '127.0.0.1'}:{port}"
    if reuse and server_ready(url):
        open_desktop_window(url)
        print(f"Opened existing local server at {url}")
        return
    server = uvicorn.Server(uvicorn.Config("features.ui.app:app", host=host, port=port, timeout_graceful_shutdown=3))
    worker = threading.Thread(target=server.run, name="realm-web-server", daemon=True)
    worker.start()
    try:
        deadline = time.monotonic() + 30
        while not server_ready(url):
            if not worker.is_alive() or time.monotonic() >= deadline:
                raise RuntimeError("The local server could not start; check the port and server output")
            time.sleep(0.1)
        open_desktop_window(url)
        print(f"Desktop UI: {url}. Press Ctrl+C here to stop the server.")
        while worker.is_alive():
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.should_exit = True
        worker.join(timeout=5)


def build_indexes(root: Path, area_names: list[str], embed_provider: str = "none") -> int:
    from core.db import load_chunks, save_chunks
    from core.linked_vaults import cache_index_for_dir
    from features.ingestion.embedder import hydrate_embeddings
    from features.ingestion.service import ingest_directory
    from features.ui import areas
    targets, total_chunks = area_names or [a.name for a in areas.list_areas(root) if (root / a.name).is_dir()], 0
    for name in targets:
        target = areas.area_path(name, root, create=False)
        cache = cache_index_for_dir(target, root)
        if cache.is_symlink():
            raise ValueError(f"Area index cannot be a symbolic link: {cache}")
        cached = load_chunks(cache) if cache.is_file() else []
        chunks = hydrate_embeddings(ingest_directory(target, read_only=target.resolve().parent != root.resolve()), cached, embed_missing=embed_provider != "none", provider=embed_provider)
        save_chunks(chunks, cache)
        total_chunks += len(chunks)
    return total_chunks
def main(argv: list[str] | None = None) -> None:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    secrets.load_dotenv_files()
    if raw_argv and raw_argv[0] in {"ask", "mcp"}:
        from core.cli_commands import dispatch_cli_subcommand
        dispatch_cli_subcommand(raw_argv, data_root)
        return
    parser = argparse.ArgumentParser(description="REALM Engine")
    parser.add_argument("--version", action="version", version=f"REALM Engine {APP_VERSION}")
    parser.add_argument("--desktop", action="store_true", help="Open a tabless Chrome/Brave/Edge app window, with browser fallback")
    parser.add_argument("--public", action="store_true", help="Serve the stateless read-only public API mode (REALM_MODE=public)")
    parser.add_argument("--build-index", action="store_true", help="Pre-build index.json for vaults and exit")
    parser.add_argument("--embed-provider", default="none", choices=("none", "ollama", "openai", "mistral", "gemini"), help="Embedding provider for --build-index")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--data-dir", type=Path, help="Directory containing knowledge areas, workspace settings and chats")
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("Port must be between 1 and 65535")
    if args.desktop and args.public:
        parser.error("Cannot combine --desktop and --public modes")
    if args.desktop and args.host not in {"127.0.0.1", "localhost"}:
        parser.error("Desktop mode uses the local loopback interface")
    if args.public:
        os.environ["REALM_MODE"] = "public"
    if args.data_dir:
        os.environ["REALM_DATA_DIR"] = str(args.data_dir.expanduser().resolve())
        secrets.load_dotenv_files()
    directory = data_root()
    directory.mkdir(parents=True, exist_ok=True)
    if args.build_index:
        raw = [a.strip() for a in os.environ.get("REALM_PUBLIC_AREAS", "").split(",") if a.strip()]
        count = build_indexes(directory, raw, embed_provider=args.embed_provider)
        print(f"Indexed {count} chunks under {directory}")
        return
    if not args.public:
        seed_starter_vault(directory)
        if args.host not in {"127.0.0.1", "localhost", "::1"} and os.environ.get("REALM_ALLOW_NON_LOOPBACK", "").strip() != "1":
            sys.stderr.write("Warning: binding local admin mode to a non-loopback address; prefer 127.0.0.1 or --public.\n")
    if args.desktop:
        run_desktop(args.host, args.port, reuse=args.data_dir is None)
    else:
        uvicorn.run("features.ui.app:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
