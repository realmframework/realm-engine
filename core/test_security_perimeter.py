"""Regression tests for P1/P2/P3 core security perimeter, secret hygiene, logging, and versioning."""

from __future__ import annotations

import socket
import tomllib
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest

from core import (
    logging_config,
    mcp_bridge,
    net_security,
    output_formats,
    runtime,
    secrets,
    version,
)


def test_net_security_blocks_nat64_multicast_cgnat_imds_and_bad_ports() -> None:
    assert not net_security.is_public_ip("224.0.0.1")
    assert not net_security.is_public_ip("100.64.0.5")
    assert not net_security.is_public_ip("64:ff9b::169.254.169.254")
    assert not net_security.is_public_ip("fd00:ec2::254")
    assert net_security.is_public_ip("93.184.216.34")
    assert net_security.is_blocked_metadata_host("metadata.google.internal")
    assert net_security.is_blocked_metadata_host("169.254.169.254")
    assert net_security.is_blocked_metadata_host("fd00:ec2::254")
    with pytest.raises(ValueError, match="Port 8081"):
        net_security.resolve_pinned_url("https://93.184.216.34:8081/x", allowed_ports=frozenset({80, 443}), resolve_dns=False)
    fake_bad = lambda *_a, **_k: [(socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("64:ff9b::a9fe:a9fe", 443, 0, 0))]  # noqa: E731
    with pytest.raises(ValueError, match="blocked or non-global"):
        net_security.resolve_pinned_url("https://example.com/", resolve_dns=True, resolver=fake_bad)
    fake_ok = lambda *_a, **_k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]  # noqa: E731
    _, pinned, host_hdr, sni = net_security.resolve_pinned_url("https://example.com/a", resolve_dns=True, resolver=fake_ok)
    assert pinned == "https://93.184.216.34/a" and host_hdr == "example.com" and sni == "example.com"


def test_ollama_base_url_rejects_metadata_and_userinfo(monkeypatch: pytest.MonkeyPatch) -> None:
    for bad in ("http://169.254.169.254:11434", "http://user:pass@127.0.0.1:11434", "http://[fd00:ec2::254]:11434"):
        monkeypatch.setenv("OLLAMA_HOST", bad)
        assert runtime.ollama_base_url() == "http://127.0.0.1:11434"
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11435/")
    assert runtime.ollama_base_url() == "http://127.0.0.1:11435"


def test_secrets_masking_corrupt_recovery_and_scrubbing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert secrets._mask_key("short") == "saved"
    assert secrets._mask_key("sk-test-1234567890") == "…7890"
    sp = tmp_path / "secrets.json"
    monkeypatch.setattr(secrets, "SECRETS_FILE", sp)
    sp.write_text("{corrupt", encoding="utf-8")
    secrets.save_api_key("openai", "sk-live-abcdef123456")
    assert (tmp_path / "secrets.json.corrupt").is_file()
    assert secrets.get_api_key("openai") == "sk-live-abcdef123456"
    scrubbed = net_security.scrub_secrets("Auth Bearer tok_1234567890 key sk-live-abcdef123456 AIzaSy1234567890abcd")
    assert "tok_1234567890" not in scrubbed and "sk-live-" not in scrubbed and "AIzaSy" not in scrubbed


def test_mcp_bridge_respects_casefold_exclusions_and_area_allowlist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    area = tmp_path / "alpha"
    (area / "SecretDir").mkdir(parents=True)
    (area / "SecretDir" / "private.md").write_text("# Private\nSensitive", encoding="utf-8")
    (area / "public.md").write_text("# Public\nHello world", encoding="utf-8")
    (tmp_path / "beta").mkdir()
    (tmp_path / "beta" / "b.md").write_text("# Beta\nB", encoding="utf-8")
    (tmp_path / "workspace.json").write_text('{"excluded_subfolders": {"alpha": ["secretdir"]}}', encoding="utf-8")
    monkeypatch.setenv("REALM_MCP_AREAS", "alpha")
    with pytest.raises(ValueError, match="not permitted"):
        mcp_bridge.resolve_area(tmp_path, "beta")
    with pytest.raises(ValueError, match="unloaded subfolder"):
        mcp_bridge._call_mcp_tool("realm_read_guide", {"area": "alpha", "doc_id": "SecretDir/private"}, tmp_path)
    assert "Hello world" in mcp_bridge._call_mcp_tool("realm_read_guide", {"area": "alpha", "doc_id": "public"}, tmp_path)


def test_output_formats_atomic_symlink_and_corrupt_backup(tmp_path: Path) -> None:
    f = tmp_path / "output_formats.json"
    f.write_text("not-json", encoding="utf-8")
    saved = output_formats.save_custom_format(tmp_path, "My Brief", ["Overview"])
    assert saved.name == "My Brief" and (tmp_path / "output_formats.json.corrupt").is_file()
    link = tmp_path / "link_dir"
    link.mkdir()
    (link / "output_formats.json").symlink_to(f)
    assert output_formats.load_custom_formats(link) == []
    with pytest.raises(ValueError, match="symbolic link"):
        output_formats.save_custom_format(link, "Blocked", ["Sec"])


def test_logging_redacts_secrets_and_version_matches_pyproject(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    expected = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    assert version.APP_VERSION == expected
    assert version._FALLBACK_VERSION == expected
    assert f'#define AppVersion "{expected}"' in (root / "packaging/realm-engine.iss").read_text(encoding="utf-8")
    logger = logging_config.configure_logging(tmp_path)
    logger.warning("Upstream error Bearer secret_token_999999 and sk-proj-999999999")
    for h in logger.handlers:
        h.flush()
    log_text = logging_config.log_file_path(tmp_path).read_text(encoding="utf-8")
    assert "secret_token_999999" not in log_text and "sk-proj-999999999" not in log_text
    assert "[REDACTED]" in log_text
    events = logging_config.recent_log_events(5)
    assert events and all("secret_token_999999" not in e["message"] for e in events)
    for h in list(logger.handlers):
        if isinstance(h, RotatingFileHandler):
            logger.removeHandler(h)
            h.close()
