"""HTML markup for Split View toggle menu, accessible resizer, and Secondary Split Pane."""

SPLIT_ICON_SVG = '<svg aria-hidden="true" class="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 4v16"/></svg>'
SPLIT_FLIP_SVG = '<svg aria-hidden="true" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 12h18"/></svg>'

SPLIT_TOGGLE_BTN_HTML: str = (
    '<button id="split-toggle-btn" type="button" popovertarget="split-mode-menu" aria-expanded="false" aria-label="Split View" data-i18n-aria-label="sp_toggle_aria" title="Split View" data-i18n-title="sp_toggle_aria">'
    + SPLIT_ICON_SVG
    + "</button>"
)

SPLIT_MENU_HTML: str = r"""<div id="split-mode-menu" popover="auto" aria-label="Split View modes">
  <button type="button" data-split-preset="chat-v" class="split-menu-item"><svg aria-hidden="true" class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 4v16"/></svg><span data-i18n="sp_chat_v">Chat | Chat (Vertical)</span></button>
  <button type="button" data-split-preset="board-h" class="split-menu-item"><svg aria-hidden="true" class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 12h18"/></svg><span data-i18n="sp_board_h">Board ↔ Chat (Horizontal)</span></button>
  <button type="button" data-split-preset="board-v" class="split-menu-item"><svg aria-hidden="true" class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 4v16M6 8h3M6 12h3"/></svg><span data-i18n="sp_board_v">Board | Chat (Vertical)</span></button>
  <button type="button" data-split-preset="guide-v" class="split-menu-item"><svg aria-hidden="true" class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 4v16M15 9h3M15 13h3"/></svg><span data-i18n="sp_guide_v">Chat | Library Guide</span></button>
  <button id="split-menu-close-btn" type="button" hidden data-split-preset="close" class="split-menu-item is-danger"><span data-i18n="sp_close">Close Split View</span></button>
</div>"""

SPLIT_PANE_HTML: str = (
    r"""<div id="split-resizer" hidden role="separator" tabindex="0" aria-orientation="vertical" aria-valuemin="25" aria-valuemax="75" aria-valuenow="50" aria-label="Resize split panes" data-i18n-aria-label="sp_resize_aria"></div>
<section id="split-pane-b" hidden aria-label="Secondary split pane" data-i18n-aria-label="sp_pane_aria">
  <header class="split-pane-header">
    <div class="split-pane-group">
      <div class="split-seg" role="group" aria-label="Secondary pane mode">
        <button id="split-mode-chat-btn" type="button" data-split-b-mode="chat" aria-pressed="true" data-i18n="sp_mode_chat">Chat</button>
        <button id="split-mode-guide-btn" type="button" data-split-b-mode="guide" aria-pressed="false" data-i18n="sp_mode_guide">Guide</button>
      </div>
      <select id="split-agent-select" aria-label="Secondary pane agent" data-i18n-aria-label="sp_agent_aria" class="split-mini-select"></select>
      <select id="split-thread-select" aria-label="Secondary pane chat thread" data-i18n-aria-label="sp_thread_aria" class="split-mini-select"></select>
      <button id="split-new-chat-btn" type="button" data-i18n="sp_new_thread" class="wb-btn wb-btn-sm">+</button>
    </div>
    <div class="split-pane-group">
      <button id="split-flip-btn" type="button" aria-label="Flip split orientation" data-i18n-aria-label="sp_flip_aria" title="Flip Horizontal / Vertical" data-i18n-title="sp_flip_aria" class="wb-icon-btn">"""
    + SPLIT_FLIP_SVG
    + r"""</button>
      <button id="split-close-btn" type="button" aria-label="Close split view" data-i18n-aria-label="sp_close" title="Close split view" data-i18n-title="sp_close" class="wb-icon-btn">✕</button>
    </div>
  </header>
  <div id="split-chat-body">
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
    <div style="padding:0.65rem 0.9rem;border-bottom:1px solid var(--border-subtle);display:flex;align-items:center;gap:0.5rem">
      <label for="split-guide-select" class="visually-hidden" data-i18n="sp_guide_select_aria">Choose a Library guide</label>
      <select id="split-guide-select" class="wb-select" style="flex:1"></select>
      <button id="split-guide-extract-btn" type="button" data-i18n="wb_extract_to_board" class="wb-btn wb-btn-sm">Extract to Board</button>
    </div>
    <div id="split-guide-scroll"></div>
  </div>
</section>"""
)
