"""Codex-inspired Two-Tier Shell: 52px Activity Rail, Context-Sensitive Drawer & Calm 44px Top Bar."""

from features.ui.split_template import SPLIT_TOGGLE_BTN_HTML

ACTIVITY_RAIL_HTML: str = r"""<nav aria-label="Primary" id="activity-rail">
  <button id="rail-drawer-toggle" type="button" class="rail-btn" aria-expanded="true" aria-controls="sidebar" aria-label="Toggle sidebar panel" title="Toggle sidebar panel" data-i18n-aria-label="sh_toggle_drawer" data-i18n-title="sh_toggle_drawer"><svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/></svg></button>
  <span class="rail-divider" aria-hidden="true"></span>
  <button id="rail-home-btn" type="button" data-rail-section="chat" aria-current="page" class="rail-btn" aria-label="Chat &amp; Home" title="Chat &amp; Home" data-i18n-aria-label="sh_rail_chat" data-i18n-title="sh_rail_chat"><svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5.5v-6h-5v6H4a1 1 0 0 1-1-1v-9.5Z"/></svg></button>
  <button id="rail-library-btn" type="button" data-rail-section="library" class="rail-btn" aria-label="Library &amp; Space" title="Library &amp; Space" data-i18n-aria-label="sh_rail_library" data-i18n-title="sh_rail_library"><svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6Zm0 6h16M10 4v16"/></svg></button>
  <button id="rail-work-btn" type="button" data-rail-section="work" class="rail-btn" aria-label="Work OS: Board, Focus &amp; Impact" title="Work OS: Board, Focus &amp; Impact" data-i18n-aria-label="sh_rail_work" data-i18n-title="sh_rail_work"><svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="4" width="18" height="16" rx="2"/><path stroke-linecap="round" d="M9 4v16M15 4v16M3 10h6M9 14h6"/></svg><span id="rail-work-dot" hidden class="rail-badge-dot" aria-hidden="true"></span></button>
  <button id="rail-workflows-btn" type="button" data-rail-section="workflows" class="rail-btn" aria-label="Workflows &amp; Schedules" title="Workflows &amp; Schedules" data-i18n-aria-label="sh_rail_workflows" data-i18n-title="sh_rail_workflows"><svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="4" width="6" height="5" rx="1.2"/><rect x="15" y="4" width="6" height="5" rx="1.2"/><rect x="15" y="15" width="6" height="5" rx="1.2"/><path stroke-linecap="round" stroke-linejoin="round" d="M9 6.5h6M12 6.5v11h3"/></svg></button>
  <button id="rail-studio-btn" type="button" data-rail-section="studio" class="rail-btn" aria-label="Agents &amp; Answer Formats" title="Agents &amp; Answer Formats" data-i18n-aria-label="sh_rail_studio" data-i18n-title="sh_rail_studio"><svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M16 11a4 4 0 1 0-8 0 4 4 0 0 0 8 0Zm-11 9a7 7 0 0 1 14 0"/></svg></button>
  <button id="rail-more-btn" type="button" popovertarget="rail-more-menu" aria-expanded="false" class="rail-btn" aria-label="More tools" title="More tools" data-i18n-aria-label="sh_rail_more" data-i18n-title="sh_rail_more"><svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><circle cx="6" cy="12" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="18" cy="12" r="1.5"/></svg></button>
  <div id="rail-more-menu" popover="auto" class="rail-popover" aria-label="More tools">
    <button type="button" data-shell-act="graph" class="shell-pop-item"><span data-i18n="graph_view">Graph View</span><span class="drawer-badge">2D</span></button>
    <button type="button" data-shell-act="study" class="shell-pop-item"><span data-i18n="study_title">Study Cards</span></button>
    <button type="button" data-shell-act="gaps" class="shell-pop-item"><span data-i18n="gap_title">Knowledge Gap Scan</span></button>
    <button type="button" data-shell-act="briefing" class="shell-pop-item"><span data-i18n="br_title">Executive Briefing</span></button>
    <button type="button" data-shell-act="link-folder" class="shell-pop-item"><span data-i18n="open_vault">Link Local Folder…</span></button>
  </div>
  <span class="rail-spacer" aria-hidden="true"></span>
  <button id="rail-status-btn" type="button" popovertarget="rail-status-popover" aria-expanded="false" class="rail-btn" aria-label="Engine &amp; Privacy status" title="Engine &amp; Privacy status" data-i18n-aria-label="sh_status_aria" data-i18n-title="sh_status_aria"><span id="system-status-pill" role="status" aria-label="Engine ready" title="Engine ready" class="text-xs font-mono text-[#38D399]">●</span></button>
  <div id="rail-status-popover" popover="auto" class="rail-popover" aria-label="Workspace status">
    <div style="font-size:0.78rem;color:var(--text-subtle);margin-bottom:0.45rem;font-family:ui-monospace,monospace" data-i18n="sh_status_head">LOCAL WORKSPACE STATUS</div>
    <div class="shell-pop-row"><span data-i18n="sh_st_privacy">Privacy</span><strong id="sh-pop-privacy">Local Only</strong></div>
    <div class="shell-pop-row"><span data-i18n="sh_st_agent">Active Agent</span><strong id="sh-pop-agent">Saga</strong></div>
    <div class="shell-pop-row"><span data-i18n="sh_st_timer">Work Timer</span><strong id="sh-pop-timer">00:00</strong></div>
    <button type="button" data-shell-act="settings" class="shell-pop-item" style="margin-top:0.45rem;border-top:1px solid var(--border-subtle);padding-top:0.55rem"><span data-i18n="sh_manage_settings">Manage Settings</span><span>→</span></button>
  </div>
  <button id="open-guide-btn" type="button" class="rail-btn" title="Quick Guide" aria-label="Quick Guide" data-i18n-title="aria_quick_guide" data-i18n-aria-label="aria_quick_guide"><svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="9"/><path stroke-linecap="round" stroke-linejoin="round" d="M9.5 9.5a2.5 2.5 0 0 1 5 .7c0 1.6-2.5 2-2.5 3.3m0 3h.01"/></svg></button>
  <button id="open-settings-btn" type="button" class="rail-btn" title="Settings" aria-label="Settings" data-i18n-title="settings" data-i18n-aria-label="settings"><svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 0 0-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 0 0-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 0 0-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 0 0-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 0 0 1.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065Z"/><circle cx="12" cy="12" r="3"/></svg></button>
</nav>"""

