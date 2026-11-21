"""Native OS folder-picker import route preserving nested subfolders in desktop & web builds."""

import os
import re
from collections.abc import Callable
from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from pypdf.errors import PdfReadError

from core.contracts import AnonymizationReport, KnowledgeChunk, WorkspaceConfig
from core.db import atomic_write_text
from core.linked_vaults import (
    is_linked_vault,
    pick_native_folder,
    validate_external_folder,
)
from features.ui import (
    folders,
    guide_edit_routes,
    import_stream_routes,
    upload_guard,
    workspace,
)

MAX_NATIVE_IMPORT_FILES = 1000
_BAD_SEG_RE = re.compile(r"[^\w .-]+", re.UNICODE)


def _safe_folder_segments(rel_parts: tuple[str, ...]) -> str:
    cleaned = [seg for part in rel_parts if (seg := re.sub(r"\s+", " ", _BAD_SEG_RE.sub("_", part)).strip(" ._-")[:64]) and not seg.startswith(".")]
    return "/".join(cleaned)


_SKIP_IMPORT_DIRS = frozenset({"__MACOSX", "node_modules", ".git", ".venv", "__pycache__"})


def walk_import_files(resolved: Path, limit: int) -> tuple[list[Path], int]:
    """Yield up to ``limit`` real non-hidden files via pruned os.walk plus skipped hidden/dir count."""
    found, pruned = [], 0
    for cur_root, dirnames, filenames in os.walk(resolved, followlinks=False):
        root_p = Path(cur_root)
        kept_dirs = []
        for d in sorted(dirnames):
            if d.startswith(".") or d in _SKIP_IMPORT_DIRS or (root_p / d).is_symlink():
                pruned += 1
            else:
                kept_dirs.append(d)
        dirnames[:] = kept_dirs
        for fname in sorted(filenames):
            if fname.startswith("."):
                pruned += 1
                continue
            item = root_p / fname
            if item.is_symlink() or not item.is_file():
                continue
            found.append(item)
            if len(found) >= limit:
                return found, pruned
    return found, pruned


def _import_folder_sync(resolved: Path, destination: Path, do_anon: bool, convert: Callable[[str, bytes, list[str] | None], str], inspect: Callable[[str, str], dict[str, object]], slug: Callable[[str, str], str]) -> tuple[list[str], int, int]:
    candidates, skipped = walk_import_files(resolved, MAX_NATIVE_IMPORT_FILES * 2)
    imported, total_redacted = [], 0
    for item in candidates:
        if len(imported) >= MAX_NATIVE_IMPORT_FILES:
            break
        rel = item.relative_to(resolved)
        try:
            if item.stat().st_size > upload_guard.MAX_UPLOAD_BYTES:
                skipped += 1
                continue
            stem, _ = workspace.validate_upload_filename(item.name)
            rel_sub = _safe_folder_segments((resolved.name, *rel.parts[:-1]))
            item_dest = folders.resolve_subfolder(destination, rel_sub, create=True) if rel_sub else destination
            raw, final_stem = item.read_bytes(), (slug(item.name, stem) if do_anon else stem)
            text = convert(item.name, raw, workspace.auto_tags_for_filename(item.name))
            report = AnonymizationReport.model_validate(inspect(text, item.name)) if do_anon else None
            out_path = guide_edit_routes._unique_md_path(item_dest, final_stem) if (do_anon and final_stem != stem) else (item_dest / f"{final_stem}.md")
            atomic_write_text(out_path, report.scrubbed_text if report else text)
            imported.append(f"{resolved.name}/{rel.as_posix()}")
            total_redacted += report.total_redacted if report else 0
        except (ValueError, OSError, BadZipFile, ParseError, PdfReadError, EOFError, KeyError):
            skipped += 1
    return imported, skipped, total_redacted


def build_router(config: Callable[[], WorkspaceConfig], reindex: Callable[[Path], list[KnowledgeChunk]], convert: Callable[[str, bytes, list[str] | None], str], inspect: Callable[[str, str], dict[str, object]], slug: Callable[[str, str], str]) -> APIRouter:
    router = APIRouter()

    @router.post("/api/workspace/import-native-folder")
    async def import_native_folder(request: Request) -> dict[str, object]:
        body: dict[str, object] = {}
        if "application/json" in request.headers.get("content-type", ""):
            try:
                raw_body = await request.json()
                if isinstance(raw_body, dict):
                    body = raw_body
            except ValueError:
                body = {}
        raw_source = str(body.get("source_path") or "").strip()
        picked = Path(raw_source).expanduser() if raw_source else await run_in_threadpool(pick_native_folder, "Choose a folder to import into your Library")
        if picked is None:
            return {"cancelled": True}
        try:
            resolved = validate_external_folder(picked, workspace.REPO_ROOT, action="import", allow_under_root=True)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        subfolder, save_area, anonymize = str(body.get("subfolder") or ""), body.get("area"), body.get("anonymize")

        def _apply() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                area = active.knowledge_dir if not isinstance(save_area, str) or not save_area else save_area
                if area not in active.active_dirs:
                    raise HTTPException(status_code=400, detail="Save to one of the selected areas")
                if is_linked_vault(area, workspace.REPO_ROOT):
                    raise HTTPException(status_code=403, detail="Linked folders are read-safe — import into a managed workspace instead.")
                target = workspace.resolve_safe_knowledge_dir(area, create=True)
                try:
                    destination = folders.resolve_subfolder(target, subfolder, create=True)
                except (ValueError, TypeError, OSError) as exc:
                    raise HTTPException(status_code=400, detail="Invalid subfolder path") from exc
                dest_res = destination.resolve()
                if dest_res.is_relative_to(resolved) or resolved.is_relative_to(dest_res):
                    raise HTTPException(status_code=400, detail="Cannot import a folder into itself or a nested subfolder")
                do_anon = active.anonymize_uploads if anonymize is None else bool(anonymize)
            imported, skipped, total_redacted = _import_folder_sync(resolved, destination, do_anon, convert, inspect, slug)
            if not imported:
                raise HTTPException(status_code=400, detail="No supported documents found in this folder")
            with workspace.STATE_LOCK:
                latest_active = config()
                if area not in latest_active.active_dirs:
                    raise HTTPException(status_code=409, detail="Workspace changed during import.")
                return {**workspace.build_workspace_payload(latest_active, reindex(target)), "cancelled": False, "folder_name": resolved.name, "imported_count": len(imported), "skipped_count": skipped, "redacted_count": total_redacted}

        return await run_in_threadpool(_apply)

    router.include_router(import_stream_routes.build_router(config, reindex, convert, inspect, slug, _safe_folder_segments, MAX_NATIVE_IMPORT_FILES))
    return router
