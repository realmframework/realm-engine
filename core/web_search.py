"""Privacy-guarded opt-in web search (strictly disabled under Local-Only Lock)."""

import html
import re
from urllib.parse import parse_qs, unquote, urlparse

import httpx

from core import secrets
from core.cancellation import check_cancelled, post_cancellable
from core.contracts import KnowledgeChunk, SearchResult, WorkspaceConfig

WEB_TIMEOUT_SECONDS = 8.0
OLLAMA_WEB_URL = "https://ollama.com/api/web_search"
DDG_HTML_URL = "https://html.duckduckgo.com/html/"
_TAG_RE = re.compile(r"<[^>]+>")
_DDG_LINK_RE = re.compile(
    r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>([\s\S]*?)</a>',
    re.IGNORECASE,
)
_DDG_SNIPPET_RE = re.compile(
    r'<a[^>]+class="result__snippet"[^>]*>([\s\S]*?)</a>|<div[^>]+class="result__snippet"[^>]*>([\s\S]*?)</div>',
    re.IGNORECASE,
)


def _clean_text(raw: str, limit: int = 500) -> str:
    text = html.unescape(_TAG_RE.sub(" ", raw))
    return re.sub(r"\s+", " ", text).strip()[:limit]


def _unwrap_ddg_url(raw_href: str) -> str:
    href = html.unescape(raw_href).strip()
    if href.startswith("//"):
        href = "https:" + href
    parsed = urlparse(href)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        uddg = parse_qs(parsed.query).get("uddg")
        if uddg:
            href = unquote(uddg[0])
    target = urlparse(href)
    return href if target.scheme in {"http", "https"} and target.netloc else ""


def _build_results(items: list[tuple[str, str, str]], max_results: int) -> list[SearchResult]:
    out: list[SearchResult] = []
    for idx, (title, url, snippet) in enumerate(items[:max_results]):
        clean_title = _clean_text(title, 160)
        clean_snippet = _clean_text(snippet, 600)
        parsed = urlparse(url)
        if not clean_title or parsed.scheme not in {"http", "https"} or not parsed.netloc:
            continue
        chunk = KnowledgeChunk(
            id=f"web-{idx + 1}",
            title=f"Web — {clean_title}",
            file_path=url,
            url=url,
            content=clean_snippet or clean_title,
            tags=["web"],
        )
        out.append(SearchResult(chunk=chunk, score=round(0.62 - idx * 0.04, 3)))
    return out


def _search_ollama_web(query: str, max_results: int) -> list[SearchResult]:
    api_key = secrets.get_api_key("ollama_web")
    if not api_key:
        return []
    response = post_cancellable(
        OLLAMA_WEB_URL,
        {"query": query, "max_results": max_results},
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=WEB_TIMEOUT_SECONDS,
    )
    if getattr(response, "status_code", 500) >= 400:
        return []
    raw_items = response.json().get("results", [])
    items = [
        (str(item.get("title", "")), str(item.get("url", "")), str(item.get("content", "")))
        for item in raw_items
        if isinstance(item, dict)
    ]
    return _build_results(items, max_results)


def _search_searxng(query: str, base_url: str, max_results: int) -> list[SearchResult]:
    parsed = urlparse(base_url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return []
    endpoint = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}/search"
    response = httpx.get(
        endpoint,
        params={"q": query, "format": "json"},
        headers={"User-Agent": "REALM-Engine/0.2"},
        timeout=WEB_TIMEOUT_SECONDS,
    )
    if response.status_code >= 400:
        return []
    raw_items = response.json().get("results", [])
    items = [
        (str(item.get("title", "")), str(item.get("url", "")), str(item.get("content", "")))
        for item in raw_items
        if isinstance(item, dict)
    ]
    return _build_results(items, max_results)


def _search_duckduckgo(query: str, max_results: int) -> list[SearchResult]:
    response = httpx.post(
        DDG_HTML_URL,
        data={"q": query},
        headers={"User-Agent": "Mozilla/5.0 (compatible; REALM-Engine/0.2)"},
        timeout=WEB_TIMEOUT_SECONDS,
        follow_redirects=True,
    )
    if response.status_code >= 400:
        return []
    links = _DDG_LINK_RE.findall(response.text)
    snippets = [a or b for a, b in _DDG_SNIPPET_RE.findall(response.text)]
    items = [
        (title, _unwrap_ddg_url(href), snippets[i] if i < len(snippets) else "")
        for i, (href, title) in enumerate(links)
    ]
    return _build_results(items, max_results)


def search_web_context(query: str, config: WorkspaceConfig, max_results: int = 3) -> list[SearchResult]:
    """Fetch opt-in web snippets strictly when Local-Only Lock is OFF and web search is enabled."""
    if config.strict_local_only or not config.web_search_enabled:
        return []
    clean_query = re.sub(r"\s+", " ", query).strip()[:200]
    if not clean_query:
        return []
    check_cancelled()
    try:
        if config.web_search_provider == "ollama":
            results = _search_ollama_web(clean_query, max_results)
        elif config.web_search_provider == "searxng":
            results = _search_searxng(clean_query, config.searxng_url, max_results)
        else:
            results = _search_duckduckgo(clean_query, max_results)
        check_cancelled()
        return results
    except InterruptedError:
        raise
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return []
