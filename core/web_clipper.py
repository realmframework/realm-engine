"""SSRF-guarded URL-to-Guide Web Clipper converting clean article HTML into local Markdown."""

import re
import socket
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx

from core.net_security import is_public_ip, resolve_pinned_url
from core.version import APP_VERSION

MAX_CLIP_BYTES = 2 * 1024 * 1024
_CLIP_PORTS = frozenset({80, 443, 8080, 8443})
_ALLOWED_CTYPES = ("text/html", "application/xhtml+xml", "text/plain", "text/markdown")
_SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "footer", "aside", "iframe", "form"}
_BLOCK_PREFIX = {"h1": "\n# ", "h2": "\n## ", "h3": "\n### ", "h4": "\n#### ", "p": "\n\n", "li": "\n- ", "blockquote": "\n> ", "br": "\n"}
_is_public_ip = is_public_ip


def _resolve_clip_target(raw_url: str, resolve_dns: bool = True) -> tuple[str, str, str, str]:
    """Validate public http(s) URL and return (url, ip_pinned_url, host_header, sni_host)."""
    return resolve_pinned_url(raw_url, allow_private=False, allowed_ports=_CLIP_PORTS, resolve_dns=resolve_dns, resolver=socket.getaddrinfo)


def validate_clip_url(raw_url: str, resolve_dns: bool = True) -> str:
    """Allow only public http(s) URLs; block localhost, private/loopback/non-global IPs."""
    return _resolve_clip_target(raw_url, resolve_dns=resolve_dns)[0]


class _ArticleExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.body_parts: list[str] = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        t = tag.lower()
        if t in _SKIP_TAGS:
            self._skip_depth += 1
        elif self._skip_depth == 0:
            if t == "title":
                self._in_title = True
            elif t in _BLOCK_PREFIX:
                self.body_parts.append(_BLOCK_PREFIX[t])

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        elif t == "title":
            self._in_title = False
        elif t in {"h1", "h2", "h3", "h4", "p", "blockquote"} and self._skip_depth == 0:
            self.body_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        cleaned = re.sub(r"\s+", " ", data)
        if self._in_title:
            self.title_parts.append(cleaned)
        elif cleaned.strip():
            self.body_parts.append(cleaned)


def _safe_yaml_scalar(value: str) -> str:
    return re.sub(r"[\r\n]+", " ", value).replace('"', "'").strip()


def html_to_clean_markdown(html_text: str, source_url: str) -> tuple[str, str]:
    """Extract readable title + Markdown with clean YAML frontmatter from HTML."""
    parser = _ArticleExtractor()
    parser.feed(html_text)
    raw_title = re.sub(r"\s+", " ", "".join(parser.title_parts)).strip()
    title = (raw_title or urlparse(source_url).netloc or "Clipped Article")[:140]
    body = re.sub(r"\n{3,}", "\n\n", "".join(parser.body_parts)).strip()
    if not body:
        raise ValueError("No readable article text could be extracted from this page")
    safe_title, safe_url = _safe_yaml_scalar(title), _safe_yaml_scalar(source_url)
    clipped_at = datetime.now(UTC).strftime("%Y-%m-%d")
    return title, f'---\ntitle: "{safe_title}"\nsource_url: "{safe_url}"\nclipped_at: {clipped_at}\ntags: [web-clip]\n---\n\n# {safe_title}\n\n> Source: {safe_url}\n\n{body}\n'


def clip_url_to_markdown(raw_url: str, timeout: float = 12.0) -> tuple[str, str]:
    """Fetch a public web page safely (per-hop IP-pinned client, content-type check, streaming cap)."""
    headers = {"User-Agent": f"REALM-Engine/{APP_VERSION} (+local-first-clipper)", "Accept": "text/html,text/plain;q=0.9", "Connection": "close"}
    current = raw_url
    for _ in range(4):
        current, pinned_url, host_hdr, sni_host = _resolve_clip_target(current, resolve_dns=True)
        with httpx.Client(timeout=timeout, follow_redirects=False, trust_env=False, headers=headers) as client:
            req = client.build_request("GET", pinned_url, headers={"Host": host_hdr}, extensions={"sni_hostname": sni_host})
            res = client.send(req, stream=True)
            try:
                if res.is_redirect and res.headers.get("location"):
                    current = urljoin(current, res.headers["location"])
                    continue
                if res.status_code >= 400:
                    raise ValueError(f"Page returned HTTP {res.status_code}")
                ctype = res.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                if ctype and ctype not in _ALLOWED_CTYPES:
                    raise ValueError(f"Unsupported content type for clipping: {ctype}")
                buf = bytearray()
                for chunk in res.iter_bytes():
                    buf.extend(chunk)
                    if len(buf) > MAX_CLIP_BYTES:
                        raise ValueError("Web page exceeds the 2 MB clipping size limit")
                text = bytes(buf).decode("utf-8", errors="replace")
            finally:
                res.close()
        if ctype in {"text/plain", "text/markdown"}:
            title = _safe_yaml_scalar((urlparse(current).path.rstrip("/").split("/")[-1] or urlparse(current).netloc)[:120])
            clipped_at = datetime.now(UTC).strftime("%Y-%m-%d")
            return title, f'---\ntitle: "{title}"\nsource_url: "{_safe_yaml_scalar(current)}"\nclipped_at: {clipped_at}\ntags: [web-clip]\n---\n\n{text.strip()}\n'
        return html_to_clean_markdown(text, current)
    raise ValueError("Too many redirects while clipping URL")
