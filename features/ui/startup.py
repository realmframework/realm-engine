"""Repair legacy placeholder topics when available local knowledge areas start up."""

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from features.ui import areas, workspace


def area_lifespan(repair: Callable[[Path], None]) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        with workspace.STATE_LOCK:
            workspace.REPO_ROOT.mkdir(parents=True, exist_ok=True)
            active = workspace.load_workspace_config().knowledge_dir
            for area in areas.list_areas(workspace.REPO_ROOT, active):
                directory = areas.area_path(area.name, workspace.REPO_ROOT)
                repair(directory)
        yield

    return lifespan
