"""Regression tests for Batch 5 client JS safety, Markdown XSS defense, and X-Ray overrides."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

from core.contracts import ChatTurnRequest, KnowledgeChunk, SearchQuery, SearchResult
from features.ui import query_engine
from features.ui.eco_sync_script import ECO_SYNC_SCRIPT
from features.ui.markdown_script import MARKDOWN_SCRIPT
from features.ui.script import CLIENT_SCRIPT
from features.ui.stream_script import STREAM_SCRIPT
from features.ui.studio_script import STUDIO_SCRIPT


def _run_node(code: str) -> str:
    if not shutil.which("node"):
        pytest.skip("node binary not installed")
    res = subprocess.run(["node", "-e", code], capture_output=True, text=True, check=False, timeout=10)
    assert res.returncode == 0, f"Node failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    return res.stdout


def test_client_script_passes_node_syntax_check() -> None:
    if not shutil.which("node"):
        pytest.skip("node binary not installed")
    js = re.sub(r"^<script>\s*|\s*</script>$", "", CLIENT_SCRIPT.strip())
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
        handle.write(js)
        tmp_path = Path(handle.name)
    try:
        res = subprocess.run(["node", "--check", str(tmp_path)], capture_output=True, text=True, check=False, timeout=10)
        assert res.returncode == 0, res.stderr
    finally:
        tmp_path.unlink(missing_ok=True)


def test_markdown_blocks_attribute_breakout_nul_injection_and_double_escape() -> None:
    prelude = (
        'function escapeHtml(v){return String(v).replace(/&/g,"&amp;").replace(/</g,"&lt;")'
        '.replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/\'/g,"&#39;");}\n'
        + MARKDOWN_SCRIPT
    )
    script = (
        prelude
        + """
const out = {
  breakout: formatInline("[click](https://example.com/`' onclick=alert(1)//`)"),
  nul: formatInline("\\u0000L0\\u0000 [ok](https://example.com)"),
  rejected: formatInline("[A & B](javascript:void0)"),
  rejectedParens: formatInline("[A & B](javascript:alert(1))"),
  guideFooter: formatMarkdown("Intro\\n\\nSources:\\n- Keep this in guides"),
  tutorFooter: formatMarkdown("Answer body.\\n\\nSources:\\n- Strip this footer", true),
};
console.log(JSON.stringify(out));
"""
    )
    data = json.loads(_run_node(script))
    assert "onclick=" not in data["breakout"] or "<a " not in data["breakout"]
    assert "\x00" not in data["nul"]
    assert "href='https://example.com'" in data["nul"]
    assert data["rejected"] == "A &amp; B"
    assert "javascript:" not in data["rejectedParens"] and "&amp;amp;" not in data["rejectedParens"]
    assert "Keep this in guides" in data["guideFooter"]
    assert "Strip this footer" not in data["tutorFooter"]
    assert "Answer body." in data["tutorFooter"]


def test_markdown_footer_regex_has_no_redos() -> None:
    prelude = (
        'function escapeHtml(v){return String(v).replace(/&/g,"&amp;").replace(/</g,"&lt;")'
        '.replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/\'/g,"&#39;");}\n'
        + MARKDOWN_SCRIPT
    )
    script = prelude + 'const evil = "x" + "\\n ".repeat(8000) + "Sources: y"; console.log(formatMarkdown(evil, true).length);'
    started = time.monotonic()
    _run_node(script)
    assert time.monotonic() - started < 2.0


def test_unicode_highlight_regex_matches_non_ascii_words() -> None:
    assert r"(?<![\\p{L}\\p{N}_])" in ECO_SYNC_SCRIPT
    script = """
const tokens = Array.from(new Set("Überprüfung evaluación".toLowerCase().split(/[^\\p{L}\\p{N}]+/u).filter(w => w.length >= 3)));
const escaped = tokens.map(t => t.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&"));
const re = new RegExp("(?<![\\\\p{L}\\\\p{N}_])(" + escaped.join("|") + ")(?![\\\\p{L}\\\\p{N}_])", "giu");
const matches = Array.from("Eine Überprüfung und evaluación fertig.".matchAll(re)).map(m => m[0]);
console.log(JSON.stringify(matches));
"""
    assert json.loads(_run_node(script)) == ["Überprüfung", "evaluación"]


def test_stream_scripts_flush_text_decoder_after_loop() -> None:
    assert "buffer += decoder.decode();" in STREAM_SCRIPT
    assert "buf += decoder.decode();" in STREAM_SCRIPT
    assert "buf += decoder.decode();" in STUDIO_SCRIPT


def test_query_engine_retrieve_applies_muted_and_pinned_doc_ids() -> None:
    chunks = [
        KnowledgeChunk(id="c1", doc_id="doc-a", title="Doc A", content="alpha", file_path="a.md", tags=[]),
        KnowledgeChunk(id="c2", doc_id="doc-b", title="Doc B", content="beta", file_path="b.md", tags=[]),
        KnowledgeChunk(id="c3", doc_id="doc-c", title="Doc C", content="gamma", file_path="c.md", tags=[]),
    ]
    req = ChatTurnRequest(
        query="alpha",
        ask_tutor=False,
        top_k=2,
        retrieval_mode="lexical",
        muted_doc_ids=["doc-a"],
        pinned_doc_ids=["doc-c"],
    )

    def _route(q: str, **_kw: object) -> dict[str, object]:
        return {"routed_query": q, "top_k": 2, "retrieval_mode": "lexical", "rrf_k": 60, "label": "Lookup"}

    def _search(_q: SearchQuery, cands: list[KnowledgeChunk], **_kw: object) -> list[SearchResult]:
        return [SearchResult(chunk=c, score=1.0) for c in cands if c.doc_id == "doc-b"]

    _, results, _ = query_engine.retrieve(req, chunks, [], _route, _search, lambda *_a, **_k: [])
    doc_ids = [r.chunk.doc_id for r in results]
    assert "doc-a" not in doc_ids
    assert doc_ids[0] == "doc-c"
    assert "doc-b" in doc_ids
