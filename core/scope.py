"""Document scoping, guide classification, and canonical public URL resolution."""

import re
import unicodedata

from core.contracts import KnowledgeChunk

NAVIGATION_TAG = "navigation"


def is_navigation(chunk: KnowledgeChunk) -> bool:
    return any(tag.casefold() == NAVIGATION_TAG for tag in chunk.tags)


def matches_scope(chunk: KnowledgeChunk, doc_id: str | None, subfolder: str | None) -> bool:
    if doc_id is not None and chunk.doc_id != doc_id:
        return False
    return subfolder is None or chunk.subfolder == subfolder or bool(subfolder and chunk.subfolder.startswith(subfolder + "/"))


def section_slug(heading: str) -> str:
    """Convert a Markdown heading to a lowercase URL anchor slug."""
    normalized = unicodedata.normalize("NFKD", heading).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-z0-9\s-]", "", normalized.lower())
    return re.sub(r"[-\s]+", "-", cleaned).strip("-")


def chunk_section_heading(title: str) -> str:
    parts = title.split(" — ", 1)
    return parts[1].strip() if len(parts) > 1 else ""


def resolve_chunk_url(chunk: KnowledgeChunk, url_template: str = "") -> str:
    """Resolve a canonical web URL + section anchor for a chunk."""
    section = chunk_section_heading(chunk.title)
    anchor = section_slug(section) if section and section.lower() not in {"overview", "body", "content"} else ""
    if chunk.url:
        base = chunk.url.strip()
        return f"{base}#{anchor}" if anchor and "#" not in base else base
    if not url_template:
        return ""
    local_doc = chunk.doc_id.split("::", 1)[-1] if "::" in chunk.doc_id else chunk.doc_id
    area = chunk.area or "knowledge_base"
    base = url_template.format(area=area, doc_id=local_doc, subfolder=chunk.subfolder, section_slug=anchor)
    base = re.sub(r"/{2,}", "/", base) if base.startswith("/") else base
    if "{section_slug}" in url_template:
        return base.rstrip("#")
    return f"{base}#{anchor}" if anchor else base
