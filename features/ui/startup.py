"""Repair legacy placeholder topics and run lightweight incremental file watcher on startup."""

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from core.file_watcher import join_vault_watcher, start_vault_watcher
from core.logging_config import configure_logging
from features.ui import areas, workspace


def area_lifespan(
    repair: Callable[[Path], None],
    on_disk_change: Callable[[dict[str, list[str]]], None] | None = None,
    get_config: Callable[[], object] | None = None,
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        configure_logging()
        with workspace.STATE_LOCK:
            workspace.REPO_ROOT.mkdir(parents=True, exist_ok=True)
            active = workspace.load_workspace_config().knowledge_dir
            for area in areas.list_areas(workspace.REPO_ROOT, active):
                if area.linked:
                    continue
                directory = areas.area_path(area.name, workspace.REPO_ROOT)
                repair(directory)

        def _active_dirs() -> dict[str, Path]:
            with workspace.STATE_LOCK:
                cfg = get_config() if get_config is not None else workspace.load_workspace_config()
                active_list = getattr(cfg, "active_dirs", [])
                resolved: dict[str, Path] = {}
                for name in active_list:
                    try:
                        resolved[str(name)] = areas.area_path(str(name), workspace.REPO_ROOT)
                    except ValueError:
                        continue
                return resolved

        stop_event = start_vault_watcher(_active_dirs, on_disk_change or (lambda _c: None))
        try:
            yield
        finally:
            join_vault_watcher(stop_event, timeout=2.0)

    return lifespan
