"""Workspace appearance settings and custom logo upload/reset with strict binary validation."""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from core.contracts import AppearanceUpdate, WorkspaceConfig
from core.runtime import bundle_root
from features.ui import workspace

MAX_LOGO_BYTES = 2 * 1024 * 1024
LOGO_MEDIA_TYPES: dict[str, str] = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}
LOGO_STEM = "custom_logo"


def _detect_image_ext(data: bytes) -> str | None:
    """Validate raster image magic bytes only (blocks SVG/HTML script injection)."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


def _find_custom_logo(root: Path) -> Path | None:
    for ext in LOGO_MEDIA_TYPES:
        candidate = root / f"{LOGO_STEM}{ext}"
        if not candidate.is_symlink() and candidate.is_file():
            return candidate
    return None


def _clear_custom_logos(root: Path) -> None:
    for ext in LOGO_MEDIA_TYPES:
        candidate = root / f"{LOGO_STEM}{ext}"
        if candidate.is_symlink():
            raise HTTPException(status_code=400, detail="Custom logo path cannot be a symbolic link")
        if candidate.is_file():
            candidate.unlink()


def build_router(
    get_config: Callable[[], WorkspaceConfig],
    set_config: Callable[[WorkspaceConfig], None],
) -> APIRouter:
    router = APIRouter()
    default_logo = bundle_root() / "features" / "ui" / "static" / "logo-512.png"

    @router.post("/api/workspace/appearance")
    def save_appearance(update: AppearanceUpdate) -> dict[str, object]:
        with workspace.STATE_LOCK:
            updated = get_config().model_copy(update=update.model_dump(exclude_unset=True))
            workspace.save_workspace_config(updated)
            set_config(updated)
        return {"config": updated.model_dump()}

    @router.post("/api/workspace/reset-defaults")
    def reset_all_defaults() -> dict[str, object]:
        """Restore REALM default settings & logo without touching user vaults, guides, or chats."""
        with workspace.STATE_LOCK:
            current = get_config()
            _clear_custom_logos(workspace.REPO_ROOT)
            restored = WorkspaceConfig(
                knowledge_dir=current.knowledge_dir,
                active_dirs=list(current.active_dirs),
            )
            workspace.save_workspace_config(restored)
            set_config(restored)
        return {"config": restored.model_dump(), "logo_url": "/static/logo-512.png"}

    @router.get("/api/workspace/logo")
    def get_logo() -> FileResponse:
        with workspace.STATE_LOCK:
            custom = _find_custom_logo(workspace.REPO_ROOT)
        target = custom or default_logo
        media_type = LOGO_MEDIA_TYPES.get(target.suffix.lower(), "image/png")
        return FileResponse(target, media_type=media_type, headers={"Cache-Control": "no-store"})

    @router.get("/api/workspace/logo/status")
    def logo_status() -> dict[str, object]:
        with workspace.STATE_LOCK:
            custom = _find_custom_logo(workspace.REPO_ROOT)
        version = int(custom.stat().st_mtime) if custom else 0
        return {"custom": custom is not None, "url": f"/api/workspace/logo?v={version}" if custom else "/static/logo-512.png"}

    @router.post("/api/workspace/logo")
    async def upload_logo(file: Annotated[UploadFile, File(...)]) -> dict[str, object]:
        raw = await file.read(MAX_LOGO_BYTES + 1)
        if not raw:
            raise HTTPException(status_code=400, detail="Logo file is empty")
        if len(raw) > MAX_LOGO_BYTES:
            raise HTTPException(status_code=413, detail="Logo image must be 2 MB or smaller")
        ext = _detect_image_ext(raw)
        if not ext:
            raise HTTPException(status_code=400, detail="Unsupported image format. Please upload a PNG, JPG, or WebP image.")
        with workspace.STATE_LOCK:
            workspace.REPO_ROOT.mkdir(parents=True, exist_ok=True)
            _clear_custom_logos(workspace.REPO_ROOT)
            target = workspace.REPO_ROOT / f"{LOGO_STEM}{ext}"
            tmp = workspace.REPO_ROOT / f"{LOGO_STEM}.tmp"
            if target.is_symlink() or tmp.is_symlink():
                raise HTTPException(status_code=400, detail="Custom logo path cannot be a symbolic link")
            tmp.write_bytes(raw)
            tmp.replace(target)
        return {"custom": True, "url": f"/api/workspace/logo?v={int(time.time() * 1000)}"}

    @router.delete("/api/workspace/logo")
    def reset_logo() -> dict[str, object]:
        with workspace.STATE_LOCK:
            _clear_custom_logos(workspace.REPO_ROOT)
        return {"custom": False, "url": "/static/logo-512.png"}

    return router
