"""HTML markup for Codex-inspired Multi-Tab Side Workbench, Split Menu & Accessible Resizer."""

SPLIT_ICON_SVG = '<svg aria-hidden="true" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 4v16"/></svg>'
SPLIT_FLIP_SVG = '<svg aria-hidden="true" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 12h18"/></svg>'

SPLIT_TOGGLE_BTN_HTML: str = (
    '<button id="split-toggle-btn" type="button" popovertarget="split-mode-menu" aria-expanded="false" aria-label="Split View" data-i18n-aria-label="sp_toggle_aria" title="Split View" data-i18n-title="sp_toggle_aria" class="topbar-icon-btn">'
    + SPLIT_ICON_SVG
    + "</button>"
)

SPLIT_MENU_HTML: str = r"""<div id="split-mode-menu" popover="auto" aria-label="Split View modes">
  <button type="button" data-split-preset="launcher" class="split-menu-item"><svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 4v16M16 10v4m-2-2h4"/></svg><span data-i18n="wb_launcher_open">Open in Side Workbench</span></button>
  <button type="button" data-split-preset="chat-v" class="split-menu-item"><svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 4v16"/></svg><span data-i18n="sp_chat_v">Chat | Chat (Vertical)</span></button>
  <button type="button" data-split-preset="board-h" class="split-menu-item"><svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 12h18"/></svg><span data-i18n="sp_board_h">Board ↔ Chat (Horizontal)</span></button>
  <button type="button" data-split-preset="board-v" class="split-menu-item"><svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 4v16M6 8h3M6 12h3"/></svg><span data-i18n="sp_board_v">Board | Chat (Vertical)</span></button>
  <button type="button" data-split-preset="guide-v" class="split-menu-item"><svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 4v16M15 9h3M15 13h3"/></svg><span data-i18n="sp_guide_v">Chat | Library Guide</span></button>
  <button id="split-menu-close-btn" type="button" hidden data-split-preset="close" class="split-menu-item is-danger"><span data-i18n="sp_close">Close Split View</span></button>
</div>"""

