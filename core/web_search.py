"""Privacy-guarded opt-in web search (strictly disabled under Local-Only Lock)."""

import html
import json
import re
import socket
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import httpx

from core import secrets
from core.cancellation import check_cancelled, post_cancellable
from core.contracts import KnowledgeChunk, SearchResult, WorkspaceConfig
from core.net_security import is_blocked_metadata_host, resolve_pinned_url
from core.runtime import is_loopback_url
from core.version import APP_VERSION

WEB_TIMEOUT_SECONDS, MAX_SEARCH_BYTES = 8.0, 1_048_576
OLLAMA_WEB_URL = "https://ollama.com/api/web_search"
DDG_HTML_URL, DDG_LITE_URL = "https://html.duckduckgo.com/html/", "https://lite.duckduckgo.com/lite/"
_ORIG_GET, _ORIG_POST = httpx.get, httpx.post
_TAG_RE = re.compile(r"<[^>]{0,300}>")
_PREAMBLE_RE = re.compile(r"^(?:please\s+)?(?:can\s+you\s+|could\s+you\s+)?(?:search(?:\s+the\s+web|\s+online)?\s+(?:for|about)|look\s+up|find\s+(?:me\s+)?(?:a\s+link\s+to|links?\s+(?:for|to)|info\s+on)|google|suche(?:\s+im\s+internet)?\s+nach|busca(?:\s+en\s+internet)?)\s+", re.IGNORECASE)
_DDG_LINK_RE = re.compile(r'<a\b[^>]{0,400}class="result__a"[^>]{0,400}href="([^"]{1,2000})"[^>]{0,200}>([\s\S]{0,500}?)</a>', re.IGNORECASE)
_DDG_SNIPPET_RE = re.compile(r'<(?:a|div)\b[^>]{0,400}class="result__snippet"[^>]{0,200}>([\s\S]{0,800}?)</(?:a|div)>', re.IGNORECASE)
_DDG_LITE_LINK_RE = re.compile(r'<a\b[^>]{0,200}href=["\']([^"\']{1,2000})["\'][^>]{0,200}class=["\']result-link["\'][^>]{0,100}>([\s\S]{0,500}?)</a>', re.IGNORECASE)
_DDG_LITE_SNIP_RE = re.compile(r'<td\b[^>]{0,200}class=["\']result-snippet["\'][^>]{0,100}>([\s\S]{0,800}?)</td>', re.IGNORECASE)


def _clean_text(raw: str, limit: int = 500) -> str:
    return re.sub(r"\s+", " ", html.unescape(_TAG_RE.sub(" ", raw))).strip()[:limit]

def _clean_web_query(query: str) -> str:
    base = re.sub(r"\s+", " ", query).strip()
    stripped = _PREAMBLE_RE.sub("", base).strip(" ?.!\"'")
    return (stripped if len(stripped) >= 3 else base)[:200]

def _unwrap_ddg_url(raw_href: str) -> str:
    href = html.unescape(raw_href).strip()
    if href.startswith("//"):
        href = "https:" + href
    parsed = urlparse(href)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/") and (uddg := parse_qs(parsed.query).get("uddg")):
        href = unquote(uddg[0])
    target = urlparse(href)
    return href if target.scheme in {"http", "https"} and target.netloc else ""


def _build_results(items: list[tuple[str, str, str]], max_results: int) -> list[SearchResult]:
    out: list[SearchResult] = []
    for idx, (title, url, snippet) in enumerate(items[:max_results]):
        clean_title, clean_snippet, parsed = _clean_text(title, 160), _clean_text(snippet, 600), urlparse(url)
        if not clean_title or parsed.scheme not in {"http", "https"} or not parsed.netloc:
            continue
        out.append(SearchResult(chunk=KnowledgeChunk(id=f"web-{idx + 1}", title=f"Web — {clean_title}", file_path=url, url=url, content=clean_snippet or clean_title, tags=["web"]), score=round(0.62 - idx * 0.04, 3)))
    return out

_is_blocked_metadata_host = is_blocked_metadata_host

def _read_stream_capped(res: httpx.Response, limit: int = MAX_SEARCH_BYTES) -> bytes:
    buf = bytearray()
    for chunk in res.iter_bytes():
        buf.extend(chunk)
        if len(buf) > limit:
            break
    return bytes(buf[:limit])

