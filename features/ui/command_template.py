"""Command Palette (<dialog>), slash menu, multiline prompt, Gemini turn icons, and Reading Comfort styles."""

COMMAND_STYLES_CSS: str = r"""<style>
:root { --ui-scale: 1; --reading-font: inherit; --reading-size: calc(1rem * var(--ui-scale, 1)); --reading-width: 48rem; --reading-leading: 1.65; }
#active-stream, #chat-stream, #tutor, #results, #chunks-header, #stream-divider, #search-dock, #seed-chips { max-width: var(--reading-width) !important; }
.md-body, .md-prose, .chat-user-msg, .comfort-preview-sample { font-family: var(--reading-font); font-size: var(--reading-size); line-height: var(--reading-leading); }
.md-body p, .md-body li, .md-prose p, .md-prose li, .md-list-item { font-family: var(--reading-font); font-size: var(--reading-size); line-height: var(--reading-leading); }
html.realm-legible body, html.realm-legible .md-body, html.realm-legible .comfort-preview-sample { font-family: "Atkinson Hyperlegible", "Verdana", "DejaVu Sans", system-ui, -apple-system, sans-serif; letter-spacing: 0.015em; }
html.realm-dyslexic body, html.realm-dyslexic .md-body, html.realm-dyslexic .comfort-preview-sample { font-family: "OpenDyslexic", "Lexend", "Comic Neue", "Verdana", system-ui, sans-serif; letter-spacing: 0.035em; word-spacing: 0.12em; --reading-leading: 1.85; }
html.realm-hc-focus { --border: light-dark(rgba(11, 16, 32, 0.44), rgba(238, 242, 248, 0.44)); --border-subtle: light-dark(rgba(11, 16, 32, 0.24), rgba(238, 242, 248, 0.24)); }
html.realm-hc-focus :where(a:any-link, button, input, select, textarea, summary, [tabindex]):focus-visible { outline: 3px solid var(--accent) !important; outline-offset: 3px !important; }
html.realm-reduce-motion .ambient-stage { display: none !important; }
html.realm-reduce-motion .stream-cursor, html.realm-reduce-motion .animate-pulse, html.realm-reduce-motion .animate-spin { animation: none !important; }
html.realm-reduce-motion #sidebar, html.realm-reduce-motion #main-shell, html.realm-reduce-motion html.no-native-switch input[type="checkbox"][switch]::before, html.realm-reduce-motion .study-progress-fill { transition: none !important; }
html.realm-reduce-motion .active\:scale-95:active { transform: none !important; }
html.realm-reduce-motion ::view-transition-group(*), html.realm-reduce-motion ::view-transition-old(*), html.realm-reduce-motion ::view-transition-new(*) { animation: none !important; }
@media (prefers-reduced-motion: reduce) {
  .animate-pulse, .animate-spin, .stream-cursor { animation: none !important; }
  #sidebar, #main-shell, .study-progress-fill, html.no-native-switch input[type="checkbox"][switch]::before { transition: none !important; }
  .active\:scale-95:active { transform: none !important; }
}
.comfort-seg-3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.25rem; padding: 0.25rem; border-radius: 0.75rem; background: var(--background); border: 1px solid var(--border-subtle); }
.comfort-seg-4 { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0.25rem; padding: 0.25rem; border-radius: 0.75rem; background: var(--background); border: 1px solid var(--border-subtle); }
.comfort-two-col { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.65rem; }
@media (max-width: 540px) { .comfort-two-col { grid-template-columns: 1fr; } }
.comfort-preview-box { padding: 0.75rem 0.9rem; border-radius: 0.75rem; background: var(--background); border: 1px solid var(--border-subtle); color: var(--text-muted); }
.comfort-preview-sample { margin: 0; }
.prompt-textarea { flex: 1 1 14ch; min-inline-size: min(100%, 14ch); field-sizing: content; height: auto; resize: none; overflow-y: auto; max-block-size: 10.5rem; min-block-size: 1.75rem; padding: 0.2rem 0; margin: 0; line-height: 1.5; font-size: calc(1.05rem * var(--ui-scale, 1)); }
#prompt-container { border-radius: 1.875rem !important; }
#prompt-container.is-multiline { border-radius: 1.35rem !important; align-items: flex-end !important; padding-block: 0.75rem !important; }
#prompt-container.is-multiline .prompt-entry { align-items: flex-start; }
#prompt-container.is-multiline #recipe-chip, #prompt-container.is-multiline #scope-chip, #prompt-container.is-multiline #attached-chips { margin-top: 0.2rem; }
#recipe-chip { flex: 0 1 auto; display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.22rem 0.65rem; border-radius: 9999px; font-size: calc(0.875rem * var(--ui-scale, 1)); font-weight: 500; background: color-mix(in oklab, var(--accent) 16%, transparent); color: var(--accent); border: 1px solid color-mix(in oklab, var(--accent) 32%, transparent); }
#recipe-chip[hidden] { display: none !important; }
#attached-chips { display: inline-flex; flex-wrap: wrap; align-items: center; gap: 0.35rem; flex: 0 1 auto; max-inline-size: 100%; }
#attached-chips[hidden] { display: none !important; }
.attached-pill { display: inline-flex; align-items: center; gap: 0.35rem; max-inline-size: 14rem; padding: 0.22rem 0.6rem; border-radius: 9999px; font-size: calc(0.875rem * var(--ui-scale, 1)); font-weight: 500; background: color-mix(in oklab, var(--text) 8%, transparent); color: var(--text); border: 1px solid var(--border); }
.attached-pill-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.attached-pill-del, #recipe-reset-btn, #scope-reset-btn { flex-shrink: 0; min-inline-size: 1.5rem; min-block-size: 1.5rem; border-radius: 9999px; border: 0; background: transparent; color: var(--text-muted); cursor: pointer; display: inline-flex; align-items: center; justify-content: center; }
.attached-pill-del:hover { background: var(--hover-tint); color: var(--text); }
#cmd-palette-modal { margin: min(10vh, 5rem) auto auto; padding: 0; inline-size: min(40rem, calc(100vw - 2rem)); block-size: min(32rem, 76vh); max-block-size: 82vh; border-radius: 1rem; overflow: hidden; backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px); }
#cmd-palette-modal[open] { display: flex; flex-direction: column; }
#cmd-palette-head { display: flex; align-items: center; gap: 0.75rem; padding: 0.85rem 1rem; border-bottom: 1px solid var(--border-subtle); flex-shrink: 0; }
#cmd-palette-input { flex: 1 1 auto; min-inline-size: 0; background: transparent; border: 0; outline: none !important; box-shadow: none !important; font-size: calc(1rem * var(--ui-scale, 1)); line-height: 1.4; color: var(--text); }
#cmd-palette-input::-webkit-search-cancel-button { -webkit-appearance: none; appearance: none; }
#cmd-palette-list { flex: 1 1 auto; min-block-size: 10rem; overflow-y: auto; padding: 0.5rem; display: flex; flex-direction: column; gap: 0.125rem; }
#cmd-palette-foot { display: flex; align-items: center; justify-content: space-between; padding: 0.6rem 1rem; border-top: 1px solid var(--border-subtle); font-size: calc(0.8125rem * var(--ui-scale, 1)); color: var(--text-subtle); flex-shrink: 0; }
.cmd-item, .slash-item { display: flex; align-items: center; gap: 0.65rem; width: 100%; padding: 0.6rem 0.75rem; border-radius: 0.6rem; text-align: left; font-size: calc(0.9375rem * var(--ui-scale, 1)); color: var(--text-muted); cursor: pointer; border: 1px solid transparent; transition: background-color 0.12s ease, color 0.12s ease; }
.cmd-item:hover, .cmd-item[aria-selected="true"], .slash-item:hover, .slash-item[aria-selected="true"] { background: color-mix(in oklab, var(--accent) 14%, transparent); color: var(--text); border-color: color-mix(in oklab, var(--accent) 30%, transparent); }
.cmd-kbd { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: calc(0.8125rem * var(--ui-scale, 1)); padding: 0.15rem 0.45rem; border-radius: 0.375rem; border: 1px solid var(--border); color: var(--text-subtle); background: var(--background); }
#slash-cmd-menu { position: absolute; top: calc(100% + 0.5rem); left: 0; right: 0; z-index: 45; max-block-size: 17.5rem; overflow-y: auto; border-radius: 1rem; padding: 0.4rem; border: 1px solid var(--border); background: color-mix(in oklab, var(--surface-raised) 96%, transparent); backdrop-filter: blur(22px); -webkit-backdrop-filter: blur(22px); box-shadow: var(--dialog-shadow); }
.chat-dock #slash-cmd-menu { top: auto; bottom: calc(100% + 0.5rem); }
#slash-cmd-menu[hidden] { display: none !important; }
.turn-action-row { display: flex; align-items: center; gap: 0.25rem; flex-wrap: wrap; margin-top: 0.85rem; }
.turn-icon-btn { display: inline-flex; align-items: center; justify-content: center; gap: 0.3rem; min-inline-size: 2rem; min-block-size: 2rem; padding: 0.35rem 0.55rem; border-radius: 9999px; border: 0; background: transparent; color: var(--text-subtle); font-size: calc(0.875rem * var(--ui-scale, 1)); cursor: pointer; transition: background-color 0.14s ease, color 0.14s ease; }
.turn-icon-btn:hover { background: var(--hover-tint); color: var(--text); }
.turn-icon-btn[aria-pressed="true"] { color: var(--accent); background: color-mix(in oklab, var(--accent) 14%, transparent); }
.turn-sources-chip { display: inline-flex; align-items: center; gap: 0.35rem; margin-inline-start: 0.35rem; padding: 0.3rem 0.75rem; border-radius: 9999px; border: 1px solid var(--border-subtle); background: transparent; color: var(--text-muted); font-size: calc(0.875rem * var(--ui-scale, 1)); cursor: pointer; transition: border-color 0.14s ease, color 0.14s ease, background-color 0.14s ease; }
.turn-sources-chip:hover { border-color: var(--border); color: var(--text); background: var(--hover-tint); }
.turn-popover-panel { position: absolute; left: 0; bottom: calc(100% + 0.35rem); z-index: 45; min-inline-size: 13.5rem; border-radius: 0.85rem; background: var(--surface-raised); border: 1px solid var(--border); padding: 0.3rem; box-shadow: var(--dialog-shadow); display: flex; flex-direction: column; gap: 0.125rem; }
.header-popover-panel { position: absolute; right: 0; top: calc(100% + 0.35rem); z-index: 45; min-inline-size: 14.5rem; border-radius: 0.85rem; background: var(--surface-raised); border: 1px solid var(--border); padding: 0.3rem; box-shadow: var(--dialog-shadow); display: flex; flex-direction: column; gap: 0.125rem; }
details.turn-more-menu > summary::-webkit-details-marker { display: none; }
.turn-popover-item { display: flex; align-items: center; gap: 0.5rem; width: 100%; text-align: left; padding: 0.5rem 0.7rem; border-radius: 0.5rem; font-size: calc(0.875rem * var(--ui-scale, 1)); color: var(--text-muted); background: transparent; border: 0; cursor: pointer; white-space: nowrap; }
.turn-popover-item:hover { background: var(--hover-tint); color: var(--text); }
mark.search-hit-mark { background: color-mix(in oklab, var(--accent) 26%, transparent); color: var(--text); border-radius: 0.25rem; padding: 0 0.16rem; font-weight: 500; }
</style>"""

