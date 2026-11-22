"""Workspace configuration, system diagnostics, upload helpers, and dynamic metadata."""

import base64
import re
from pathlib import Path
from threading import RLock

import httpx
from fastapi import HTTPException, Request

from core import contracts
from core.db import atomic_write_text, backup_corrupt_file
from core.runtime import data_root, is_loopback_url, ollama_base_url
from features.ui import selection
from features.ui.areas import area_path, list_areas
from features.ui.folders import list_subfolders, resolve_document
from features.ui.starter_prompts import build_starter_prompts

REPO_ROOT = data_root()
WORKSPACE_FILE = REPO_ROOT / "workspace.json"
STATE_LOCK = RLock()
ALLOWED_UPLOAD_EXTENSIONS = {".md", ".txt", ".html", ".pdf", ".docx", ".csv", ".tsv", ".xlsx", ".pptx"}
OLLAMA_TAGS_URL = f"{ollama_base_url()}/api/tags"
_ORIG_HTTPX_GET = httpx.get


def load_workspace_config(path: Path | None = None) -> contracts.WorkspaceConfig:
    target = path or WORKSPACE_FILE
    if target.is_file() and not target.is_symlink():
        try:
            return contracts.WorkspaceConfig.model_validate_json(target.read_text(encoding="utf-8"))
        except ValueError:
            backup_corrupt_file(target)
        except OSError:
            return contracts.WorkspaceConfig()
    return contracts.WorkspaceConfig()
def save_workspace_config(config: contracts.WorkspaceConfig, path: Path | None = None) -> None:
    atomic_write_text(path or WORKSPACE_FILE, config.model_dump_json(indent=2))
def build_tutor_config(provider: str | None, model: str | None, api_key: str | None, temperature: float = 0.2) -> contracts.TutorConfig:
    clamped = max(0.0, min(1.0, float(temperature)))
    try:
        return contracts.TutorConfig.model_validate({"provider": provider or "ollama", "model": (model or "").strip(), "api_key": api_key or None, "temperature": clamped})
    except ValueError:
        return contracts.TutorConfig(temperature=clamped)
def build_search_query(q: str, tag: str | None, top_k: int = 5, retrieval_mode: str = "hybrid", rrf_k: int = 60) -> contracts.SearchQuery:
    mode: contracts.RetrievalMode = retrieval_mode if retrieval_mode in ("hybrid", "lexical", "vector") else "hybrid"
    return contracts.SearchQuery(query=q, tag_filter=tag, top_k=max(1, min(15, int(top_k))), retrieval_mode=mode, rrf_k=max(1, min(120, int(rrf_k))))
def resolve_safe_knowledge_dir(knowledge_dir: str, repo_root: Path | None = None, create: bool = False) -> Path:
    return area_path(knowledge_dir, repo_root or REPO_ROOT, create)
