"""Two-Tier Spatial Shell: 52px Activity Rail, Context Drawer (with Left Files Tree) & Top-Right Layout Controls."""

from features.ui.icons import (
    ICON_AGENTS,
    ICON_BOTTOM_PANEL,
    ICON_COLLAPSE_ALL,
    ICON_EXPAND_ALL,
    ICON_FOCUS,
    ICON_FOLDER_TREE,
    ICON_FORMATS,
    ICON_GRAPH,
    ICON_HELP,
    ICON_HOME,
    ICON_IMPACT,
    ICON_LIBRARY,
    ICON_MORE,
    ICON_PLUS,
    ICON_RIGHT_SIDEBAR,
    ICON_SEARCH,
    ICON_SETTINGS,
    ICON_SIDEBAR_LEFT,
    ICON_WORK,
    ICON_WORKFLOWS,
)

ACTIVITY_RAIL_HTML: str = (
    '<nav aria-label="Primary" id="activity-rail">'
    f'<button id="rail-drawer-toggle" type="button" aria-expanded="true" aria-controls="sidebar" class="rail-btn" aria-label="Toggle left sidebar" title="Toggle left sidebar" data-i18n-aria-label="sh_toggle_drawer" data-i18n-title="sh_toggle_drawer">{ICON_SIDEBAR_LEFT}</button>'
    '<span class="rail-divider" aria-hidden="true"></span>'
    f'<button id="rail-home-btn" type="button" data-rail-section="chat" aria-current="page" class="rail-btn" aria-label="Chat &amp; Home" title="Chat &amp; Home" data-i18n-aria-label="sh_rail_chat" data-i18n-title="sh_rail_chat">{ICON_HOME}</button>'
    f'<button id="rail-files-btn" type="button" data-rail-section="files" class="rail-btn" aria-label="Files" title="Files" data-i18n-aria-label="sh_rail_files" data-i18n-title="sh_rail_files">{ICON_FOLDER_TREE}</button>'
    f'<button id="rail-library-btn" type="button" data-rail-section="library" class="rail-btn" aria-label="Library" title="Library" data-i18n-aria-label="sh_rail_library" data-i18n-title="sh_rail_library">{ICON_LIBRARY}</button>'
    f'<button id="rail-graph-btn" type="button" data-rail-section="graph" class="rail-btn" aria-label="Graph View" title="Graph View" data-i18n-aria-label="sh_rail_graph" data-i18n-title="sh_rail_graph">{ICON_GRAPH}</button>'
    f'<button id="rail-work-btn" type="button" data-rail-section="work" class="rail-btn" aria-label="Work OS: Board, Focus &amp; Impact" title="Work OS: Board, Focus &amp; Impact" data-i18n-aria-label="sh_rail_work" data-i18n-title="sh_rail_work">{ICON_WORK}<span id="rail-work-dot" hidden class="rail-badge-dot" aria-hidden="true"></span></button>'
    f'<button id="rail-workflows-btn" type="button" data-rail-section="workflows" class="rail-btn" aria-label="Workflows &amp; Schedules" title="Workflows &amp; Schedules" data-i18n-aria-label="sh_rail_workflows" data-i18n-title="sh_rail_workflows">{ICON_WORKFLOWS}</button>'
    f'<button id="rail-studio-btn" type="button" data-rail-section="studio" class="rail-btn" aria-label="Agents &amp; Answer Formats" title="Agents &amp; Answer Formats" data-i18n-aria-label="sh_rail_studio" data-i18n-title="sh_rail_studio">{ICON_AGENTS}</button>'
    '<span class="rail-spacer" aria-hidden="true"></span>'
    '<button id="rail-status-btn" type="button" popovertarget="rail-status-popover" aria-expanded="false" class="rail-btn" aria-label="Engine &amp; Privacy status" title="Engine &amp; Privacy status" data-i18n-aria-label="sh_status_aria" data-i18n-title="sh_status_aria"><span id="system-status-pill" role="status" aria-label="Engine ready" title="Engine ready" class="text-xs font-mono text-[#38D399]">●</span></button>'
    '<div id="rail-status-popover" popover="auto" class="rail-popover" aria-label="Workspace status">'
    '<div class="drawer-heading" style="padding:0 0 0.45rem" data-i18n="sh_status_head">LOCAL WORKSPACE STATUS</div>'
    '<div class="shell-pop-row"><span data-i18n="sh_st_privacy">Privacy</span><strong id="sh-pop-privacy" class="text-right">Local Only</strong></div>'
    '<div class="shell-pop-row"><span data-i18n="sh_st_agent">Active Agent</span><strong id="sh-pop-agent">Saga</strong></div>'
    '<div class="shell-pop-row"><span data-i18n="sh_st_timer">Work Timer</span><strong id="sh-pop-timer">00:00</strong></div>'
    "</div>"
    f'<button id="open-guide-btn" type="button" class="rail-btn" title="Quick Guide" aria-label="Quick Guide" data-i18n-title="aria_quick_guide" data-i18n-aria-label="aria_quick_guide">{ICON_HELP}</button>'
    f'<button id="open-settings-btn" type="button" class="rail-btn" title="Settings" aria-label="Settings" data-i18n-title="settings" data-i18n-aria-label="settings">{ICON_SETTINGS}</button>'
    "</nav>"
)

