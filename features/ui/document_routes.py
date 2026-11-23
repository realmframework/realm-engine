"""Active-area upload and guide mutation routes."""

import re
from collections.abc import Callable
from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from pypdf.errors import PdfReadError

from core import contracts
from core.db import atomic_write_text
from core.file_types import (
    CODE_EXTENSIONS,
    EDITABLE_TEXT_EXTENSIONS,
    is_ignored_relpath,
)
from core.linked_vaults import is_linked_vault
from features.ui import (
    file_ops_routes,
    folder_routes,
    folders,
    guide_edit_routes,
    native_import_routes,
    preview_routes,
    route_helpers,
    selection,
    upload_guard,
    workspace,
)

_BAD_SEG_RE = re.compile(r"[^\w .-]+", re.UNICODE)


def _safe_rel_folder(rel_path: str) -> str:
    parts = [p for p in rel_path.replace("\\", "/").split("/")[:-1] if p and p not in {".", ".."}]
    return "/".join(seg for seg in (re.sub(r"\s+", " ", _BAD_SEG_RE.sub("_", p)).strip(" ._-")[:64] for p in parts) if seg and not seg.startswith("."))


def build_router(
    config: Callable[[], contracts.WorkspaceConfig],
    reindex: Callable[[Path], list[contracts.KnowledgeChunk]],
    convert: Callable[[str, bytes, list[str] | None], str],
    inspect: Callable[[str, str], dict[str, object]],
    slug: Callable[[str, str], str],
) -> APIRouter:
    router = APIRouter()

    @router.post("/api/upload")
    async def upload(request: Request) -> dict[str, object]:
        files, tags, anonymize, subfolder, save_area, rel_paths, skip_unsupported = await upload_guard.read_upload(request, workspace.decode_json_upload)
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        def _apply() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                area = active.knowledge_dir if save_area is None else save_area
                if not isinstance(area, str) or area not in active.active_dirs:
                    raise HTTPException(status_code=400, detail="Save to one of the selected areas")
                if is_linked_vault(area, workspace.REPO_ROOT):
                    raise HTTPException(status_code=403, detail="Linked folders are read-safe — upload files into a managed workspace instead.")
                target = workspace.resolve_safe_knowledge_dir(area, create=True)
                try:
                    destination = folders.resolve_subfolder(target, subfolder, create=True)
                except (ValueError, TypeError, OSError) as exc:
                    raise HTTPException(status_code=400, detail="Invalid subfolder path") from exc
                total, skipped, titles, uploaded = 0, 0, [], []
                for idx, (filename, raw) in enumerate(files):
                    rel = rel_paths[idx] if idx < len(rel_paths) else ""
                    base_name = Path(filename.replace("\\", "/")).name if skip_unsupported else filename
                    if skip_unsupported and (not base_name or base_name.startswith(".") or "__MACOSX" in rel.split("/") or (rel and is_ignored_relpath(Path(rel.replace("\\", "/"))))):
                        skipped += 1
                        continue
                    try:
                        stem, ext = workspace.validate_upload_filename(base_name)
                        item_dest = folders.resolve_subfolder(destination, rel_sub, create=True) if (rel_sub := _safe_rel_folder(rel) if rel else "") else destination
                        do_anon = active.anonymize_uploads if anonymize is None else bool(anonymize)
                        is_code = ext in CODE_EXTENSIONS
                        anon_stem = slug(base_name, stem) if do_anon else stem
                        text = raw.decode("utf-8", errors="replace") if is_code else convert(base_name, raw, workspace.auto_tags_for_filename(base_name, tags))
                        report = contracts.AnonymizationReport.model_validate(inspect(text, base_name)) if do_anon else None
                        final_text = report.scrubbed_text if report else text
                        out_path = (item_dest / f"{anon_stem}{ext}") if is_code else (guide_edit_routes._unique_md_path(item_dest, anon_stem) if (do_anon and anon_stem != stem) else (item_dest / f"{anon_stem}.md"))
                        atomic_write_text(out_path, final_text)
                        uploaded.append(rel or base_name)
                        titles.append(out_path.name if is_code else (final_text.splitlines()[0].lstrip("# ") if final_text.splitlines() else stem))
                        total += report.total_redacted if report else 0
                    except (ValueError, BadZipFile, ParseError, PdfReadError, EOFError, KeyError) as exc:
                        if not skip_unsupported:
                            raise HTTPException(status_code=400, detail="Unable to index this document") from exc
                        skipped += 1
                if not uploaded:
                    raise HTTPException(status_code=400, detail="No supported documents found in this folder")
                return {**workspace.build_workspace_payload(active, reindex(target)), "uploaded_files": uploaded, "uploaded_titles": titles, "redacted_count": total, "skipped_files": skipped}

        return await run_in_threadpool(_apply)

    @router.post("/api/guides/{doc_id:path}/anonymize")
    def anonymize_guide(doc_id: str, request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            area_slug = route_helpers.guide_area_slug(active, doc_id)
            if is_linked_vault(area_slug, workspace.REPO_ROOT):
                raise HTTPException(status_code=403, detail="Linked folders are read-safe — anonymization cannot modify external files on disk.")
            target, local_id = workspace.resolve_selected_guide(active, doc_id)
            selection.assert_guide_not_excluded(active, area_slug, local_id)
            path = workspace.resolve_guide_file(target, local_id)
            if path.suffix.lower() not in EDITABLE_TEXT_EXTENSIONS:
                raise HTTPException(status_code=400, detail="Only text, Markdown, and source-code files can be anonymized in place.")
            report = contracts.AnonymizationReport.model_validate(inspect(path.read_text(encoding="utf-8", errors="replace"), path.name))
            atomic_write_text(path, report.scrubbed_text)
            reindex(target)
            return {"doc_id": doc_id, "redacted_count": report.total_redacted}

    @router.delete("/api/guides/{doc_id:path}")
    def delete_guide(doc_id: str, request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            area_slug = route_helpers.guide_area_slug(active, doc_id)
            if is_linked_vault(area_slug, workspace.REPO_ROOT):
                raise HTTPException(status_code=403, detail="Linked folders are read-safe — unlink the folder instead of deleting files on disk.")
            target, local_id = workspace.resolve_selected_guide(active, doc_id)
            selection.assert_guide_not_excluded(active, area_slug, local_id)
            workspace.resolve_guide_file(target, local_id).unlink()
            reindex(target)
            return {"doc_id": doc_id, "deleted": True}

    for sub in (
        preview_routes.build_router(config, convert, inspect),
        folder_routes.build_router(config, reindex),
        file_ops_routes.build_router(config, reindex),
        guide_edit_routes.build_router(config, reindex),
        native_import_routes.build_router(config, reindex, convert, inspect, slug),
    ):
        router.include_router(sub)
    return router
