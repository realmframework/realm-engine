"""True-DRY Single-Bar 4-Zone Workbench Markup: Unified Chat Tabs, Split Chat, Bottom Tools & Engine Inspector."""

from features.ui.icons import (
    ICON_CHEVRON_UP,
    ICON_MORE,
    ICON_SIDEBAR_LEFT,
    ICON_SPLIT_EDITOR,
)

CENTER_TABBAR_HTML: str = (
    '<header id="center-tabbar" class="wb-zone-bar" aria-label="Workspace bar">'
    '<div class="wb-bar-left">'
    f'<button id="sidebar-open-btn" aria-label="Expand sidebar" data-i18n-aria-label="aria_expand_rail" type="button" class="hidden topbar-icon-btn">{ICON_SIDEBAR_LEFT}</button>'
    '<div id="center-chat-tabs-group" class="wb-tabs-with-add">'
    '<div id="center-tablist" role="tablist" aria-label="Open chats" data-i18n-aria-label="wb_open_chats_aria" class="wb-tab-strip"></div>'
    '<button id="center-add-tab-btn" type="button" aria-label="New Chat" title="New Chat" data-i18n-aria-label="new_chat" data-i18n-title="new_chat" class="wb-icon-btn wb-tab-add-btn">+</button>'
    "</div>"
    "</div>"
    '<div id="center-chat-actions" class="wb-bar-actions">'
    '<label for="center-agent-select" class="visually-hidden" data-i18n="sh_st_agent">Active Agent</label>'
    '<select id="center-agent-select" aria-label="Active Agent" data-i18n-aria-label="sh_st_agent" class="wb-compact-select"></select>'
    f'<button id="center-split-btn" type="button" aria-pressed="false" aria-label="Split chat right" title="Split chat right" data-i18n-aria-label="sh_toggle_right" data-i18n-title="sh_toggle_right" class="wb-icon-btn">{ICON_SPLIT_EDITOR}</button>'
    "</div>"
    "</header>"
)

CENTER_SPLIT_PANE_HTML: str = (
    '<div id="center-split-resizer" hidden role="separator" tabindex="0" aria-orientation="vertical" aria-valuemin="28" aria-valuemax="72" aria-valuenow="50" aria-label="Resize split chats" data-i18n-aria-label="sp_resize_aria" class="wb-resizer wb-resizer-v"></div>'
    '<section id="center-split-pane" hidden aria-label="Split Chat" data-i18n-aria-label="sp_pane_aria">'
    '<header class="wb-zone-bar">'
    '<div class="wb-bar-left">'
    '<div class="wb-tabs-with-add">'
    '<div id="split-chat-tablist" role="tablist" aria-label="Split chat tabs" class="wb-tab-strip"></div>'
    '<button id="split-chat-add-btn" type="button" aria-label="New split chat" title="New split chat" data-i18n-aria-label="new_chat" data-i18n-title="new_chat" class="wb-icon-btn wb-tab-add-btn">+</button>'
    "</div>"
    "</div>"
    '<div class="wb-bar-actions">'
    '<label for="split-agent-select" class="visually-hidden" data-i18n="sp_agent_aria">Split chat agent</label>'
    '<select id="split-agent-select" aria-label="Split chat agent" data-i18n-aria-label="sp_agent_aria" class="wb-compact-select"></select>'
    '<button id="split-chat-close-btn" type="button" aria-label="Close split chat" title="Close split chat" data-i18n-aria-label="sp_close" data-i18n-title="sp_close" class="wb-icon-btn">✕</button>'
    "</div>"
    "</header>"
    '<iframe id="center-split-frame" class="wb-embed-frame" title="Split Chat"></iframe>'
    "</section>"
)

