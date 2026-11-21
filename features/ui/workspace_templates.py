"""Create new isolated workspaces with optional physical-folder starter templates."""

import re
import shutil
from collections.abc import Callable
from contextlib import suppress

from fastapi import APIRouter, HTTPException, Request

from core.contracts import WorkspaceConfig
from core.db import atomic_write_bytes
from core.linked_vaults import is_linked_vault
from core.runtime import copy_starter_welcome
from features.ui import areas, workspace

TEMPLATES = {
    "blank": (),
    "starter": (),
    "care": ("care_plans", "protocols", "daily_notes"),
    "finance": ("contracts", "invoices", "taxes"),
    "study": ("subjects", "notes", "assignments"),
}


def build_router(config: Callable[[], WorkspaceConfig], activate: Callable[[WorkspaceConfig], dict[str, object]]) -> APIRouter:
    router = APIRouter()

    @router.post("/api/workspace/create")
    def create(payload: dict[str, str], request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            name, template = payload.get("name", ""), payload.get("template", "blank")
            if template not in TEMPLATES or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", name) or name in areas.RESERVED_DIRS:
                raise HTTPException(status_code=400, detail="Choose a template and a folder name using lowercase letters, numbers, underscores or hyphens.")
            candidate = workspace.REPO_ROOT / name
            if candidate.exists() or candidate.is_symlink() or is_linked_vault(name, workspace.REPO_ROOT):
                raise HTTPException(status_code=409, detail="That workspace already exists. Choose another name or open it from the sidebar.")
            if workspace.WORKSPACE_FILE.is_symlink():
                raise HTTPException(status_code=400, detail="Workspace configuration cannot be a symbolic link.")
            original = workspace.WORKSPACE_FILE.read_bytes() if workspace.WORKSPACE_FILE.exists() else None
            try:
                candidate.mkdir()
            except OSError as exc:
                raise HTTPException(status_code=409, detail="That workspace could not be created. Choose another name and try again.") from exc
            try:
                directory = areas.area_path(name, workspace.REPO_ROOT, create=True)
                for folder in TEMPLATES[template]:
                    (directory / folder).mkdir()
                if template == "starter":
                    copy_starter_welcome(directory)
                strict = active.strict_local_only or template in {"care", "finance"}
                next_config = active.model_copy(update={"knowledge_dir": name, "active_dirs": [name], "strict_local_only": strict, "run_mode": "local" if strict and active.run_mode == "cloud" else active.run_mode})
                return activate(next_config)
            except Exception:
                with suppress(Exception):
                    activate(active)
                if original is None:
                    workspace.WORKSPACE_FILE.unlink(missing_ok=True)
                else:
                    atomic_write_bytes(workspace.WORKSPACE_FILE, original)
                if candidate.is_dir() and not candidate.is_symlink():
                    shutil.rmtree(candidate)
                raise

    return router
