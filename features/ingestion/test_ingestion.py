"""Unit tests for Markdown ingestion, YAML frontmatter, converters, and DSGVO anonymizer."""

import io
import zipfile
from pathlib import Path

import pytest

from core.contracts import AnonymizationReport, KnowledgeChunk
from features.ingestion.anonymizer import (
    PII_TYPES,
    anonymize_text,
    inspect_anonymization,
)
from features.ingestion.converters import convert_file_to_chunks
from features.ingestion.parser import parse_markdown_text
from features.ingestion.service import ingest_directory, parse_markdown_file


def test_ingest_directory_parses_markdown_and_frontmatter(tmp_path: Path) -> None:
    (tmp_path / "arch.md").write_text(
        "# AI-First Architecture\nTags: architecture, vertical-slice\n\n"
        "## Context Locality\nStrict slices isolate features.\n\n## Verification\nAST tests enforce rules.\n",
        encoding="utf-8",
    )
    (tmp_path / "rag.md").write_text(
        "---\ntitle: \"Hybrid Search: BM25 & Vectors\"\ndescription: Combine lexical and dense recall.\n"
        "tags: [rag, search, bm25]\nurl: /knowledge/ai-engineering/rag\n---\n\n"
        "## Reciprocal Rank Fusion\nRRF merges rankings without score normalization.\n",
        encoding="utf-8",
    )
    chunks: list[KnowledgeChunk] = ingest_directory(tmp_path)
    assert len(chunks) == 3 and len({c.id for c in chunks}) == 3
    rag_chunk = next(c for c in chunks if c.doc_id == "rag")
    assert rag_chunk.title == "Hybrid Search: BM25 & Vectors — Reciprocal Rank Fusion"
    assert rag_chunk.tags == ["rag", "search", "bm25"]
    assert rag_chunk.description == "Combine lexical and dense recall."
    assert rag_chunk.url == "/knowledge/ai-engineering/rag"


def test_frontmatter_multiline_tag_list_and_plain_fallback(tmp_path: Path) -> None:
    fm_doc = "---\ntitle: Agent Harness\ntags:\n  - agents\n  - tools\n---\n\n# Agent Harness\n\n## Loops\nBounded turns.\n"
    chunks = parse_markdown_text(fm_doc, "harness", "/tmp/harness.md")
    assert len(chunks) == 1 and chunks[0].tags == ["agents", "tools"] and chunks[0].title == "Agent Harness — Loops"

    plain_file = tmp_path / "custom_notes.md"
    plain_file.write_text("# Custom Team Runbook\nLine two has no tags prefix.\nLine three details deployment.\n", encoding="utf-8")
    plain = parse_markdown_file(plain_file)
    assert len(plain) == 1 and plain[0].title == "Custom Team Runbook — Overview" and plain[0].tags == ["general"]


def test_universal_converters_txt_html_docx_and_xml_cap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from features.ingestion import converters

    txt_file = tmp_path / "study_guide.txt"
    txt_file.write_text("Quantum entanglement links particle states across distance.", encoding="utf-8")
    html_file = tmp_path / "lecture_notes.html"
    html_file.write_text("<html><head><title>Neural Scaling</title><script>bad()</script></head><body><p>Chinchilla compute optimal scaling laws.</p></body></html>", encoding="utf-8")
    docx_file = tmp_path / "architecture_spec.docx"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("word/document.xml", "<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'><w:body><w:p><w:pPr><w:pStyle w:val='Heading1'/></w:pPr><w:r><w:t>Vector Indexing</w:t></w:r></w:p><w:p><w:r><w:t>HNSW graphs accelerate approximate nearest neighbor search.</w:t></w:r></w:p></w:body></w:document>")
    docx_file.write_bytes(buf.getvalue())

    assert len(convert_file_to_chunks(txt_file, tags=["physics"])) == 1
    assert "Neural Scaling" in convert_file_to_chunks(html_file, tags=["scaling"])[0].title
    assert "Vector Indexing" in convert_file_to_chunks(docx_file, tags=["systems"])[0].title
    assert len(ingest_directory(tmp_path)) == 3
    monkeypatch.setattr(converters, "MAX_DOCX_XML_BYTES", 32)
    with pytest.raises(ValueError, match="decompression limit"):
        convert_file_to_chunks(docx_file)


