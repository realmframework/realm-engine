"""Tests for custom workspace logo upload/reset and adaptive theme persistence."""

from pathlib import Path

from fastapi.testclient import TestClient

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 32
WEBP_BYTES = b"RIFF\x20\x00\x00\x00WEBP" + b"\x00" * 24


def test_custom_logo_upload_validation_and_reset(area_client: TestClient, tmp_path: Path) -> None:
    initial = area_client.get("/api/workspace/logo/status")
    assert initial.status_code == 200 and initial.json() == {"custom": False, "url": "/static/logo-512.png"}
    assert area_client.get("/api/workspace/logo").status_code == 200

    # Block SVG / script payloads and oversized files
    bad_svg = area_client.post("/api/workspace/logo", files={"file": ("logo.svg", b"<svg onload=alert(1)></svg>", "image/svg+xml")})
    assert bad_svg.status_code == 400
    too_big = area_client.post("/api/workspace/logo", files={"file": ("huge.png", PNG_BYTES + b"x" * (2 * 1024 * 1024), "image/png")})
    assert too_big.status_code == 413

    # Upload PNG, then replace with JPG & WebP (old files cleaned up)
    up_png = area_client.post("/api/workspace/logo", files={"file": ("brand.png", PNG_BYTES, "image/png")})
    assert up_png.status_code == 200 and up_png.json()["custom"] is True
    assert (tmp_path / "custom_logo.png").is_file()
    served = area_client.get("/api/workspace/logo")
    assert served.status_code == 200 and served.headers["content-type"] == "image/png" and served.content == PNG_BYTES

    up_jpg = area_client.post("/api/workspace/logo", files={"file": ("brand.jpg", JPG_BYTES, "image/jpeg")})
    assert up_jpg.status_code == 200 and not (tmp_path / "custom_logo.png").exists() and (tmp_path / "custom_logo.jpg").is_file()

    up_webp = area_client.post("/api/workspace/logo", files={"file": ("brand.webp", WEBP_BYTES, "image/webp")})
    assert up_webp.status_code == 200 and not (tmp_path / "custom_logo.jpg").exists() and (tmp_path / "custom_logo.webp").is_file()

    status = area_client.get("/api/workspace/logo/status").json()
    assert status["custom"] is True and str(status["url"]).startswith("/api/workspace/logo?v=")

    reset = area_client.delete("/api/workspace/logo")
    assert reset.status_code == 200 and reset.json() == {"custom": False, "url": "/static/logo-512.png"}
    assert not (tmp_path / "custom_logo.webp").exists()


def test_appearance_endpoint_persists_theme_and_rejects_invalid_hex(area_client: TestClient) -> None:
    saved = area_client.post(
        "/api/workspace/appearance",
        json={"theme_mode": "light", "theme_accent": "#A855F7", "theme_glow": "#38BDF8", "ambient_effects": False, "language": "de", "agent_name": "Lisbeth"},
    )
    assert saved.status_code == 200
    cfg = saved.json()["config"]
    assert cfg["theme_mode"] == "light" and cfg["theme_accent"] == "#A855F7" and cfg["theme_glow"] == "#38BDF8"
    assert cfg["ambient_effects"] is False and cfg["language"] == "de" and cfg["agent_name"] == "Lisbeth"

    # Partial update preserves previously saved theme/ambient fields
    lang_only = area_client.post("/api/workspace/appearance", json={"language": "es"})
    assert lang_only.status_code == 200
    merged = lang_only.json()["config"]
    assert merged["language"] == "es" and merged["theme_accent"] == "#A855F7" and merged["ambient_effects"] is False

    invalid = area_client.post(
        "/api/workspace/appearance",
        json={"theme_mode": "light", "theme_accent": "red; background:url(x)", "theme_glow": "#38BDF8"},
    )
    assert invalid.status_code == 422
    assert area_client.post("/api/workspace/appearance", json={"language": "fr"}).status_code == 422


def test_reset_defaults_restores_logo_and_config_without_deleting_guides(area_client: TestClient, tmp_path: Path) -> None:
    assert area_client.post("/api/workspace/logo", files={"file": ("brand.png", PNG_BYTES, "image/png")}).status_code == 200
    assert area_client.post(
        "/api/workspace",
        json={"app_title": "Custom Space", "strict_local_only": False, "run_mode": "cloud", "theme_mode": "light", "theme_accent": "#F472B6", "theme_glow": "#818CF8", "daily_cloud_request_limit": 99},
    ).status_code == 200

    res = area_client.post("/api/workspace/reset-defaults")
    assert res.status_code == 200
    body = res.json()
    cfg = body["config"]
    assert body["logo_url"] == "/static/logo-512.png"
    assert not (tmp_path / "custom_logo.png").exists()
    assert cfg["app_title"] == "My Knowledge Base" and cfg["agent_name"] == "Saga"
    assert cfg["theme_mode"] == "system" and cfg["theme_accent"] == "#4BB8E8" and cfg["theme_glow"] == "#6366F1"
    assert cfg["strict_local_only"] is True and cfg["run_mode"] == "local" and cfg["daily_cloud_request_limit"] == 50
    assert (tmp_path / "knowledge_base" / "shared.md").is_file()


def test_ui_exposes_adaptive_color_scheme_and_custom_theme_controls(area_client: TestClient) -> None:
    html = area_client.get("/").text
    assert '<meta name="color-scheme" content="light dark" />' in html
    assert "light-dark(" in html
    assert "color-mix(in oklab," in html
    assert "contrast-color(var(--accent))" in html
    for marker in (
        'id="hero-logo"', 'id="workspace-logo-input"', 'id="agent-name-input"', 'id="theme-accent-picker"', 'id="theme-glow-picker"',
        'data-theme-mode="system"', 'data-theme-mode="light"', 'id="ambient-aurora-canvas"', 'id="ambient-dots-canvas"', 'class="supernova-beam',
        'id="theme-ambient-toggle"', 'data-lang-choice="de"', 'data-lang-choice="es"',
        'id="onboarding-step-1"', 'id="onboarding-step-4"', 'id="onboarding-skip-btn"',
        '"Realm"', '"Lisbeth"', '"Salander"', '"Wasp"', '"Plague"', '"Blomkvist"', '"Millennium"', '"Erika"', '"Harriet"',
    ):
        assert marker in html
