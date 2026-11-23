"""Repair legacy placeholder topics, run vault file watcher, and tick scheduled local workflows."""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI

from core.file_watcher import join_vault_watcher, start_vault_watcher
from core.local_ai_os import reap_stale_sidecar
from core.local_ai_sidecar import shutdown_sidecar
from core.logging_config import configure_logging
from features.ui import areas, workspace


def area_lifespan(
    repair: Callable[[Path], None],
    on_disk_change: Callable[[dict[str, list[str]]], None] | None = None,
    get_config: Callable[[], object] | None = None,
    workflow_tick: Callable[[], Awaitable[object]] | None = None,
    on_shutdown: Callable[[], None] | None = None,
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        configure_logging()
        reap_stale_sidecar(workspace.REPO_ROOT)
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
        sched_task: asyncio.Task[None] | None = None
        if workflow_tick is not None:
            tick_fn = workflow_tick

            async def _sched_loop() -> None:
                while True:
                    await asyncio.sleep(60)
                    with suppress(Exception):
                        await tick_fn()
            sched_task = asyncio.create_task(_sched_loop())
        try:
            yield
        finally:
            if sched_task is not None:
                sched_task.cancel()
                with suppress(asyncio.CancelledError):
                    await sched_task
            join_vault_watcher(stop_event, timeout=2.0)
            with suppress(Exception):
                shutdown_sidecar()
            if on_shutdown is not None:
                with suppress(Exception):
                    on_shutdown()

    return lifespan