BOTTOM_PANEL_HTML: str = (
    '<div id="bottom-panel-resizer" hidden role="separator" tabindex="0" aria-orientation="horizontal" aria-valuemin="22" aria-valuemax="78" aria-valuenow="56" aria-label="Resize bottom panel" data-i18n-aria-label="bp_resize_aria" class="wb-resizer wb-resizer-h"></div>'
    '<section id="bottom-panel" hidden aria-label="Work tools panel" data-i18n-aria-label="bp_panel_aria">'
    '<header class="wb-zone-bar">'
    '<div id="bottom-panel-tablist" role="tablist" aria-label="Bottom panel tools" data-i18n-aria-label="bp_tools_aria" class="wb-tab-strip">'
    '<button type="button" role="tab" id="bp-tab-work" data-bp-tool="work" aria-selected="true" class="wb-zone-tab"><span data-i18n="work_board_nav">Board &amp; Calendar</span></button>'
    '<button type="button" role="tab" id="bp-tab-focus" data-bp-tool="focus" aria-selected="false" class="wb-zone-tab"><span data-i18n="focus_nav">Focus &amp; Goals</span></button>'
    '<button type="button" role="tab" id="bp-tab-impact" data-bp-tool="impact" aria-selected="false" class="wb-zone-tab"><span data-i18n="impact_nav">Time &amp; Impact</span></button>'
    '<button type="button" role="tab" id="bp-tab-workflows" data-bp-tool="workflows" aria-selected="false" class="wb-zone-tab"><span data-i18n="workflows_nav">Workflows</span></button>'
    '<button type="button" role="tab" id="bp-tab-library" data-bp-tool="library" aria-selected="false" class="wb-zone-tab"><span data-i18n="library">Library</span></button>'
    "</div>"
    '<div class="wb-bar-actions">'
    f'<button id="bottom-panel-more-btn" type="button" popovertarget="bottom-panel-more-menu" aria-expanded="false" aria-label="Show or hide bottom panel tools" title="Show or hide tools" data-i18n-aria-label="bp_manage_tools" data-i18n-title="bp_manage_tools" class="wb-icon-btn">{ICON_MORE}</button>'
    '<div id="bottom-panel-more-menu" popover="auto" class="rail-popover" aria-label="Bottom panel tools">'
    '<div focusgroup="menu nomemory" class="bp-menu-group" aria-label="Toggle visible tools">'
    '<button type="button" role="menuitemcheckbox" aria-checked="true" data-bp-vis="work" class="shell-pop-item bp-check-item"><span data-i18n="work_board_nav">Board &amp; Calendar</span></button>'
    '<button type="button" role="menuitemcheckbox" aria-checked="true" data-bp-vis="focus" class="shell-pop-item bp-check-item"><span data-i18n="focus_nav">Focus &amp; Goals</span></button>'
    '<button type="button" role="menuitemcheckbox" aria-checked="true" data-bp-vis="impact" class="shell-pop-item bp-check-item"><span data-i18n="impact_nav">Time &amp; Impact</span></button>'
    '<button type="button" role="menuitemcheckbox" aria-checked="true" data-bp-vis="workflows" class="shell-pop-item bp-check-item"><span data-i18n="workflows_nav">Workflows</span></button>'
    '<button type="button" role="menuitemcheckbox" aria-checked="true" data-bp-vis="library" class="shell-pop-item bp-check-item"><span data-i18n="library">Library</span></button>'
    "</div>"
    "</div>"
    f'<button id="bottom-panel-max-btn" type="button" aria-pressed="false" aria-label="Maximize panel size" title="Maximize panel size" data-i18n-aria-label="bp_max_aria" data-i18n-title="bp_max_aria" class="wb-icon-btn">{ICON_CHEVRON_UP}</button>'
    '<button id="bottom-panel-close-btn" type="button" aria-label="Close panel" title="Close panel" data-i18n-aria-label="bp_close_aria" data-i18n-title="bp_close_aria" class="wb-icon-btn">✕</button>'
    "</div>"
    "</header>"
    '<iframe id="bottom-panel-frame" class="wb-embed-frame" title="Work tools panel"></iframe>'
    "</section>"
)

RIGHT_SIDEBAR_HTML: str = (
    '<div id="right-sidebar-resizer" hidden role="separator" tabindex="0" aria-orientation="vertical" aria-valuemin="260" aria-valuemax="560" aria-valuenow="348" aria-label="Resize Engine Inspector" data-i18n-aria-label="rs_resize_aria" class="wb-resizer wb-resizer-v"></div>'
    '<aside id="inspector-sidebar" hidden aria-label="Engine Inspector">'
    '<header class="wb-zone-bar">'
    '<span data-i18n="insp_title" class="wb-zone-title">Engine Inspector</span>'
    '<button id="close-inspector-btn" type="button" aria-label="Close Engine Inspector" data-i18n-aria-label="aria_close_inspector" class="wb-icon-btn inspector-mobile-close">✕</button>'
    "</header>"
    '<div id="right-panel-inspector" class="right-sidebar-scroll">'
    '<div id="inspector-sidebar-body" class="flex flex-col gap-4 text-sm shrink-0 pb-10"></div>'
    "</div>"
    "</aside>"
)
