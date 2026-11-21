"""Shared SSRF IP-pinning, loopback verification, and secret-redaction primitives."""

import ipaddress
import re
import socket
from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse, urlunsplit

IPAddr = ipaddress.IPv4Address | ipaddress.IPv6Address
NAT64_WELL_KNOWN = ipaddress.ip_network("64:ff9b::/96")
NAT64_LOCAL = ipaddress.ip_network("64:ff9b:1::/48")
CGNAT_NET = ipaddress.ip_network("100.64.0.0/10")
METADATA_IPS = frozenset({"169.254.169.254", "100.100.100.200", "192.0.0.192", "fd00:ec2::254"})
_SECRET_TOKEN_RE = re.compile(
    r"(?:Bearer\s+[A-Za-z0-9._\-]{8,}|(?:sk|pk|xai|gsk|ms|rk|ant)-[A-Za-z0-9._\-]{8,}|AIza[0-9A-Za-z_\-]{12,})",
    re.IGNORECASE,
)


def parse_ip(host: str) -> IPAddr | None:
    try:
        ip = ipaddress.ip_address(host.strip("[]").split("%", 1)[0])
        return ip.ipv4_mapped if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None else ip
    except ValueError:
        return None


def is_metadata_or_unsafe_ip(ip: IPAddr) -> bool:
    if ip.is_link_local or ip.is_multicast or ip.is_unspecified or ip.is_reserved or str(ip).lower() in METADATA_IPS:
        return True
    if isinstance(ip, ipaddress.IPv4Address) and ip in CGNAT_NET:
        return True
    return isinstance(ip, ipaddress.IPv6Address) and (ip in NAT64_WELL_KNOWN or ip in NAT64_LOCAL)


def is_public_ip(host: str) -> bool:
    ip = parse_ip(host)
    return bool(ip and ip.is_global and not (ip.is_private or ip.is_loopback or is_metadata_or_unsafe_ip(ip)))


def is_loopback_ip(host: str) -> bool:
    ip = parse_ip(host)
    return bool(ip and ip.is_loopback)


def is_blocked_metadata_host(host: str) -> bool:
    low = host.lower().strip("[]").rstrip(".")
    if low == "metadata.google.internal" or low.endswith(".metadata.internal"):
        return True
    ip = parse_ip(low)
    return is_metadata_or_unsafe_ip(ip) if ip is not None else False


def resolve_pinned_url(
    raw_url: str,
    *,
    allow_private: bool = False,
    allowed_ports: frozenset[int] | None = None,
    resolve_dns: bool = True,
    resolver: Callable[..., list[Any]] = socket.getaddrinfo,
) -> tuple[str, str, str, str]:
    """Validate http(s) URL, reject unsafe IPs/ports, and return (url, ip_pinned_url, host_hdr, sni_host)."""
    url = raw_url.strip()
    if any(ord(c) < 32 or ord(c) == 127 for c in url):
        raise ValueError("Enter a valid http:// or https:// URL")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Enter a valid http:// or https:// URL")
    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
    except ValueError as exc:
        raise ValueError("Invalid URL port") from exc
    if allowed_ports is not None and port not in allowed_ports:
        raise ValueError(f"Port {port} is not permitted for outbound clipping")
    host = parsed.hostname.lower().rstrip(".")
    literal = parse_ip(host)
    if is_blocked_metadata_host(host):
        raise ValueError("Cloud metadata and non-routable targets are blocked")
    if not allow_private and (host == "localhost" or host.endswith((".local", ".internal")) or (literal is not None and not is_public_ip(host))):
        raise ValueError("Private, local, and loopback URLs cannot be clipped")
    pinned_ip = str(literal) if literal is not None else ""
    if resolve_dns:
        try:
            infos = resolver(host, port, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise ValueError(f"Could not resolve hostname: {host}") from exc
        resolved_ips = [str(info[4][0]) for info in infos]
        if not resolved_ips:
            raise ValueError(f"Could not resolve hostname: {host}")
        for addr in resolved_ips:
            parsed_addr = parse_ip(addr)
            if parsed_addr is None or (not is_public_ip(addr) if not allow_private else is_metadata_or_unsafe_ip(parsed_addr)):
                raise ValueError("URL resolves to a blocked or non-global IP address")
        pinned_ip = resolved_ips[0]
    if not pinned_ip:
        return url, url, parsed.netloc, host
    ip_host = f"[{pinned_ip}]" if ":" in pinned_ip else pinned_ip
    pinned_netloc = f"{ip_host}:{parsed.port}" if parsed.port else ip_host
    return url, urlunsplit((parsed.scheme, pinned_netloc, parsed.path or "/", parsed.query, "")), parsed.netloc, host


def scrub_secrets(text: str) -> str:
    """Redact API keys and bearer tokens from diagnostic or provider error messages."""
    return _SECRET_TOKEN_RE.sub("[REDACTED]", text)