def resolve_guide_file(target_dir: Path, doc_id: str) -> Path:
    try:
        return resolve_document(target_dir, doc_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Guide not found") from exc

def _get_ollama_tags() -> httpx.Response:
    url = OLLAMA_TAGS_URL if httpx.get is not _ORIG_HTTPX_GET else f"{ollama_base_url()}/api/tags"
    if httpx.get is not _ORIG_HTTPX_GET:
        return httpx.get(url, timeout=1.0)
    with httpx.Client(trust_env=not is_loopback_url(url), follow_redirects=False, timeout=1.0) as client:
        return client.get(url)

def probe_system_status(chunks: list[contracts.KnowledgeChunk], workspace_file: Path | None = None) -> dict[str, object]:
    target_ws, ollama_online, ollama_models = workspace_file or WORKSPACE_FILE, False, []
    try:
        res = _get_ollama_tags()
        if res.status_code == 200 and isinstance((raw := res.json()), dict):
            ollama_online, ollama_models = True, [str(m.get("name", "")) for m in (raw.get("models") or []) if isinstance(m, dict) and m.get("name")]
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        ollama_online = False
    has_nomic = any(m.startswith("nomic-embed-text") for m in ollama_models)
    embedded = sum(1 for c in chunks if c.embedding)
    hybrid_ready = has_nomic and (not chunks or embedded > 0)
    return {"ollama_online": ollama_online, "ollama_models": ollama_models, "has_nomic_embed": has_nomic, "embedded_chunks": embedded, "retrieval_tier": "hybrid_local" if hybrid_ready else "lexical_zero_gpu", "is_first_run": not target_ws.is_file(), "doc_count": len(group_chunks_into_guides(chunks))}

def validate_upload_filename(filename: str) -> tuple[str, str]:
    base = Path(filename.strip()).name
    ext = Path(base).suffix.lower()
    if not base or base.startswith(".") or ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValueError(f"Unsupported or invalid filename: {filename}")
    safe_stem = re.sub(r"[^a-zA-Z0-9_-]+", "_", Path(base).stem).strip("_").lower()
    if not safe_stem:
        raise ValueError(f"Invalid filename stem: {filename}")
    return safe_stem, ext

def auto_tags_for_filename(filename: str, raw_tags: str | None = None) -> list[str]:
    if raw_tags and raw_tags.strip() and (explicit := [t.strip().lower() for t in raw_tags.split(",") if t.strip()]):
        return explicit
    validate_upload_filename(filename)
    return []

def decode_json_upload(payload: dict[str, object]) -> tuple[list[tuple[str, bytes]], str | None]:
    raw_tags = str(payload["tags"]) if "tags" in payload and payload["tags"] is not None else None
    items = payload.get("files")
    entries = items if isinstance(items, list) else [payload]
    files: list[tuple[str, bytes]] = []
    for entry in entries:
        if isinstance(entry, dict):
            fname, b64 = str(entry.get("filename") or ""), entry.get("content_base64")
            raw_bytes = base64.b64decode(str(b64)) if isinstance(b64, str) else str(entry.get("content") or "").encode("utf-8")
            files.append((fname, raw_bytes))
    return files, raw_tags

def group_chunks_into_guides(chunks: list[contracts.KnowledgeChunk], tag: str | None = None) -> list[dict[str, object]]:
    guides_by_id: dict[str, dict[str, object]] = {}
    for chunk in chunks:
        if tag and tag not in chunk.tags:
            continue
        doc_id = chunk.doc_id or Path(chunk.file_path).stem or chunk.id.rsplit("-", 1)[0]
        parts = chunk.title.split(" — ", 1)
        doc_title, section_title = parts[0].strip(), (parts[1].strip() if len(parts) > 1 else chunk.title)
        if doc_id not in guides_by_id:
            guides_by_id[doc_id] = {"doc_id": doc_id, "file_path": chunk.file_path, "area": chunk.area, "subfolder": chunk.subfolder, "title": doc_title, "tags": list(chunk.tags), "sections": []}
        sections = guides_by_id[doc_id]["sections"]
        if isinstance(sections, list):
            sections.append({"section_title": section_title, "content": chunk.content})
    return list(guides_by_id.values())

def build_workspace_payload(config: contracts.WorkspaceConfig, chunks: list[contracts.KnowledgeChunk]) -> dict[str, object]:
    guides = group_chunks_into_guides(chunks)
    tag_counts: dict[str, int] = {}
    for guide in guides:
        raw_tags = guide.get("tags")
        if isinstance(raw_tags, list):
            for tag in dict.fromkeys(str(item) for item in raw_tags):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
    sorted_tags = [{"name": n, "count": c} for n, c in sorted(tag_counts.items(), key=lambda pair: (-pair[1], pair[0]))]
    prompts = build_starter_prompts(chunks, [str(tag["name"]) for tag in sorted_tags])
    areas = [a.model_dump() for a in list_areas(REPO_ROOT, config.knowledge_dir)]
    for area in areas:
        if len(config.active_dirs) == 1 and area["name"] == config.knowledge_dir:
            area["doc_count"] = len(guides)
    avail = list(dict.fromkeys([*[str(a["name"]) for a in areas], *([config.knowledge_dir] if config.knowledge_dir else [])]))
    try:
        subs = [] if not config.active_dirs else (selection.subfolders(config, REPO_ROOT) if len(config.active_dirs) > 1 else selection.filter_subfolders(list_subfolders(resolve_safe_knowledge_dir(config.knowledge_dir)), config.knowledge_dir, config))
    except (HTTPException, ValueError):
        subs = []
    return {"config": config.model_dump(), "areas": areas, "subfolders": subs, "unloaded_subfolders": selection.unloaded_subfolders(config), "available_dirs": avail, "tags": sorted_tags, "starter_prompts": prompts, "doc_count": len(guides), "embeddings_active": any(bool(c.embedding) for c in chunks)}


def require_area(request: Request, config: contracts.WorkspaceConfig) -> None:
    expected = request.headers.get("x-knowledge-area")
    if expected is not None and expected != config.knowledge_dir:
        raise HTTPException(status_code=409, detail="Knowledge area changed. Select the area again before continuing.")
    expected_selection = request.headers.get("x-knowledge-selection")
    if expected_selection is not None and expected_selection != ",".join(config.active_dirs):
        raise HTTPException(status_code=409, detail="Selected areas changed. Select the areas again before continuing.")
def resolve_selected_guide(config: contracts.WorkspaceConfig, doc_id: str) -> tuple[Path, str]:
    return selection.document_source(config, REPO_ROOT, doc_id) if len(config.active_dirs) > 1 else (resolve_safe_knowledge_dir(config.knowledge_dir), doc_id)