SIDEBAR_HTML: str = r"""<aside id="sidebar" aria-label="Workspace sidebar" data-i18n-aria-label="aria_sidebar" class="fixed left-[52px] top-0 h-screen w-[248px] bg-[#0B1020] z-50 flex flex-col p-3 transition-transform duration-200">
  <div class="flex items-center gap-1 mb-2.5 pb-2 border-b border-white/10">
    <button id="workspace-switcher-btn" popovertarget="workspace-menu" aria-expanded="false" aria-controls="workspace-menu" type="button" aria-label="Switch workspace" data-i18n-aria-label="aria_switch_ws" class="flex-1 min-w-0 flex items-center gap-2 px-2 py-1.5 rounded-lg text-left hover:bg-white/5">
      <span id="workspace-color-dot" aria-hidden="true" class="flex items-center gap-1 shrink-0"></span><span id="brand-title" class="text-sm font-semibold truncate">Workspaces</span>
      <svg aria-hidden="true" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" class="ml-auto shrink-0"><path d="m6 9 6 6 6-6"/></svg>
    </button>
    <div id="workspace-menu" popover="auto" aria-label="Workspace switcher" class="workspace-menu rounded-xl border border-white/15 bg-[#0B1020] text-[#EEF2F8] p-2 shadow-2xl">
      <button id="free-chat-mode-btn" type="button" aria-pressed="false" class="w-full px-3 py-2 mb-1.5 rounded-lg bg-[#04060F] border border-white/10 hover:border-[#4BB8E8] text-left text-xs font-medium text-[#EEF2F8] flex items-center justify-between gap-2 transition"><span class="flex items-center gap-2 min-w-0"><svg aria-hidden="true" class="w-3.5 h-3.5 text-[#4BB8E8] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3v3m0 12v3M3 12h3m12 0h3m-3.6-6.4L15 8m-6 8-2.4 2.4m0-12.8L9 8m6 8 2.4 2.4"/></svg><span data-i18n="free_chat" class="truncate">Free Chat (No Workspace)</span></span><span id="free-chat-pill" class="text-2xs font-mono text-[#738196] shrink-0">OFF</span></button>
      <div class="flex items-center justify-between px-3 py-2"><span data-i18n="workspaces_lbl" class="text-xs text-[#738196]">Workspaces</span><button id="select-all-areas-btn" type="button" aria-pressed="false" data-i18n="select_all_areas" class="text-xs text-[#4BB8E8]">Select All Workspaces</button></div><nav id="knowledge-areas" aria-label="Workspaces" class="flex flex-col gap-1"></nav>
      <button id="new-area-btn" type="button" data-i18n="new_area_btn" class="w-full px-3 py-2 mt-2 rounded-lg border-t border-white/10 text-left text-sm text-[#4BB8E8] hover:bg-white/5">+ New Workspace</button>
      <button id="link-vault-btn" type="button" data-i18n-span="open_vault" class="w-full px-3 py-2 rounded-lg text-left text-sm text-[#A0B0C8] hover:text-[#EEF2F8] hover:bg-white/5 flex items-center gap-2 transition"><svg aria-hidden="true" class="w-4 h-4 shrink-0 text-[#4BB8E8]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z"/><path stroke-linecap="round" stroke-linejoin="round" d="M10 13h4m-2-2v4"/></svg><span>Link Local Folder…</span></button>
      <p id="selection-primary-note" hidden class="text-xs text-[#738196] px-3 py-2"></p>
      <p id="area-status" role="status" class="text-xs text-[#A0B0C8] px-3 py-1"></p>
    </div>
    <button id="sidebar-cmd-btn" type="button" aria-label="Quick Search (⌘K)" title="Quick Search (⌘K)" data-i18n-aria-label="quick_search_nav" data-i18n-title="quick_search_nav" class="topbar-icon-btn shrink-0"><svg aria-hidden="true" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path stroke-linecap="round" d="m20 20-3.5-3.5"/></svg><span id="sidebar-cmd-kbd" class="visually-hidden">⌘K</span></button>
    <button id="sidebar-collapse-btn" type="button" aria-label="Collapse sidebar" data-i18n-aria-label="aria_collapse_rail" class="topbar-icon-btn shrink-0"><svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="m15 18-6-6 6-6"/></svg></button>
  </div>

  <div id="drawer-panel-chat" class="drawer-panel">
    <button id="new-chat-btn" type="button" data-i18n="new_chat" class="drawer-primary-btn">+ New Chat</button>
    <span data-i18n="recent_chats" class="drawer-heading">Recent Chats</span>
    <div id="recent-chats-list" class="flex flex-col gap-0.5 flex-1 min-h-0 overflow-y-auto"><div data-i18n="no_recent_chats" class="px-2.5 py-1.5 text-xs text-[#738196]">No recent chats</div></div>
  </div>

  <div id="drawer-panel-library" hidden class="drawer-panel">
    <span data-i18n="sh_rail_library" class="drawer-heading">Library &amp; Space</span>
    <button id="sidebar-browse-btn" type="button" class="drawer-item"><span data-i18n-span="library" class="drawer-item-lead"><svg aria-hidden="true" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6Zm0 6h16M10 4v16"/></svg><span>Library</span></span><span id="sidebar-guide-count" class="drawer-badge">0</span></button>
    <button id="sidebar-graph-btn" type="button" class="drawer-item"><span data-i18n-span="graph_view" class="drawer-item-lead"><svg aria-hidden="true" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="12" cy="18" r="2.5"/><path stroke-linecap="round" d="M8.2 7.2 10.8 16m5-8.8L13.2 16M8.5 6h7"/></svg><span>Graph View</span></span><span class="drawer-badge">2D</span></button>
    <button type="button" data-shell-act="new-note" class="drawer-item"><span data-i18n-span="lib_new_note" class="drawer-item-lead"><svg aria-hidden="true" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 5v14M5 12h14"/></svg><span>+ New Note</span></span><span class="drawer-badge">.md</span></button>
    <button type="button" data-shell-act="upload" class="drawer-item"><span data-i18n-span="up_title" class="drawer-item-lead"><svg aria-hidden="true" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 16V4m0 0-4 4m4-4 4 4M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/></svg><span>Add Documents</span></span></button>
    <button type="button" data-shell-act="study" class="drawer-item"><span data-i18n-span="study_title" class="drawer-item-lead"><svg aria-hidden="true" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><rect x="4" y="5" width="16" height="14" rx="2"/><path stroke-linecap="round" d="M8 10h8M8 14h5"/></svg><span>Study Cards</span></span></button>
  </div>

  <div id="drawer-panel-work" hidden class="drawer-panel">
    <span data-i18n="work_section_lbl" class="drawer-heading">Work OS</span>
    <button id="sidebar-work-btn" type="button" class="drawer-item"><span data-i18n-span="work_board_nav" class="drawer-item-lead"><svg aria-hidden="true" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2"/><path stroke-linecap="round" d="M9 4v16M15 4v16M3 10h6M9 14h6"/></svg><span>Board &amp; Calendar</span></span><span id="sidebar-work-badge" class="drawer-badge">0</span></button>
    <div style="display:flex;flex-direction:column;gap:0.15rem;padding-inline-start:1rem">
      <button type="button" data-work-jump="kanban" class="drawer-item" style="padding-block:0.35rem;font-size:0.82rem"><span data-i18n="wb_tab_kanban">Kanban</span></button>
      <button type="button" data-work-jump="tasks" class="drawer-item" style="padding-block:0.35rem;font-size:0.82rem"><span data-i18n="wb_tab_tasks">Tasks</span></button>
      <button type="button" data-work-jump="calendar" class="drawer-item" style="padding-block:0.35rem;font-size:0.82rem"><span data-i18n="wb_tab_calendar">Calendar</span></button>
      <button type="button" data-work-jump="projects" class="drawer-item" style="padding-block:0.35rem;font-size:0.82rem"><span data-i18n="wb_tab_projects">Projects</span></button>
    </div>
    <span class="drawer-heading" style="margin-top:0.35rem" data-i18n="sh_focus_impact_grp">Focus &amp; Outcomes</span>
    <button id="sidebar-focus-btn" type="button" class="drawer-item"><span data-i18n-span="focus_nav" class="drawer-item-lead"><svg aria-hidden="true" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3.5"/></svg><span>Focus &amp; Goals</span></span><span id="sidebar-focus-badge" class="drawer-badge">0h</span></button>
    <button id="sidebar-impact-btn" type="button" class="drawer-item"><span data-i18n-span="impact_nav" class="drawer-item-lead"><svg aria-hidden="true" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><circle cx="12" cy="13" r="8"/><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4l2.5 2M9.5 2.5h5"/></svg><span>Time &amp; Impact</span></span><span id="sidebar-impact-badge" class="drawer-badge">0h</span></button>
  </div>

  <div id="drawer-panel-workflows" hidden class="drawer-panel">
    <button id="sidebar-workflows-btn" type="button" class="drawer-item is-active" style="margin-bottom:0.2rem"><span data-i18n-span="workflows_nav" class="drawer-item-lead"><svg aria-hidden="true" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><rect x="3" y="4" width="6" height="5" rx="1.2"/><rect x="15" y="4" width="6" height="5" rx="1.2"/><rect x="15" y="15" width="6" height="5" rx="1.2"/><path stroke-linecap="round" stroke-linejoin="round" d="M9 6.5h6M12 6.5v11h3"/></svg><span>Workflows</span></span><span id="sidebar-workflows-badge" class="drawer-badge">0</span></button>
    <button type="button" data-shell-act="wf-new" class="drawer-primary-btn" data-i18n="wf_new_btn">+ New Pipeline</button>
    <button type="button" data-shell-act="wf-templates" class="drawer-item"><span data-i18n="wf_browse_templates">Browse 4 Starter Templates</span></button>
    <span data-i18n="sh_saved_pipelines" class="drawer-heading">Pipelines</span>
    <div id="drawer-workflows-list" class="flex flex-col gap-0.5 flex-1 min-h-0 overflow-y-auto"></div>
  </div>

  <div id="drawer-panel-studio" hidden class="drawer-panel">
    <span data-i18n="sh_rail_studio" class="drawer-heading">Customize</span>
    <button id="sidebar-agents-btn" type="button" class="drawer-item"><span data-i18n-span="agents_nav" class="drawer-item-lead"><svg aria-hidden="true" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M16 11a4 4 0 1 0-8 0 4 4 0 0 0 8 0Zm-11 9a7 7 0 0 1 14 0"/></svg><span>Agents</span></span><span id="sidebar-agent-badge" class="drawer-badge text-[#4BB8E8]">Saga</span></button>
    <button id="sidebar-formats-btn" type="button" class="drawer-item"><span data-i18n-span="formats_nav" class="drawer-item-lead"><svg aria-hidden="true" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2M9 5h6M9 12h6m-6 4h4"/></svg><span>Answer Formats</span></span><span id="sidebar-format-badge" class="drawer-badge">Studio</span></button>
    <span data-i18n="sh_team_roster" class="drawer-heading" style="margin-top:0.4rem">Quick Switch Agent</span>
    <div id="drawer-agents-list" class="flex flex-col gap-0.5 flex-1 min-h-0 overflow-y-auto"></div>
  </div>
</aside>"""