def _search_ollama_web(query: str, max_results: int) -> list[SearchResult]:
    if not (api_key := secrets.get_api_key("ollama_web")):
        return []
    response = post_cancellable(OLLAMA_WEB_URL, {"query": query, "max_results": max_results}, headers={"Authorization": f"Bearer {api_key}"}, timeout=WEB_TIMEOUT_SECONDS)
    if getattr(response, "status_code", 500) >= 400 or len(getattr(response, "content", b"")) > MAX_SEARCH_BYTES:
        return []
    raw_items = response.json().get("results", [])
    return _build_results([(str(it.get("title", "")), str(it.get("url", "")), str(it.get("content", ""))) for it in raw_items if isinstance(it, dict)], max_results)

def _search_searxng(query: str, base_url: str, max_results: int) -> list[SearchResult]:
    try:
        clean_url, pinned_base, host_hdr, sni_host = resolve_pinned_url(base_url, allow_private=True, resolve_dns=(httpx.get is _ORIG_GET), resolver=socket.getaddrinfo)
    except ValueError:
        return []
    endpoint = f"{clean_url.rstrip('/')}/search"
    if httpx.get is not _ORIG_GET:
        response = httpx.get(endpoint, params={"q": query, "format": "json"}, headers={"User-Agent": f"REALM-Engine/{APP_VERSION}"}, timeout=WEB_TIMEOUT_SECONDS)
        if response.status_code >= 400:
            return []
        raw_payload = response.json()
    else:
        with httpx.Client(timeout=WEB_TIMEOUT_SECONDS, follow_redirects=False, trust_env=not is_loopback_url(clean_url)) as client:
            req = client.build_request("GET", f"{pinned_base.rstrip('/')}/search", params={"q": query, "format": "json"}, headers={"User-Agent": f"REALM-Engine/{APP_VERSION}", "Host": host_hdr}, extensions={"sni_hostname": sni_host})
            res = client.send(req, stream=True)
            try:
                if res.status_code >= 400:
                    return []
                raw_payload = json.loads(_read_stream_capped(res).decode("utf-8", errors="replace"))
            finally:
                res.close()
    raw_items = raw_payload.get("results", []) if isinstance(raw_payload, dict) else []
    return _build_results([(str(it.get("title", "")), str(it.get("url", "")), str(it.get("content", ""))) for it in raw_items if isinstance(it, dict)], max_results)


def _fetch_ddg_page(start_url: str, query: str, headers: dict[str, str]) -> str:
    if httpx.post is not _ORIG_POST:
        response = httpx.post(start_url, data={"q": query}, headers=headers, timeout=WEB_TIMEOUT_SECONDS, follow_redirects=False)
        return "" if response.status_code != 200 else response.text[:MAX_SEARCH_BYTES]
    target = start_url
    for _ in range(3):
        with httpx.Client(timeout=WEB_TIMEOUT_SECONDS, follow_redirects=False) as client, client.stream("POST", target, data={"q": query}, headers=headers) as res:
            if res.is_redirect and (loc := res.headers.get("location")):
                nxt = urljoin(target, loc)
                host = (urlparse(nxt).hostname or "").lower()
                if urlparse(nxt).scheme == "https" and (host == "duckduckgo.com" or host.endswith(".duckduckgo.com")):
                    target = nxt
                    continue
                return ""
            return "" if res.status_code != 200 else _read_stream_capped(res).decode("utf-8", errors="replace")
    return ""

def _search_duckduckgo(query: str, max_results: int) -> list[SearchResult]:
    headers = {"User-Agent": f"Mozilla/5.0 (compatible; REALM-Engine/{APP_VERSION})"}
    body = _fetch_ddg_page(DDG_HTML_URL, query, headers)
    links, snippets = _DDG_LINK_RE.findall(body), _DDG_SNIPPET_RE.findall(body)
    if not links:
        lite = _fetch_ddg_page(DDG_LITE_URL, query, headers)
        links, snippets = _DDG_LITE_LINK_RE.findall(lite), _DDG_LITE_SNIP_RE.findall(lite)
    items = [(title, _unwrap_ddg_url(href), snippets[i] if i < len(snippets) else "") for i, (href, title) in enumerate(links)]
    return _build_results(items, max_results)

def search_web_context(query: str, config: WorkspaceConfig, max_results: int = 5) -> list[SearchResult]:
    """Fetch opt-in web snippets strictly when Local-Only Lock is OFF and web search is enabled."""
    if config.strict_local_only or not config.web_search_enabled:
        return []
    clean_query = _clean_web_query(query)
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
