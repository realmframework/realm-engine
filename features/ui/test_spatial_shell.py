"""Integration tests for Two-Tier Spatial Shell & True-DRY VS Code 4-Zone Workbench."""

from fastapi.testclient import TestClient


def test_spatial_shell_activity_rail_drawer_panels_and_topbar(area_client: TestClient) -> None:
    html = area_client.get("/").text
    for needle in (
        'id="activity-rail"',
        'id="rail-drawer-toggle"',
        'id="rail-home-btn"',
        'id="rail-library-btn"',
        'id="rail-work-btn"',
        'id="rail-workflows-btn"',
        'id="rail-studio-btn"',
        'id="mobile-rail-strip"',
        'id="rail-more-menu" popover="auto"',
        'id="rail-status-popover" popover="auto"',
        'id="drawer-panel-chat"',
        'id="drawer-panel-library"',
        'id="drawer-panel-work"',
        'id="drawer-panel-workflows"',
        'id="drawer-panel-studio"',
        'id="app-topbar"',
        'id="topbar-title"',
        'id="topbar-timer-pill"',
        'id="topbar-more-menu" popover="auto"',
        'data-i18n-span="sh_new_note"',
    ):
        assert needle in html
    assert 'id="sidebar-collapse-btn"' not in html
    assert 'id="layout-left-btn"' not in html
    assert 'id="sidebar-workflows-btn"' not in html


def test_four_zone_workbench_controls_and_zero_fake_mini_widgets(area_client: TestClient) -> None:
    html = area_client.get("/").text
    for needle in (
        'id="layout-bottom-btn"',
        'id="layout-right-btn"',
        'id="inspector-token-label"',
        'id="center-tablist"',
        'id="center-agent-select"',
        'id="center-add-tab-btn"',
        'id="center-split-btn"',
        'id="split-chat-tablist"',
        'id="split-agent-select"',
        "renderChatTabStrip",
        "populateAgentSelect",
        "syncSplitPaneAccent",
        'id="bottom-panel-tablist"',
        'id="bottom-panel-more-btn"',
        'id="bottom-panel-max-btn"',
        'id="bottom-panel-close-btn"',
        'data-bp-tool="work"',
        'data-bp-tool="focus"',
        'data-bp-tool="impact"',
        'data-bp-tool="workflows"',
        'data-bp-tool="library"',
        'data-bp-vis="work"',
        'role="menuitemcheckbox"',
        'id="right-sidebar-tablist"',
        'id="right-doc-select"',
        "syncCenterChatTab",
        "toggleContextDrawer",
        "openChatInSplit",
        "toggleBottomPanel",
        "setRightSidebarOpen",
    ):
        assert needle in html
    for removed in (
        'id="split-toggle-btn"',
        'id="split-mode-menu"',
        'id="split-launcher-body"',
        'id="split-tasks-body"',
        'id="split-focus-body"',
        'id="split-impact-body"',
    ):
        assert removed not in html