APP_TOPBAR_HTML: str = (
    r"""<header id="app-topbar" aria-label="Workspace bar">
  <div class="topbar-left">
    <button id="sidebar-open-btn" aria-label="Expand sidebar" data-i18n-aria-label="aria_expand_rail" type="button" class="hidden topbar-icon-btn"><svg aria-hidden="true" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/></svg></button>
    <span id="topbar-title">REALM Engine</span>
    <button id="topbar-timer-pill" type="button" hidden title="Open Time &amp; Impact">00:00</button>
  </div>
  <div id="top-right-tools" class="topbar-right">
    <button id="topbar-more-btn" type="button" popovertarget="topbar-more-menu" aria-expanded="false" aria-label="Workspace actions" title="Workspace actions" data-i18n-aria-label="sh_actions_aria" data-i18n-title="sh_actions_aria" class="topbar-icon-btn"><svg aria-hidden="true" width="17" height="17" viewBox="0 0 24 24" fill="currentColor"><circle cx="6" cy="12" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="18" cy="12" r="1.4"/></svg></button>
    <div id="topbar-more-menu" popover="auto" class="rail-popover" aria-label="Quick actions">
      <button type="button" data-shell-act="new-chat" class="shell-pop-item"><span data-i18n="new_chat">+ New Chat</span></button>
      <button type="button" data-shell-act="deep-focus" class="shell-pop-item"><span data-i18n="foc_start_deep">Start Deep Focus</span></button>
      <button type="button" data-shell-act="log-impact" class="shell-pop-item"><span data-i18n="imp_log_btn">+ Log Impact</span></button>
      <button type="button" data-shell-act="open-kanban" class="shell-pop-item"><span data-i18n="work_board_nav">Board &amp; Calendar</span></button>
      <button type="button" data-shell-act="settings" data-i18n-span="settings" class="shell-pop-item" style="border-top:1px solid var(--border-subtle);margin-top:0.25rem;padding-top:0.5rem"><span>Settings</span></button>
    </div>
    <button id="inspector-toggle-btn" type="button" hidden aria-expanded="false" aria-controls="inspector-sidebar" aria-label="Open Engine Inspector" data-i18n-aria-label="aria_open_inspector" title="Engine Inspector" class="topbar-icon-btn"><svg aria-hidden="true" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5M11 8v6M8 11h6"/></svg></button>"""
    + SPLIT_TOGGLE_BTN_HTML
    + r"""
  </div>
</header>"""
)