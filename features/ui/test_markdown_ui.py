"""Tests for the upgraded Markdown renderer, XSS safety, and universal /healthz endpoint."""

import json
import shutil
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from core.version import APP_VERSION
from features.ui import app as ui_app
from features.ui.markdown_script import MARKDOWN_SCRIPT

_ESCAPE_HELPER = (
    'function escapeHtml(v){return String(v).replace(/&/g,"&amp;").replace(/</g,"&lt;")'
    '.replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/\'/g,"&#39;");}\n'
)


def _run_js(expression: str) -> str:
    node = shutil.which("node")
    assert node is not None
    script = _ESCAPE_HELPER + MARKDOWN_SCRIPT + f"\nconsole.log(JSON.stringify({expression}));"
    out = subprocess.run([node, "-e", script], capture_output=True, text=True, check=True, timeout=5)
    return str(json.loads(out.stdout))


def test_healthz_works_in_both_local_and_public_modes(tmp_path: Path) -> None:
    local_res = TestClient(ui_app.app).get("/healthz")
    assert local_res.status_code == 200 and local_res.json() == {"status": "ok", "mode": "local", "version": APP_VERSION}

    vault = tmp_path / "ai-engineering"
    vault.mkdir()
    (vault / "guide.md").write_text("# Guide\n\n## Intro\nHello.\n", encoding="utf-8")
    pub_res = TestClient(ui_app.build_public_app(data_dir=tmp_path)).get("/healthz")
    assert pub_res.status_code == 200 and pub_res.json() == {"status": "ok", "mode": "public", "version": APP_VERSION}


def test_markdown_renderer_styles_and_scripts_ship_in_html() -> None:
    html = TestClient(ui_app.app).get("/").text
    for expected in (".md-table-wrap", ".md-pre-wrap", ".md-quote", ".md-math", "bindMarkdownLinks", "resolveRelativeGuideId"):
        assert expected in html


def test_markdown_renderer_handles_code_tables_links_italics_and_xss() -> None:
    if shutil.which("node") is None:
        return
    sample = (
        "### Stage Overview\n\n"
        "Combining _hybrid search_ with `snake_case_id` and [Docs](https://example.com) or [Related](../06-eval/metrics.md).\n\n"
        "> Grounded answers must cite retrieved evidence.\n\n"
        "| Stage | Purpose |\n| --- | --- |\n| BM25 | Exact terms |\n| Dense | Semantic recall |\n\n"
        "```sql\nSELECT id FROM chunks WHERE score > 0;\n```\n\n"
        "$$\nRRF(d) = 1 / (k + rank)\n$$\n\n"
        "1. First item\n   * Nested child\n\n"
        "[Click me](javascript:alert(1)) <script>evil()</script>"
    )
    rendered = _run_js(f"formatMarkdown({json.dumps(sample)})")
    assert "<em class='text-[#EEF2F8]/90 italic'>hybrid search</em>" in rendered
    assert "<code class='md-code-inline'>snake_case_id</code>" in rendered
    assert "href='https://example.com' target='_blank' rel='noopener noreferrer'" in rendered
    assert "data-md-doc='../06-eval/metrics.md'" in rendered
    assert "<blockquote class='md-quote'>" in rendered
    assert "<table class='md-table'>" in rendered and "<th>Stage</th>" in rendered and "<td>Exact terms</td>" in rendered
    assert "<div class='md-pre-lang'>sql</div>" in rendered and "&gt; 0;" in rendered
    assert "<div class='md-math'><code>RRF(d) = 1 / (k + rank)</code></div>" in rendered
    assert "padding-inline-start:1.1rem" in rendered
    assert "javascript:" not in rendered and "<script>" not in rendered

    resolved = _run_js("resolveRelativeGuideId('04-retrieval-and-rag/hybrid-search', '../06-eval/metrics.md')")
    assert resolved == "06-eval/metrics"
    sibling = _run_js("resolveRelativeGuideId('04-retrieval-and-rag/hybrid-search', 'pgvector.md')")
    assert sibling == "04-retrieval-and-rag/pgvector"
