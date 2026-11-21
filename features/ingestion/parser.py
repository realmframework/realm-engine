"""Forgiving Markdown parser with optional YAML frontmatter and fenced-code awareness."""

import re
from pathlib import Path

from core.contracts import KnowledgeChunk

_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")


def _clean_scalar(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
        return stripped[1:-1].strip()
    return stripped


def parse_frontmatter(lines: list[str]) -> tuple[dict[str, object], list[str]]:
    """Parse optional leading ``---`` YAML frontmatter without swallowing horizontal rules."""
    if not lines or lines[0].strip() != "---":
        return {}, lines
    end_idx = next((i for i in range(1, len(lines)) if lines[i].strip() in {"---", "..."}), None)
    if end_idx is None:
        return {}, lines
    meta: dict[str, object] = {}
    list_key: str | None = None
    for raw in lines[1:end_idx]:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if list_key and stripped.startswith("- "):
            current = meta.get(list_key)
            if isinstance(current, list):
                current.append(_clean_scalar(stripped[2:]))
            continue
        list_key = None
        if ":" not in raw:
            return {}, lines
        key, value = raw.split(":", 1)
        key_clean, val_clean = key.strip().lower(), value.strip()
        if not key_clean or not re.fullmatch(r"[a-z0-9_-]{1,40}", key_clean):
            return {}, lines
        if val_clean.startswith("[") and val_clean.endswith("]"):
            meta[key_clean] = [_clean_scalar(item) for item in val_clean[1:-1].split(",") if _clean_scalar(item)]
        elif val_clean == "":
            meta[key_clean] = []
            list_key = key_clean
        else:
            meta[key_clean] = _clean_scalar(val_clean)
    if not meta:
        return {}, lines
    body = lines[end_idx + 1 :]
    while body and not body[0].strip():
        body = body[1:]
    return meta, body


def _extract_tags(meta: dict[str, object], body_lines: list[str]) -> tuple[list[str], int]:
    raw_meta = meta.get("tags")
    meta_tags: list[str] = []
    if isinstance(raw_meta, list):
        meta_tags = [str(tag).strip() for tag in raw_meta if str(tag).strip()]
    elif isinstance(raw_meta, str) and raw_meta.strip():
        meta_tags = [tag.strip() for tag in raw_meta.split(",") if tag.strip()]
    if body_lines and body_lines[0].startswith("Tags:"):
        inline = [tag.strip() for tag in body_lines[0][len("Tags:") :].split(",") if tag.strip()]
        return (inline or meta_tags or ["general"]), 1
    return (meta_tags or ["general"]), 0


def parse_markdown_text(text: str, stem: str, file_path: str) -> list[KnowledgeChunk]:
    """Split Markdown text into chunks keyed by ``## `` headings while preserving intro & fences."""
    lines = text.lstrip("\ufeff").splitlines()
    if not lines:
        return []
    meta, body_lines = parse_frontmatter(lines)
    if not body_lines:
        return []
    meta_title = str(meta.get("title") or "").strip()
    if body_lines[0].startswith("#") and not body_lines[0].startswith("##"):
        title = body_lines[0].lstrip("# ").strip() or meta_title or stem
        body_start = 1
    else:
        title = meta_title or Path(stem).name.replace("_", " ").replace("-", " ").title()
        body_start = 0

    tags, tag_offset = _extract_tags(meta, body_lines[body_start:])
    body_start += tag_offset
    description, url = str(meta.get("description") or "").strip(), str(meta.get("url") or "").strip()

    remaining_lines = body_lines[body_start:]
    sections: list[tuple[str, list[str]]] = []
    lead: list[str] = []
    heading: str | None = None
    body: list[str] = []
    fence_char = ""
    fence_len = 0

    for line in remaining_lines:
        if m := _FENCE_RE.match(line):
            marker = m.group(1)
            if not fence_char:
                fence_char, fence_len = marker[0], len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_len and not line.strip().lstrip(fence_char):
                fence_char, fence_len = "", 0
        if not fence_char and line.startswith("## "):
            if heading is None and "\n".join(lead).strip():
                sections.append(("Overview", lead))
                lead = []
            elif heading is not None and body:
                sections.append((heading, body))
            heading, body = line[3:].strip(), []
        elif heading is not None:
            body.append(line)
        else:
            lead.append(line)
    if heading is not None and body:
        sections.append((heading, body))
    if not sections and "\n".join(remaining_lines).strip():
        sections.append(("Overview", remaining_lines))

    chunks: list[KnowledgeChunk] = []
    for section_heading, section_lines in sections:
        content = "\n".join(section_lines).strip()
        if not content:
            continue
        chunks.append(
            KnowledgeChunk(
                id=f"{stem}-{len(chunks)}",
                title=f"{title} — {section_heading}",
                file_path=file_path,
                doc_id=stem,
                subfolder=Path(stem).parent.as_posix() if "/" in stem else "",
                content=content,
                tags=tags,
                embedding=None,
                url=url,
                description=description,
            )
        )
    return chunks


def parse_markdown_file(file_path: Path, knowledge_dir: Path | None = None) -> list[KnowledgeChunk]:
    """Split a Markdown file on disk into knowledge chunks."""
    stem = file_path.relative_to(knowledge_dir).with_suffix("").as_posix() if knowledge_dir else file_path.stem
    return parse_markdown_text(file_path.read_text(encoding="utf-8", errors="replace"), stem, str(file_path))
