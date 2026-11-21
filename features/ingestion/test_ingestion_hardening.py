"""Regression tests for ingestion, anonymizer, parsers, extractors, and embedder (Batch 3)."""

import csv
import io
import zipfile
from pathlib import Path
from typing import Any

import httpx
import pytest

from core.contracts import KnowledgeChunk
from features.ingestion import anonymizer, converters, embedder, parser, service
from features.ingestion.office_extractors import extract_csv, extract_xlsx


def test_anonymizer_preserves_technical_docs_and_tight_regexes() -> None:
    assert anonymizer.extract_filename_names("Kubernetes_Guide.pdf") == []
    assert anonymizer.extract_filename_names("Architecture_Overview.md") == []
    text = "Coords: 52.520008, 13.404954\nTotal: 12345\nSummary\nIBAN: de89370400440532013000\n"
    rep = anonymizer.inspect_anonymization(text, "Kubernetes_Guide.pdf")
    scrubbed = str(rep["scrubbed_text"])
    assert "52.520008" in scrubbed and "Total: 12345" in scrubbed and "[REDACTED_IBAN]" in scrubbed


def test_parser_and_read_only_ingestion_integrity(tmp_path: Path) -> None:
    md = "\ufeffIntro lead text.\n\n---\n\nKept after rule.\n\n```python\n## not a heading\n```\n\n## Real Section\nBody.\n"
    chunks = parser.parse_markdown_text(md, "doc", "doc.md")
    titles = [c.title for c in chunks]
    assert any("Overview" in t for t in titles) and any("Real Section" in t for t in titles)
    assert not any("not a heading" in t for t in titles)
    assert any("Kept after rule." in c.content for c in chunks)

    uploaded_md = b"---\ntitle: Frontmatter Note\ntags: [ops]\n---\n# Frontmatter Note\nBody.\n"
    assert converters.convert_bytes_to_markdown("fm.md", uploaded_md).startswith("---\n")

    legacy = tmp_path / "legacy.md"
    orig = "# Legacy\nTags: uploaded\n\n## Overview\nText.\n"
    legacy.write_text(orig, encoding="utf-8")
    (tmp_path / "broken.pdf").write_bytes(b"not-a-pdf")
    out = service.ingest_directory(tmp_path, read_only=True)
    assert legacy.read_text(encoding="utf-8") == orig
    assert any(c.doc_id == "legacy" for c in out)


def test_office_extractors_sparse_cols_rels_and_csv_error(monkeypatch: pytest.MonkeyPatch) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Revenue" r:id="rId9"/></sheets></workbook>')
        zf.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="rId9" Target="worksheets/sheet2.xml"/></Relationships>')
        zf.writestr("xl/worksheets/sheet2.xml", '<worksheet><sheetData><row><c t="inlineStr"><is><t>A</t></is></c><c r="AAAAAA1" t="inlineStr"><is><t>Far</t></is></c></row></sheetData></worksheet>')
    _, sections = extract_xlsx(buf.getvalue(), "book")
    assert sections[0][0] == "Revenue" and "| A |" in sections[0][1]

    def _boom(*_a: Any, **_kw: Any) -> Any:
        raise csv.Error("field larger than field limit")

    monkeypatch.setattr(csv, "reader", _boom)
    with pytest.raises(ValueError):
        extract_csv(b"a,b\n1,2\n", "bad")


def test_embedder_cooldown_status_check_and_index_sorting(monkeypatch: pytest.MonkeyPatch) -> None:
    embedder.reset_ollama_status()
    calls = 0

    def _fail_post(*_a: Any, **_kw: Any) -> Any:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx, "post", _fail_post)
    assert embedder.embed_batch(["hello"]) == []
    assert embedder.is_ollama_offline() is True
    assert embedder.embed_batch(["hello again"]) == [] and calls == 1

    monkeypatch.setattr(embedder, "_OFFLINE_UNTIL", 0.0)
    assert embedder.is_ollama_offline() is False

    class _Resp:
        status_code = 200
        def json(self) -> dict[str, object]:
            return {"data": [{"index": 1, "embedding": [0.0, 1.0]}, {"index": 0, "embedding": [1.0, 0.0]}]}

    monkeypatch.setattr(httpx, "post", lambda *_a, **_kw: _Resp())
    vecs = embedder.embed_batch(["a", "b"], provider="openai", api_key="sk-test")
    assert vecs == [[1.0, 0.0], [0.0, 1.0]]
    c = KnowledgeChunk(id="c1", title="T", content="Body", tags=[], file_path="a.md")
    assert embedder.hydrate_embeddings([c], [], embed_missing=False)[0].id == "c1"
