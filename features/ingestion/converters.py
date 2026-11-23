"""Universal document converters (.pdf, .docx, .txt, .html, .md) for the ingestion slice."""

import html
import io
import re
import xml.etree.ElementTree as ET
import zipfile
from contextlib import suppress
from html.parser import HTMLParser
from pathlib import Path

from pypdf import PdfReader

from core.contracts import KnowledgeChunk
from core.db import atomic_write_text
from core.file_types import CODE_LANG_BY_EXT, SUPPORTED_EXTENSIONS
from features.ingestion import topics as _topics
from features.ingestion.code_extractor import extract_code
from features.ingestion.office_extractors import extract_csv, extract_pptx, extract_xlsx
from features.ingestion.parser import parse_markdown_text
from features.ingestion.topics import infer_document_tags, repair_directory_topics

__all__ = ["SUPPORTED_EXTENSIONS", "convert_bytes_to_markdown", "convert_file_to_chunks", "infer_document_tags", "repair_directory_topics"]

SECTION_CHAR_TARGET, MAX_DOCX_XML_BYTES = 1200, 20 * 1024 * 1024


def _title_from_stem(filename: str) -> str:
    return Path(filename).stem.replace("_", " ").replace("-", " ").strip().title() or "Untitled Document"


def _chunk_paragraphs(paragraphs: list[str], target_chars: int = SECTION_CHAR_TARGET) -> list[tuple[str, str]]:
    cleaned = [p.strip() for p in paragraphs if p.strip()]
    if not cleaned:
        return [("Overview", "No extractable text content.")]
    sections, bucket, bucket_len = [], [], 0
    for para in cleaned:
        if bucket and bucket_len + len(para) > target_chars:
            sec_name = "Overview" if not sections and len(cleaned) == len(bucket) else f"Section {len(sections) + 1}"
            sections.append((sec_name, "\n\n".join(bucket)))
            bucket, bucket_len = [], 0
        bucket.append(para)
        bucket_len += len(para)
    if bucket:
        sections.append(("Overview" if not sections else f"Section {len(sections) + 1}", "\n\n".join(bucket)))
    return sections


def _extract_html(raw_text: str, fallback_title: str) -> tuple[str, list[tuple[str, str]]]:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", raw_text, flags=re.IGNORECASE | re.DOTALL)
    title = html.unescape(title_match.group(1)).strip() if title_match else fallback_title
    cleaned_html = re.sub(r"<(script|style)[^>]*>[\s\S]*?</\1>", " ", raw_text, flags=re.IGNORECASE)
    blocks: list[str] = []

    class _Extractor(HTMLParser):
        def handle_data(self, data: str) -> None:
            if data.strip():
                blocks.append(data.strip())

    _Extractor().feed(cleaned_html)
    return (title or fallback_title), _chunk_paragraphs(blocks)


def _extract_docx(raw_bytes: bytes, fallback_title: str) -> tuple[str, list[tuple[str, str]]]:
    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as archive, archive.open("word/document.xml") as handle:
        xml_bytes = handle.read(MAX_DOCX_XML_BYTES + 1)
    if len(xml_bytes) > MAX_DOCX_XML_BYTES:
        raise ValueError("DOCX XML exceeds the 20 MiB decompression limit")
    root = ET.fromstring(xml_bytes)
    title, sections, current_heading, current_paras = fallback_title, [], None, []
    for elem in root.iter():
        if not elem.tag.endswith("}p") and elem.tag != "p":
            continue
        styles = [v.lower() for c in elem.iter() if c.tag.endswith("}pStyle") or c.tag == "pStyle" for k, v in c.attrib.items() if k.endswith("val")]
        style_val = styles[0] if styles else ""
        line = "".join(n.text for n in elem.iter() if (n.tag.endswith("}t") or n.tag == "t") and n.text).strip()
        if not line:
            continue
        if "title" in style_val and title == fallback_title:
            title = line
        elif "heading" in style_val:
            if current_paras:
                sections.append((current_heading or "Overview", "\n\n".join(current_paras)))
                current_paras = []
            current_heading = line
        else:
            current_paras.append(line)
    if current_heading and current_paras:
        sections.append((current_heading, "\n\n".join(current_paras)))
    elif not sections:
        sections = _chunk_paragraphs(current_paras)
    return title, sections