SPLIT_PANE_HTML: str = (
    r"""<div id="split-resizer" hidden role="separator" tabindex="0" aria-orientation="vertical" aria-valuemin="25" aria-valuemax="75" aria-valuenow="50" aria-label="Resize split panes" data-i18n-aria-label="sp_resize_aria"></div>
<section id="split-pane-b" hidden aria-label="Secondary split pane" data-i18n-aria-label="sp_pane_aria">
  <header class="wb-side-tabbar">
    <div id="wb-side-tablist" role="tablist" aria-label="Side workbench tabs" class="wb-side-tablist"></div>
    <div class="split-pane-group">
      <button id="wb-side-add-tab" type="button" aria-label="New tab" title="New tab" data-i18n-aria-label="wb_new_tab" data-i18n-title="wb_new_tab" class="wb-icon-btn">+</button>
      <button id="split-flip-btn" type="button" aria-label="Flip split orientation" data-i18n-aria-label="sp_flip_aria" title="Flip Horizontal / Vertical" data-i18n-title="sp_flip_aria" class="wb-icon-btn">"""
    + SPLIT_FLIP_SVG
    + r"""</button>
      <button id="split-close-btn" type="button" aria-label="Close split view" data-i18n-aria-label="sp_close" title="Close split view" data-i18n-title="sp_close" class="wb-icon-btn">✕</button>
    </div>
  </header>

  <div id="split-launcher-body" hidden class="wb-launcher-wrap">
    <input id="wb-launcher-search" type="search" aria-label="Search guides, tasks, or open a tool" data-i18n-aria-label="wb_launcher_ph" placeholder="Search guides, tasks, or open a tool..." data-i18n-placeholder="wb_launcher_ph" class="wb-input wb-launcher-search" />
    <div id="wb-launcher-results" style="width:100%;max-width:27rem;display:flex;flex-direction:column;gap:0.3rem"></div>
    <div style="width:100%;max-width:27rem">
      <div style="font-size:0.78rem;color:var(--text-subtle);margin-bottom:0.55rem" data-i18n="wb_launcher_open">Open in Side Workbench</div>
      <div class="wb-launcher-grid">
        <button type="button" data-open-side-tile="chat" class="wb-launcher-tile"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path stroke-linecap="round" stroke-linejoin="round" d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg><span data-i18n="wb_tile_chat">Side Chat</span></button>
        <button type="button" data-open-side-tile="guide" class="wb-launcher-tile"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6Zm0 6h16M10 4v16"/></svg><span data-i18n="wb_tile_guide">Library Guide</span></button>
        <button type="button" data-open-side-tile="tasks" class="wb-launcher-tile"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="4" width="18" height="16" rx="2"/><path stroke-linecap="round" d="M9 4v16M15 4v16"/></svg><span data-i18n="wb_tile_tasks">Quick Tasks</span></button>
        <button type="button" data-open-side-tile="focus" class="wb-launcher-tile"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3.5"/></svg><span data-i18n="wb_tile_focus">Focus Timer</span></button>
        <button type="button" data-open-side-tile="impact" class="wb-launcher-tile"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="13" r="8"/><path stroke-linecap="round" d="M12 9v4l2.5 2M9.5 2.5h5"/></svg><span data-i18n="wb_tile_impact">Quick Impact</span></button>
      </div>
    </div>
  </div>

  <div id="split-chat-body">
    <div class="split-pane-header">
      <div class="split-pane-group">
        <div class="split-seg" role="group" aria-label="Secondary pane mode">
          <button id="split-mode-chat-btn" type="button" data-split-b-mode="chat" aria-pressed="true" data-i18n="sp_mode_chat">Chat</button>
          <button id="split-mode-guide-btn" type="button" data-split-b-mode="guide" aria-pressed="false" data-i18n="sp_mode_guide">Guide</button>
        </div>
        <select id="split-agent-select" aria-label="Secondary pane agent" data-i18n-aria-label="sp_agent_aria" class="split-mini-select"></select>
        <select id="split-thread-select" aria-label="Secondary pane chat thread" data-i18n-aria-label="sp_thread_aria" class="split-mini-select"></select>
        <button id="split-new-chat-btn" type="button" data-i18n="sp_new_thread" class="wb-btn wb-btn-sm">+</button>
      </div>
    </div>
    <div id="split-chat-stream" tabindex="-1"></div>
    <form id="split-chat-form" class="split-chat-dock">
      <div class="split-pill">
        <label for="split-query" class="visually-hidden" data-i18n="sp_input_aria">Message secondary chat</label>
        <textarea id="split-query" rows="1" maxlength="8000" placeholder="Ask in split chat..." data-i18n-placeholder="sp_input_ph" autocomplete="off"></textarea>
        <button id="split-submit-btn" type="submit" aria-label="Send message" data-i18n-aria-label="submit_query" class="w-8 h-8 rounded-full bg-[#4BB8E8] text-[#04060F] flex items-center justify-center text-sm font-semibold shrink-0 transition">↑</button>
      </div>
    </form>
  </div>

  <div id="split-guide-body" hidden>
    <div style="padding:0.55rem 0.85rem;border-bottom:1px solid var(--border-subtle);display:flex;align-items:center;gap:0.5rem">
      <label for="split-guide-select" class="visually-hidden" data-i18n="sp_guide_select_aria">Choose a Library guide</label>
      <select id="split-guide-select" class="wb-select" style="flex:1"></select>
      <button id="split-guide-extract-btn" type="button" data-i18n="wb_extract_to_board" class="wb-btn wb-btn-sm">Extract to Board</button>
    </div>
    <div id="split-guide-scroll"></div>
  </div>

  <div id="split-tasks-body" hidden class="wb-side-subpane">
    <form id="wb-side-task-form" style="display:flex;gap:0.4rem"><input id="wb-side-task-in" type="text" maxlength="200" aria-label="Quick add task" data-i18n-aria-label="wb_quick_ph" placeholder="Add a task..." data-i18n-placeholder="wb_quick_ph" class="wb-input" style="flex:1"/><button type="submit" data-i18n="wb_add_btn" class="wb-btn wb-btn-sm wb-btn-primary">Add</button></form>
    <div id="wb-side-task-list" style="display:flex;flex-direction:column;gap:0.4rem"></div>
  </div>

  <div id="split-focus-body" hidden class="wb-side-subpane">
    <div style="display:flex;align-items:center;justify-content:space-between;gap:0.5rem"><strong data-i18n="foc_title">Focus &amp; Goals</strong><button id="wb-side-open-deep" type="button" data-i18n="foc_start_deep" class="wb-btn wb-btn-sm wb-btn-primary">Start Deep Focus</button></div>
    <div style="display:flex;flex-wrap:wrap;gap:0.35rem" role="group" aria-label="Quick soundscape">
      <button type="button" data-side-snd="off" data-i18n="foc_snd_off" class="wb-pill-btn">Silent</button>
      <button type="button" data-side-snd="brown" data-i18n="foc_snd_brown" class="wb-pill-btn">Brown Noise</button>
      <button type="button" data-side-snd="rain" data-i18n="foc_snd_rain" class="wb-pill-btn">Soft Rain</button>
      <button type="button" data-side-snd="drone" data-i18n="foc_snd_drone" class="wb-pill-btn">Warm Drone</button>
    </div>
    <div id="wb-side-focus-goals" style="display:flex;flex-direction:column;gap:0.55rem"></div>
  </div>

  <div id="split-impact-body" hidden class="wb-side-subpane">
    <div style="display:flex;align-items:center;justify-content:space-between;gap:0.5rem"><strong data-i18n="imp_title">Time &amp; Impact</strong><button id="wb-side-open-impact" type="button" data-i18n="imp_log_btn" class="wb-btn wb-btn-sm wb-btn-primary">+ Log Impact</button></div>
    <form id="wb-side-imp-form" style="display:flex;flex-direction:column;gap:0.55rem">
      <div class="wb-field"><label for="wb-si-what" data-i18n="imp_what_done">What did you do?</label><input id="wb-si-what" type="text" required maxlength="600" class="wb-input"/></div>
      <div class="wb-field"><label for="wb-si-effect" data-i18n="imp_effect">What effect or change did it create?</label><textarea id="wb-si-effect" rows="2" required maxlength="1000" class="wb-textarea"></textarea></div>
      <button type="submit" data-i18n="save" class="wb-btn wb-btn-sm wb-btn-primary">Save</button>
    </form>
    <div id="wb-side-imp-recent" style="display:flex;flex-direction:column;gap:0.45rem"></div>
  </div>
</section>"""
)