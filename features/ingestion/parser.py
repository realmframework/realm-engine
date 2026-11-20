"""Forgiving Markdown parser with optional YAML frontmatter support."""

from pathlib import Path

from core.contracts import KnowledgeChunk


def _clean_scalar(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
        return stripped[1:-1].strip()
    return stripped


def parse_frontmatter(lines: list[str]) -> tuple[dict[str, object], list[str]]:
    """Parse optional leading ``---`` YAML frontmatter without external dependencies."""
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
            continue
        key, value = raw.split(":", 1)
        key_clean, val_clean = key.strip().lower(), value.strip()
        if not key_clean:
            continue
        if val_clean.startswith("[") and val_clean.endswith("]"):
            items = [_clean_scalar(item) for item in val_clean[1:-1].split(",") if _clean_scalar(item)]
            meta[key_clean] = items
        elif val_clean == "":
            meta[key_clean] = []
            list_key = key_clean
        else:
            meta[key_clean] = _clean_scalar(val_clean)
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
    """Split Markdown text into knowledge chunks keyed by ``## `` headings or an Overview fallback."""
    lines = text.splitlines()
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
    description = str(meta.get("description") or "").strip()
    url = str(meta.get("url") or "").strip()

    remaining_lines = body_lines[body_start:]
    sections: list[tuple[str, list[str]]] = []
    heading: str | None = None
    body: list[str] = []

    for line in remaining_lines:
        if line.startswith("## "):
            if heading is not None and body:
                sections.append((heading, body))
            heading = line[3:].strip()
            body = []
        elif heading is not None:
            body.append(line)
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
    return parse_markdown_text(file_path.read_text(encoding="utf-8"), stem, str(file_path))