def _extract_pdf(raw_bytes: bytes, fallback_title: str) -> tuple[str, list[tuple[str, str]]]:
    reader = PdfReader(io.BytesIO(raw_bytes))
    sections = [(f"Page {idx + 1}", text) for idx, page in enumerate(reader.pages) if (text := (page.extract_text() or "").strip())]
    return fallback_title, sections or [("Page 1", "No extractable text content.")]


def convert_bytes_to_markdown(filename: str, raw_bytes: bytes, tags: list[str] | None = None) -> str:
    """Convert raw document or source-code bytes into structured Markdown for RAG indexing."""
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {ext}")
    fallback_title = _title_from_stem(filename)
    if ext == ".md":
        text = raw_bytes.decode("utf-8", errors="replace").lstrip("\ufeff").strip()
        if text.startswith(("#", "---\n", "---\r\n")):
            return _topics.normalize_document_tags(text, filename, tags)
        return _topics.normalize_document_tags(f"# {fallback_title}\n\n## Overview\n{text}", filename, tags)
    if (code_lang := CODE_LANG_BY_EXT.get(ext)):
        title, sections = extract_code(raw_bytes.decode("utf-8", errors="replace"), Path(filename).name, code_lang)
        tags = list(dict.fromkeys([*(tags or []), code_lang, "code"]))
    elif ext == ".txt":
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", raw_bytes.decode("utf-8", errors="replace")) if p.strip()]
        title, sections = fallback_title, _chunk_paragraphs(paragraphs)
    elif ext == ".html":
        title, sections = _extract_html(raw_bytes.decode("utf-8", errors="replace"), fallback_title)
    elif ext == ".docx":
        title, sections = _extract_docx(raw_bytes, fallback_title)
    elif ext in {".csv", ".tsv"}:
        title, sections = extract_csv(raw_bytes, fallback_title, delimiter="\t" if ext == ".tsv" else ",")
    elif ext == ".xlsx":
        title, sections = extract_xlsx(raw_bytes, fallback_title)
    elif ext == ".pptx":
        title, sections = extract_pptx(raw_bytes, fallback_title)
    else:
        title, sections = _extract_pdf(raw_bytes, fallback_title)
    sec_blocks = "\n\n".join(f"## {heading}\n{body}" for heading, body in sections)
    return _topics.normalize_document_tags(f"# {title}\n\n{sec_blocks}\n", filename, tags)


MAX_LOCAL_INGEST_BYTES = 15 * 1024 * 1024


def convert_file_to_chunks(file_path: Path, tags: list[str] | None = None, knowledge_dir: Path | None = None, *, read_only: bool = False, stem_override: str | None = None) -> list[KnowledgeChunk]:
    """Parse any supported document file into KnowledgeChunks without mutating read-only vaults."""
    if file_path.stat().st_size > MAX_LOCAL_INGEST_BYTES:
        raise ValueError("Document exceeds the 15 MiB indexing size limit")
    stem = stem_override or (file_path.relative_to(knowledge_dir).with_suffix("").as_posix() if knowledge_dir else file_path.stem)
    if file_path.suffix.lower() == ".md":
        original = file_path.read_text(encoding="utf-8", errors="replace")
        normalized = _topics.normalize_document_tags(original, file_path.name)
        if not read_only and _topics.has_placeholder_tags(original) and normalized != original:
            with suppress(OSError, ValueError):
                atomic_write_text(file_path, normalized)
        return parse_markdown_text(normalized, stem, str(file_path))
    return parse_markdown_text(convert_bytes_to_markdown(file_path.name, file_path.read_bytes(), tags=tags), stem, str(file_path))