SIDEBAR_HTML: str = (
    '<aside id="sidebar" aria-label="Workspace sidebar" data-i18n-aria-label="aria_sidebar" class="fixed left-[52px] top-0 h-screen w-[248px] bg-[#0B1020] z-50 flex flex-col transition-transform duration-200">'
    '<div id="sidebar-header">'
    '<button id="workspace-switcher-btn" popovertarget="workspace-menu" aria-expanded="false" aria-controls="workspace-menu" type="button" aria-label="Switch workspace" data-i18n-aria-label="aria_switch_ws" class="flex-1 min-w-0 flex items-center gap-2 px-2 py-1.5 rounded-lg text-left hover:bg-white/5">'
    '<span id="workspace-color-dot" aria-hidden="true" class="flex items-center gap-1 shrink-0"></span><span id="brand-title" class="text-sm font-semibold truncate">Workspaces</span>'
    '<svg aria-hidden="true" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" class="ml-auto shrink-0"><path d="m6 9 6 6 6-6"/></svg>'
    "</button>"
    '<div id="workspace-menu" popover="auto" aria-label="Workspace switcher" class="workspace-menu rounded-xl border border-white/15 bg-[#0B1020] text-[#EEF2F8] p-2 shadow-2xl">'
    '<div class="flex items-center justify-between gap-2 px-3 py-2">'
    '<span data-i18n="workspaces_lbl" class="text-xs text-[#738196]">Workspaces</span>'
    '<div class="flex items-center gap-2.5">'
    '<button id="clear-areas-btn" type="button" data-i18n="clear_areas_btn" class="text-xs text-[#A0B0C8] hover:text-[#EEF2F8]">None</button>'
    '<button id="select-all-areas-btn" type="button" aria-pressed="false" data-i18n="select_all_areas" class="text-xs text-[#4BB8E8]">Select All</button>'
    "</div></div>"
    '<p id="free-chat-menu-note" hidden data-i18n="no_ws_free_hint" class="text-xs text-[#738196] px-3 pb-1.5">No workspace selected — chatting freely without vault files.</p>'
    '<nav id="knowledge-areas" aria-label="Workspaces" class="flex flex-col gap-1"></nav>'
    '<button id="new-area-btn" type="button" data-i18n="new_area_btn" class="w-full px-3 py-2 mt-2 rounded-lg border-t border-white/10 text-left text-sm text-[#4BB8E8] hover:bg-white/5">+ New Workspace</button>'
    '<button id="link-vault-btn" type="button" data-i18n-span="open_vault" class="w-full px-3 py-2 rounded-lg text-left text-sm text-[#A0B0C8] hover:text-[#EEF2F8] hover:bg-white/5 flex items-center gap-2 transition"><svg aria-hidden="true" class="w-4 h-4 shrink-0 text-[#4BB8E8]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z"/><path stroke-linecap="round" stroke-linejoin="round" d="M10 13h4m-2-2v4"/></svg><span>Link Local Folder…</span></button>'
    '<p id="selection-primary-note" hidden class="text-xs text-[#738196] px-3 py-2"></p>'
    '<p id="area-status" role="status" class="text-xs text-[#A0B0C8] px-3 py-1"></p>'
    "</div>"
    f'<button id="sidebar-cmd-btn" type="button" aria-label="Quick Search (⌘K)" title="Quick Search (⌘K)" data-i18n-aria-label="quick_search_nav" data-i18n-title="quick_search_nav" class="topbar-icon-btn shrink-0">{ICON_SEARCH}<span id="sidebar-cmd-kbd" class="visually-hidden">⌘K</span></button>'
    '<button id="mobile-drawer-close-btn" type="button" aria-label="Close sidebar" data-i18n-aria-label="aria_collapse_rail" class="topbar-icon-btn mobile-only-ctrl shrink-0">✕</button>'
    "</div>"
    '<div id="sidebar-body">'
    '<div id="mobile-rail-strip" class="mobile-rail-strip" role="group" aria-label="Sections">'
    f'<button type="button" data-rail-section="chat" class="rail-btn" aria-label="Chat &amp; Home" data-i18n-aria-label="sh_rail_chat">{ICON_HOME}</button>'
    f'<button type="button" data-rail-section="files" class="rail-btn" aria-label="Files" data-i18n-aria-label="sh_rail_files">{ICON_FOLDER_TREE}</button>'
    f'<button type="button" data-rail-section="library" class="rail-btn" aria-label="Library" data-i18n-aria-label="sh_rail_library">{ICON_LIBRARY}</button>'
    f'<button type="button" data-rail-section="graph" class="rail-btn" aria-label="Graph View" data-i18n-aria-label="sh_rail_graph">{ICON_GRAPH}</button>'
    f'<button type="button" data-rail-section="work" class="rail-btn" aria-label="Work OS" data-i18n-aria-label="sh_rail_work">{ICON_WORK}</button>'
    f'<button type="button" data-rail-section="workflows" class="rail-btn" aria-label="Workflows" data-i18n-aria-label="sh_rail_workflows">{ICON_WORKFLOWS}</button>'
    f'<button type="button" data-rail-section="studio" class="rail-btn" aria-label="Agents &amp; Formats" data-i18n-aria-label="sh_rail_studio">{ICON_AGENTS}</button>'
    "</div>"
    '<div id="drawer-panel-chat" class="drawer-panel">'
    '<span data-i18n="recent_chats" class="drawer-heading">Recent Chats</span>'
    '<div id="recent-chats-list" class="flex flex-col gap-0.5 flex-1 min-h-0 overflow-y-auto"><div data-i18n="no_recent_chats" class="px-2.5 py-1.5 text-xs text-[#738196]">No recent chats</div></div>'
    "</div>"
    '<div id="drawer-panel-files" hidden class="drawer-panel left-files-pane">'
    '<div class="ft-head">'
    '<span id="files-tree-ws-title" class="ft-ws-title">Files</span>'
    '<div class="ft-head-actions">'
    f'<button id="tree-new-note-btn" type="button" aria-label="New Note" title="New Note" data-i18n-aria-label="sh_new_note" data-i18n-title="sh_new_note" class="wb-icon-btn ft-act-btn">{ICON_PLUS}</button>'
    f'<button id="tree-expand-btn" type="button" aria-label="Expand all folders" title="Expand all folders" data-i18n-aria-label="ft_expand_all" data-i18n-title="ft_expand_all" class="wb-icon-btn ft-act-btn">{ICON_EXPAND_ALL}</button>'
    f'<button id="tree-collapse-btn" type="button" aria-label="Collapse all folders" title="Collapse all folders" data-i18n-aria-label="ft_collapse_all" data-i18n-title="ft_collapse_all" class="wb-icon-btn ft-act-btn">{ICON_COLLAPSE_ALL}</button>'
    f'<button id="tree-more-btn" type="button" popovertarget="ft-options-menu" aria-expanded="false" aria-label="Explorer options" title="Explorer options" data-i18n-aria-label="ft_opts_aria" data-i18n-title="ft_opts_aria" class="wb-icon-btn ft-act-btn">{ICON_MORE}</button>'
    "</div></div>"
    '<div id="ft-options-menu" popover="auto" class="rail-popover" aria-label="Explorer options"><div focusgroup="menu nomemory" class="bp-menu-group">'
    '<button id="ft-opt-reveal" type="button" role="menuitemcheckbox" aria-checked="true" class="shell-pop-item bp-check-item"><span data-i18n="ft_opt_reveal">Auto-reveal active file</span></button>'
    '<button id="ft-opt-newtab" type="button" role="menuitemcheckbox" aria-checked="true" class="shell-pop-item bp-check-item"><span data-i18n="ft_opt_newtab">Always open in new tab</span></button>'
    '<div class="shell-pop-sep"><button id="ft-act-reveal-now" type="button" class="shell-pop-item"><span data-i18n="ft_reveal_now">Reveal active file</span></button>'
    '<button id="tree-refresh-btn" type="button" class="shell-pop-item"><span data-i18n="ft_refresh">Refresh files</span></button></div></div></div>'
    '<div id="ft-file-menu" popover="auto" class="rail-popover" aria-label="File actions"><div focusgroup="menu nomemory" class="bp-menu-group">'
    '<button type="button" data-fm-act="open-pin" class="shell-pop-item"><span data-i18n="ft_act_open_tab">Open in new tab</span></button>'
    '<button type="button" data-fm-act="copilot" class="shell-pop-item"><span data-i18n="ft_act_copilot">Open &amp; ask Copilot</span></button>'
    '<button type="button" data-fm-act="move" data-fm-writable="1" class="shell-pop-item"><span data-i18n="ft_act_move">Move to folder…</span></button>'
    '<button type="button" data-fm-act="copy-path" class="shell-pop-item"><span data-i18n="ft_act_copy">Copy path</span></button>'
    '<button type="button" data-fm-act="anonymize" data-fm-writable="1" class="shell-pop-item"><span data-i18n="ft_act_anon">Anonymize (GDPR)</span></button>'
    '<div data-fm-writable="1" class="shell-pop-sep"><button type="button" data-fm-act="delete" class="shell-pop-item ft-pop-danger"><span data-i18n="delete_btn">Delete</span></button></div>'
    "</div></div>"
    '<nav id="workspace-files-tree" aria-label="Workspace files" class="ft-tree"></nav>'
    "</div>"
    '<div id="drawer-panel-work" hidden class="drawer-panel">'
    '<span data-i18n="work_section_lbl" class="drawer-heading">Work OS</span>'
    f'<button id="sidebar-work-btn" type="button" class="drawer-item"><span data-i18n-span="work_board_nav" class="drawer-item-lead">{ICON_WORK}<span>Board &amp; Calendar</span></span><span id="sidebar-work-badge" class="drawer-badge">0</span></button>'
    f'<button id="sidebar-focus-btn" type="button" class="drawer-item"><span data-i18n-span="focus_nav" class="drawer-item-lead">{ICON_FOCUS}<span>Focus &amp; Goals</span></span><span id="sidebar-focus-badge" class="drawer-badge">0h</span></button>'
    f'<button id="sidebar-impact-btn" type="button" class="drawer-item"><span data-i18n-span="impact_nav" class="drawer-item-lead">{ICON_IMPACT}<span>Time &amp; Impact</span></span><span id="sidebar-impact-badge" class="drawer-badge">0h</span></button>'
    "</div>"
    '<div id="drawer-panel-workflows" hidden class="drawer-panel">'
    '<div class="flex items-center justify-between pr-2"><span data-i18n="sh_saved_pipelines" class="drawer-heading">Workflows</span><span id="sidebar-workflows-badge" class="drawer-badge">0</span></div>'
    '<div id="drawer-workflows-list" class="flex flex-col gap-0.5 flex-1 min-h-0 overflow-y-auto"></div>'
    "</div>"
    '<div id="drawer-panel-studio" hidden class="drawer-panel">'
    '<span data-i18n="sh_rail_studio" class="drawer-heading">Customize</span>'
    f'<button id="sidebar-agents-btn" type="button" class="drawer-item"><span data-i18n-span="agents_nav" class="drawer-item-lead">{ICON_AGENTS}<span>Agents</span></span><span id="sidebar-agent-badge" class="drawer-badge text-[#4BB8E8]">Saga</span></button>'
    f'<button id="sidebar-formats-btn" type="button" class="drawer-item"><span data-i18n-span="formats_nav" class="drawer-item-lead">{ICON_FORMATS}<span>Answer Formats</span></span><span id="sidebar-format-badge" class="drawer-badge">Studio</span></button>'
    '<span data-i18n="sh_team_roster" class="drawer-heading" style="margin-top:0.4rem">Quick Switch Agent</span>'
    '<div id="drawer-agents-list" class="flex flex-col gap-0.5 flex-1 min-h-0 overflow-y-auto"></div>'
    "</div>"
    '<div class="mobile-drawer-footer">'
    f'<button type="button" data-shell-act="guide" class="drawer-item"><span data-i18n-span="aria_quick_guide" class="drawer-item-lead">{ICON_HELP}<span>Quick Guide</span></span></button>'
    f'<button type="button" data-shell-act="settings" class="drawer-item"><span data-i18n-span="settings" class="drawer-item-lead">{ICON_SETTINGS}<span>Settings</span></span></button>'
    "</div>"
    "</div>"
    "</aside>"
)

CENTER_LAYOUT_CONTROLS_HTML: str = (
    '<div id="wb-center-controls" aria-label="Bottom panel controls">'
    '<button id="topbar-timer-pill" type="button" hidden title="Open Time &amp; Impact">00:00</button>'
    f'<button id="layout-bottom-btn" type="button" aria-pressed="false" aria-label="Toggle bottom panel" title="Toggle bottom panel" data-i18n-aria-label="sh_toggle_bottom" data-i18n-title="sh_toggle_bottom" class="topbar-icon-btn">{ICON_BOTTOM_PANEL}</button>'
    "</div>"
)

RIGHT_LAYOUT_TOGGLE_HTML: str = (
    '<div id="wb-right-toggle-wrap" aria-label="Right sidebar control">'
    f'<button id="layout-right-btn" type="button" aria-pressed="false" aria-expanded="false" aria-controls="inspector-sidebar" aria-label="Toggle right sidebar" title="Toggle right sidebar" data-i18n-aria-label="sh_toggle_right_sb" data-i18n-title="sh_toggle_right_sb" class="topbar-icon-btn">{ICON_RIGHT_SIDEBAR}</button>'
    "</div>"
)
