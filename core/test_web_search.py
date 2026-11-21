"""Tests for privacy-guarded opt-in web search (Local-Only Lock enforcement & providers)."""

import httpx
import pytest

from core import secrets, web_search
from core.contracts import WorkspaceConfig


def test_web_search_is_strictly_blocked_when_local_only_or_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[str] = []
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: called.append("post") or httpx.Response(200))
    monkeypatch.setattr(httpx, "get", lambda *a, **kw: called.append("get") or httpx.Response(200))

    locked = WorkspaceConfig(strict_local_only=True, web_search_enabled=True, web_search_provider="duckduckgo")
    assert web_search.search_web_context("python 3.12 features", locked) == []

    disabled = WorkspaceConfig(strict_local_only=False, web_search_enabled=False, web_search_provider="duckduckgo")
    assert web_search.search_web_context("python 3.12 features", disabled) == []
    assert called == []


def test_duckduckgo_parser_unwraps_redirect_urls_and_tags_web(monkeypatch: pytest.MonkeyPatch) -> None:
    sample_html = (
        '<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fguide">Example Guide</a>'
        '<a class="result__snippet">Fast local hybrid search overview.</a>'
    )
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: httpx.Response(200, text=sample_html))
    cfg = WorkspaceConfig(strict_local_only=False, web_search_enabled=True, web_search_provider="duckduckgo")
    results = web_search.search_web_context("hybrid search", cfg)
    assert len(results) == 1
    assert results[0].chunk.title == "Web — Example Guide"
    assert results[0].chunk.url == "https://example.com/guide"
    assert results[0].chunk.tags == ["web"]
    assert "Fast local hybrid search" in results[0].chunk.content


def test_ollama_web_and_searxng_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(secrets, "get_api_key", lambda prov, explicit=None: "ollama-secret" if prov == "ollama_web" else None)
    seen: list[dict[str, object]] = []

    def fake_post(url: str, payload: dict[str, object], headers: dict[str, str] | None = None, timeout: float = 8.0) -> httpx.Response:
        seen.append({"url": url, "payload": payload, "headers": headers})
        return httpx.Response(200, json={"results": [{"title": "Ollama Docs", "url": "https://ollama.com/blog", "content": "Web search API."}]})

    monkeypatch.setattr(web_search, "post_cancellable", fake_post)
    cfg_ollama = WorkspaceConfig(strict_local_only=False, web_search_enabled=True, web_search_provider="ollama")
    res = web_search.search_web_context("ollama web search", cfg_ollama)
    assert len(res) == 1 and res[0].chunk.url == "https://ollama.com/blog"
    assert seen[0]["url"] == web_search.OLLAMA_WEB_URL

    monkeypatch.setattr(httpx, "get", lambda *a, **kw: httpx.Response(200, json={"results": [{"title": "SearX", "url": "https://docs.searxng.org", "content": "Private metasearch."}]}))
    cfg_searx = WorkspaceConfig(strict_local_only=False, web_search_enabled=True, web_search_provider="searxng", searxng_url="http://127.0.0.1:8080")
    res_sx = web_search.search_web_context("private search", cfg_searx)
    assert len(res_sx) == 1 and res_sx[0].chunk.title == "Web — SearX"

    bad_scheme = WorkspaceConfig(strict_local_only=False, web_search_enabled=True, web_search_provider="searxng", searxng_url="file:///etc/passwd")
    assert web_search.search_web_context("bad", bad_scheme) == []


def test_duckduckgo_lite_fallback_and_preamble_cleanup(monkeypatch: pytest.MonkeyPatch) -> None:
    seen_queries: list[tuple[str, str]] = []
    lite_html = '<a rel="nofollow" href="https://huyenchip.com/" class=\'result-link\'>Chip Huyen</a><td class="result-snippet">Author of AI Engineering.</td>'

    def fake_post(url: str, data: dict[str, str], **_kw: object) -> httpx.Response:
        seen_queries.append((url, data["q"]))
        if "lite.duckduckgo.com" in url:
            return httpx.Response(200, text=lite_html)
        return httpx.Response(202, text="<html>challenge</html>")

    monkeypatch.setattr(httpx, "post", fake_post)
    cfg = WorkspaceConfig(strict_local_only=False, web_search_enabled=True, web_search_provider="duckduckgo")
    results = web_search.search_web_context("Can you search the web for Chip Huyen AI Engineering?", cfg)
    assert len(results) == 1 and results[0].chunk.url == "https://huyenchip.com/"
    assert seen_queries == [(web_search.DDG_HTML_URL, "Chip Huyen AI Engineering"), (web_search.DDG_LITE_URL, "Chip Huyen AI Engineering")]
