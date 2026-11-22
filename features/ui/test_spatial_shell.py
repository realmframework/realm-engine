"""Integration tests for v0.9.0 Codex-inspired Two-Tier Spatial Shell & Multi-Tab Workbench."""

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
    ):
        assert needle in html


def test_multi_tab_side_workbench_and_launcher_tiles(area_client: TestClient) -> None:
    html = area_client.get("/").text
    for needle in (
        'id="wb-side-tablist"',
        'id="wb-side-add-tab"',
        'id="split-launcher-body"',
        'id="wb-launcher-search"',
        'data-open-side-tile="chat"',
        'data-open-side-tile="guide"',
        'data-open-side-tile="tasks"',
        'data-open-side-tile="focus"',
        'data-open-side-tile="impact"',
        'id="split-tasks-body"',
        'id="split-focus-body"',
        'id="split-impact-body"',
        "openSideWorkbenchTab",
        "toggleContextDrawer",
    ):
        assert needle in html