def test_anonymize_text_redacts_email_iban_phone_ip_and_filename_names() -> None:
    raw = "Contact max@example.de, IBAN DE89370400440532013000, IP 192.168.1.42, Tel +49 30 1234567."
    scrubbed, count = anonymize_text(raw)
    assert count == 4
    assert "[REDACTED_EMAIL]" in scrubbed and "[REDACTED_IBAN]" in scrubbed
    assert "[REDACTED_IP]" in scrubbed and "[REDACTED_PHONE]" in scrubbed
    assert "max@example.de" not in scrubbed and "DE89370400440532013000" not in scrubbed
    cv_scrubbed, cv_count = anonymize_text("Contact Jon Doe at test@example.com", filename="CV_Jon_Doe_2026.pdf")
    assert cv_count == 3 and "[REDACTED_EMAIL]" in cv_scrubbed and "[REDACTED_NAME]" in cv_scrubbed
    assert "Jon" not in cv_scrubbed and "Doe" not in cv_scrubbed


def test_inspect_anonymization_counts_masked_samples_and_consistency() -> None:
    raw = "Alice Smith\nalice@example.org\nDE89370400440532013000\n+49 30 1234567\n192.168.1.42"
    report = inspect_anonymization(raw, "CV_Alice_Smith.md")
    assert report["counts_by_type"] == {**dict.fromkeys(PII_TYPES, 0), "EMAIL": 1, "IBAN": 1, "PHONE": 1, "NAME": 2, "IP": 1}
    assert report["total_redacted"] == 6
    assert (report["scrubbed_text"], report["total_redacted"]) == anonymize_text(raw, "CV_Alice_Smith.md")
    samples = AnonymizationReport.model_validate(report).samples
    assert len(samples) == 6 and {s["type"] for s in samples} == {"EMAIL", "IBAN", "PHONE", "NAME", "IP"}
    for sample in samples:
        assert set(sample) == {"type", "original", "replacement", "context"}
        assert "***" in sample["original"] and sample["replacement"] in sample["context"]
        assert all(token not in sample["context"] for token in raw.splitlines())
    assert inspect_anonymization(str(report["scrubbed_text"]), "CV_Alice_Smith.md")["total_redacted"] == 0


def test_inspect_anonymization_sample_limit_and_overlap() -> None:
    report = inspect_anonymization(" ".join(f"learner{i}@example.org" for i in range(12)))
    assert report["total_redacted"] == 12 and len(AnonymizationReport.model_validate(report).samples) == 8
    assert inspect_anonymization("DE89370400440532013000")["total_redacted"] == 1
    assert inspect_anonymization("Nothing personal here")["counts_by_type"] == dict.fromkeys(PII_TYPES, 0)


def test_nested_subfolders_are_indexed_in_the_parent_area(tmp_path: Path) -> None:
    folder = tmp_path / "subfolder_a"
    folder.mkdir()
    content = "# Nested Guide\nTags: architecture\n\n## Nested Section\nShared area search marker.\n"
    (folder / "guide.md").write_text(content, encoding="utf-8")
    (tmp_path / "guide.md").write_text(content, encoding="utf-8")
    chunks = ingest_directory(tmp_path)
    assert len(chunks) == 2 and len({chunk.id for chunk in chunks}) == 2
    nested = next(chunk for chunk in chunks if chunk.subfolder == "subfolder_a")
    assert nested.doc_id == "subfolder_a/guide" and nested.id == "subfolder_a/guide-0"
    assert nested.content == "Shared area search marker."


def test_german_healthcare_pii_and_non_overlapping_counts() -> None:
    raw = "Geboren 14.03.1938, KV A123456789, Adresse 90402 Nürnberg, Hauptstraße 12."
    report = inspect_anonymization(raw)
    assert report["counts_by_type"] == {**dict.fromkeys(PII_TYPES, 0), "DOB": 1, "HEALTH_ID": 1, "ADDRESS": 2}
    assert report["total_redacted"] == 4
    text, count = anonymize_text(raw)
    assert count == 4 and text.count("[REDACTED_ADDRESS]") == 2
    assert "[REDACTED_DOB]" in text and "[REDACTED_HEALTH_ID]" in text
    assert all(token not in text for token in ("14.03.1938", "A123456789", "90402 Nürnberg", "Hauptstraße 12"))
    assert inspect_anonymization(text)["total_redacted"] == 0
