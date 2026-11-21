"""Native OS folder-picker import route preserving nested subfolders in desktop & web builds."""

import re
from collections.abc import Callable
from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from pypdf.errors import PdfReadError

from core.contracts import AnonymizationReport, KnowledgeChunk, WorkspaceConfig
from core.linked_vaults import pick_native_folder
from features.ui import folders, import_stream_routes, upload_guard, workspace

MAX_NATIVE_IMPORT_FILES = 1000
_BAD_SEG_RE = re.compile(r"[^\w .-]+", re.UNICODE)


def _safe_folder_segments(rel_parts: tuple[str, ...]) -> str:
    cleaned: list[str] = []
    for part in rel_parts:
        seg = re.sub(r"\s+", " ", _BAD_SEG_RE.sub("_", part)).strip(" ._-")[:64]
        if seg and not seg.startswith("."):
            cleaned.append(seg)
    return "/".join(cleaned)


def _has_symlink_ancestor(path: Path, root: Path) -> bool:
    cur = path
    while cur != root:
        if cur.is_symlink():
            return True
        cur = cur.parent
    return False


def _import_folder_sync(
    resolved: Path,
    destination: Path,
    do_anon: bool,
    convert: Callable[[str, bytes, list[str] | None], str],
    inspect: Callable[[str, str], dict[str, object]],
    slug: Callable[[str, str], str],
) -> tuple[list[str], int, int]:
    imported: list[str] = []
    skipped = 0
    total_redacted = 0
    for item in sorted(resolved.rglob("*")):
        if len(imported) >= MAX_NATIVE_IMPORT_FILES:
            break
        if not item.is_file() or _has_symlink_ancestor(item, resolved):
            continue
        rel = item.relative_to(resolved)
        if any(part.startswith(".") or part == "__MACOSX" for part in rel.parts):
            skipped += 1
            continue
        try:
            if item.stat().st_size > upload_guard.MAX_UPLOAD_BYTES:
                skipped += 1
                continue
            stem, _ = workspace.validate_upload_filename(item.name)
            rel_sub = _safe_folder_segments((resolved.name, *rel.parts[:-1]))
            item_dest = folders.resolve_subfolder(destination, rel_sub, create=True) if rel_sub else destination
            raw = item.read_bytes()
            final_stem = slug(item.name, stem) if do_anon else stem
            text = convert(item.name, raw, workspace.auto_tags_for_filename(item.name))
            report = AnonymizationReport.model_validate(inspect(text, item.name)) if do_anon else None
            out_path = item_dest / f"{final_stem}.md"
            if out_path.is_symlink():
                skipped += 1
                continue
            out_path.write_text(report.scrubbed_text if report else text, encoding="utf-8")
            imported.append(f"{resolved.name}/{rel.as_posix()}")
            total_redacted += report.total_redacted if report else 0
        except (ValueError, OSError, BadZipFile, ParseError, PdfReadError, EOFError, KeyError):
            skipped += 1
    return imported, skipped, total_redacted


def build_router(
    config: Callable[[], WorkspaceConfig],
    reindex: Callable[[Path], list[KnowledgeChunk]],
    convert: Callable[[str, bytes, list[str] | None], str],
    inspect: Callable[[str, str], dict[str, object]],
    slug: Callable[[str, str], str],
) -> APIRouter:
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
        picked = (
            Path(raw_source).expanduser()
            if raw_source
            else await run_in_threadpool(pick_native_folder, "Choose a folder to import into your Library")
        )
        if picked is None:
            return {"cancelled": True}
        if picked.is_symlink() or not picked.is_dir():
            raise HTTPException(status_code=400, detail="Choose a valid folder (symbolic links are not allowed)")
        resolved = picked.resolve()
        if resolved == resolved.parent:
            raise HTTPException(status_code=400, detail="Cannot import the filesystem root")
        subfolder, save_area, anonymize = str(body.get("subfolder") or ""), body.get("area"), body.get("anonymize")

        def _apply() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                area = active.knowledge_dir if not isinstance(save_area, str) or not save_area else save_area
                if area not in active.active_dirs:
                    raise HTTPException(status_code=400, detail="Save to one of the selected areas")
                target = workspace.resolve_safe_knowledge_dir(area, create=True)
                try:
                    destination = folders.resolve_subfolder(target, subfolder, create=True)
                except (ValueError, TypeError, OSError) as exc:
                    raise HTTPException(status_code=400, detail="Invalid subfolder path") from exc
                if destination.resolve().is_relative_to(resolved):
                    raise HTTPException(status_code=400, detail="Cannot import a parent folder into itself")
                do_anon = active.anonymize_uploads if anonymize is None else bool(anonymize)
                imported, skipped, total_redacted = _import_folder_sync(resolved, destination, do_anon, convert, inspect, slug)
                if not imported:
                    raise HTTPException(status_code=400, detail="No supported documents found in this folder")
                return {
                    **workspace.build_workspace_payload(active, reindex(target)),
                    "cancelled": False,
                    "folder_name": resolved.name,
                    "imported_count": len(imported),
                    "skipped_count": skipped,
                    "redacted_count": total_redacted,
                }

        return await run_in_threadpool(_apply)

    router.include_router(
        import_stream_routes.build_router(config, reindex, convert, inspect, slug, _safe_folder_segments, MAX_NATIVE_IMPORT_FILES)
    )
    return router
