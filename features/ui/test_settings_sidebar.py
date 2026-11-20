"""Settings ownership and rail contracts complement native browser interaction checks."""

import re

from fastapi.testclient import TestClient


def test_settings_has_three_native_panels_with_one_copy_of_controls(area_client: TestClient) -> None:
    html = area_client.get("/").text
    settings = html.split('<dialog id="settings-modal"', 1)[1].split("</dialog>", 1)[0]
    assert settings.count('role="tab"') == 3 and settings.count('role="tabpanel"') == 3
    for name in ("workspace", "rag", "privacy"):
        assert f'id="settings-tab-{name}"' in settings
        assert f'aria-labelledby="settings-tab-{name}"' in settings
    assert 'id="settings-panel-rag" role="tabpanel" aria-labelledby="settings-tab-rag" hidden' in settings
    assert 'id="settings-panel-privacy" role="tabpanel" aria-labelledby="settings-tab-privacy" hidden' in settings
    for control in ("provider", "api-key", "tts-model", "tts-voice", "daily-cloud-request-limit", "download-backup-btn", "rag-top-k", "rag-rrf-k", "rag-temperature", "governance-local-only", "run-audit-btn", "scrub-vault-btn", "export-compliance-btn"):
        assert settings.count(f'id="{control}"') == 1
    assert 'id="settings-advanced"' not in html
    assert 'id="rag-studio-modal"' not in html and 'id="rag-modal"' not in html
    assert 'id="cfg-strict-local-only"' not in html


def test_sidebar_owns_workspace_popover_and_history_without_topics_or_audit(area_client: TestClient) -> None:
    html = area_client.get("/").text
    sidebar = html.split('<aside id="sidebar"', 1)[1].split("</aside>", 1)[0]
    assert 'popovertarget="workspace-menu"' in sidebar and 'id="workspace-menu" popover="auto"' in sidebar
    assert 'id="knowledge-areas"' in sidebar and 'id="new-area-btn"' in sidebar
    assert re.search(r'id="recent-chats-list"[^>]*flex-1[^>]*overflow-y-auto', sidebar)
    assert "Topics" not in sidebar and 'id="tags"' not in sidebar
    for removed in ("ui-mode-switch", "data-ui-mode-choice", "sidebar-compliance-btn", "rag-studio-btn", "how-rag-btn"):
        assert removed not in html
    assert "localStorage.getItem(\"ui_mode\")" not in html and "setUIMode" not in html
    assert "library-topics" in html and "data-library-tag" in html
