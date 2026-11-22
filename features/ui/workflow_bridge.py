"""Workspace-scoped callbacks bridging Workflow Engine nodes to Library, Slides, Board & Impact."""

import re
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from core.contracts import KnowledgeChunk, SearchQuery, WorkspaceConfig
from core.db import atomic_write_bytes, atomic_write_text
from core.linked_vaults import is_linked_vault
from features.ui import folders, workspace
from features.ui.privacy import require_local


def _slug(raw: str, fallback: str) -> str:
    clean = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")[:52]
    return clean or fallback


def build_workflow_callbacks(
    cfg: WorkspaceConfig,
    get_index: Callable[[], list[KnowledgeChunk]],
    reindex: Callable[[Path], list[KnowledgeChunk]],
    hybrid_search: Callable[..., Sequence[object]],
    stream_messages: object,
    cloud_guard: Callable[..., object],
    export_deck_bytes: Callable[..., tuple[bytes, str, str, object]],
    add_tasks_from_text: Callable[[str, str, str, Path | None], int],
    log_workflow_impact: Callable[[str, Path | None, str, str, str], str],
) -> dict[str, object]:
    area = cfg.knowledge_dir

    def _vault_search(query: str, top_k: int) -> str:
        chunks = get_index()
        if not chunks:
            return f"No indexed documents yet for query: {query}"
        hits = hybrid_search(SearchQuery(query=query, top_k=top_k, retrieval_mode="lexical"), chunks)
        parts: list[str] = []
        for h in hits:
            chunk = getattr(h, "chunk", h)
            title = str(getattr(chunk, "title", "") or getattr(chunk, "doc_id", "Document"))
            snippet = str(getattr(chunk, "content", "") or getattr(h, "snippet", ""))[:500]
            if snippet:
                parts.append(f"### {title}\n{snippet}")
        return "\n\n".join(parts) or f"No matching passages for: {query}"

    def _save_guide(title: str, markdown: str, subfolder: str) -> str:
        if not area or is_linked_vault(area, workspace.REPO_ROOT):
            return f"{_slug(title, 'workflow-note')}.md (skipped: read-safe vault)"
        target_root = workspace.resolve_safe_knowledge_dir(area)
        sub = _slug(subfolder, "workflows") if subfolder else "workflows"
        rel = f"{sub}/{_slug(title, 'note')}-{datetime.now(UTC):%Y%m%d-%H%M}.md"
        dest = folders.contained_path(target_root, rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        body = markdown if markdown.lstrip().startswith("#") else f"# {title}\n\n{markdown}\n"
        atomic_write_text(dest, body)
        reindex(target_root)
        return rel

    def _generate_slides(title: str, markdown: str, fmt: str) -> str:
        out_fmt: Literal["pptx", "pdf"] = "pdf" if fmt == "pdf" else "pptx"
        raw, _mime, ext, _deck = export_deck_bytes(title, markdown, accent_hex=cfg.theme_accent, glow_hex=cfg.theme_glow, fmt=out_fmt)
        base = workspace.resolve_safe_knowledge_dir(area) if area and not is_linked_vault(area, workspace.REPO_ROOT) else (workspace.REPO_ROOT / "exports")
        out_dir = base / "exports"
        out_dir.mkdir(parents=True, exist_ok=True)
        fname = f"{_slug(title, 'slides')}-{datetime.now(UTC):%Y%m%d-%H%M}{ext}"
        atomic_write_bytes(out_dir / fname, raw)
        return f"exports/{fname}"

    def _guard(provider: str, model: str, text: str) -> None:
        require_local(cfg, provider)  # type: ignore[arg-type]
        if provider != "ollama":
            cloud_guard(provider, model, text, 600, "workflow_agent")

    return {
        "vault_search": _vault_search,
        "stream_messages": stream_messages,
        "cloud_guard": _guard,
        "extract_tasks": lambda txt, pid: add_tasks_from_text(area, txt, pid, workspace.REPO_ROOT),
        "generate_slides": _generate_slides,
        "save_guide": _save_guide,
        "log_impact": lambda what, eff, tag: log_workflow_impact(area, workspace.REPO_ROOT, what, eff, tag),
    }
