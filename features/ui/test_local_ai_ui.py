"""UI & full-app integration guards for Built-in Private AI zero-jargon UX and strict local lock."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_builtin_local_ai_ui_panels_zero_jargon_and_strict_local_models(area_client: TestClient) -> None:
    html = area_client.get("/").text
    for marker in (
        'id="onboarding-lai-panel"',
        'id="settings-lai-panel"',
        'id="onboarding-lai-setup-btn"',
        'id="settings-lai-setup-btn"',
        'id="settings-lai-progress-bar"',
        'data-lai-profile="eco"',
        'data-lai-profile="performance"',
        '<option value="builtin">Built-in Private AI</option>',
        "lai_offline_badge",
        "bindLocalAiUX",
    ):
        assert marker in html

    # Verify zero technical jargon inside user-facing Built-in Private AI panels
    for prefix in ("onboarding", "settings"):
        panel = html.split(f'id="{prefix}-lai-panel"', 1)[1].split("</section>", 1)[0]
        for jargon in ("GGUF", "Q4_K_M", "quantiz", "llama.cpp", "llama-server", "Vulkan"):
            assert jargon.lower() not in panel.lower()

    # Strict local-only lock allows builtin model listing & status endpoints while blocking cloud
    assert area_client.get("/api/local-ai/status").status_code == 200
    res_models = area_client.get("/api/models?provider=builtin")
    assert res_models.status_code == 200 and res_models.json()["provider"] == "builtin"
    assert area_client.get("/api/models?provider=openai").status_code == 403