SLASH_MENU_HTML: str = r"""<div id="slash-cmd-menu" hidden role="listbox" aria-label="Prompt commands"></div>"""

COMMAND_PALETTE_HTML: str = r"""<dialog id="cmd-palette-modal" closedby="any" aria-labelledby="cmd-palette-title" class="bg-[#0B1020] text-[#EEF2F8] border border-white/15 shadow-2xl">
  <h2 id="cmd-palette-title" data-i18n="cmd_title" class="visually-hidden">Quick Search</h2>
  <div id="cmd-palette-head">
    <svg aria-hidden="true" class="w-4 h-4 text-[#4BB8E8] shrink-0" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path stroke-linecap="round" d="m20 20-3.5-3.5"/></svg>
    <input id="cmd-palette-input" type="search" role="combobox" aria-labelledby="cmd-palette-title" aria-expanded="false" aria-controls="cmd-palette-list" aria-autocomplete="list" autocomplete="off" spellcheck="false" autofocus data-i18n-placeholder="cmd_placeholder" placeholder="Search guides, chats, agents, workspaces, or actions…" />
    <button id="close-cmd-palette" type="button" aria-label="Close dialog" data-i18n-aria-label="aria_close_dialog" class="h-8 w-8 rounded-full text-[#738196] hover:text-[#EEF2F8] hover:bg-white/[0.06] flex items-center justify-center text-sm shrink-0 transition">✕</button>
  </div>
  <div id="cmd-palette-list" role="listbox" aria-label="Search results"></div>
  <div id="cmd-palette-foot">
    <span data-i18n="cmd_hint_keys">↑↓ navigate · ↵ select · esc close</span>
    <span id="cmd-palette-count" class="font-mono"></span>
  </div>
</dialog>"""
