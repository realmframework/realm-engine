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
        'id="rail-status-popover" popover="auto"',
        'id="drawer-panel-chat"',
        'id="drawer-panel-library"',
        'id="drawer-panel-work"',
        'id="drawer-panel-workflows"',
        'id="drawer-panel-studio"',
        'id="wb-center-controls"',
        'id="wb-right-toggle-wrap"',
        'id="topbar-timer-pill"',
        'id="clear-areas-btn"',
        'data-i18n-span="sh_new_note"',
        'id="realm-surface-polish-styles"',
        "--surface-glass",
    ):
        assert needle in html
    for removed in (
        'id="sidebar-collapse-btn"',
        'id="layout-left-btn"',
        'id="sidebar-workflows-btn"',
        'id="app-topbar"',
        'id="topbar-more-menu"',
        'id="rail-more-menu"',
        'id="new-chat-btn"',
        'id="free-chat-mode-btn"',
        'id="right-tab-doc"',
        'id="inspector-toggle-btn"',
        'id="wb-global-controls"',
        'data-work-jump="kanban"',
    ):
        assert removed not in html


def test_four_zone_workbench_controls_and_zero_fake_mini_widgets(area_client: TestClient) -> None:
    html = area_client.get("/").text
    for needle in (
        'id="layout-bottom-btn"',
        'id="layout-right-btn"',
        'id="center-tablist"',
        'id="center-agent-select"',
        'id="center-add-tab-btn"',
        'id="center-split-btn"',
        'id="split-chat-tablist"',
        'id="split-agent-select"',
        "renderChatTabStrip",
        "populateAgentSelect",
        "syncSplitPaneAccent",
        "syncGlobalControlsWidth",
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
        'id="right-tab-files"',
        'id="right-tab-copilot"',
        'id="right-tab-inspector"',
        'id="right-panel-files"',
        'id="right-panel-copilot"',
        'id="cp-agent-select"',
        'id="cp-model-select"',
        'id="cp-format-select"',
        'id="cp-input"',
        'id="cp-messages"',
        "syncCopilotControls",
        "syncCopilotPaneAccent",
        'id="right-files-tree"',
        'id="right-panel-inspector"',
        'id="center-file-view"',
        "openFileInCenterTab",
        "openCopilotForCurrentContext",
        "cpApplyAction",
        "renderRightFilesTree",
        "setRightSidebarTab",
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
