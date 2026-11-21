"""Save-as-Guide modal dialog and floating Highlight-to-Ask Reader selection pill."""

EDITOR_STYLES_CSS: str = r"""<style>
#save-guide-modal { inline-size: min(42rem, calc(100vw - 2rem)); max-block-size: 88vh; overflow: hidden; }
#save-guide-modal[open] { display: flex; flex-direction: column; }
#save-guide-form { flex: 1 1 auto; min-block-size: 16rem; max-block-size: 68vh; overflow-y: auto; display: flex; flex-direction: column; gap: 0.75rem; padding-inline-end: 0.25rem; }
.sg-meta-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.65rem; }
@media (max-width: 600px) { .sg-meta-grid { grid-template-columns: 1fr; } }
#sg-content-input { min-block-size: 13rem; }
#guide-md-textarea { min-block-size: 22rem; }
#reader-selection-pill { position: fixed; z-index: 60; display: flex; align-items: center; gap: 0.25rem; padding: 0.3rem; border-radius: 9999px; border: 1px solid var(--border); background: color-mix(in oklab, var(--surface-raised) 96%, transparent); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); box-shadow: var(--dialog-shadow); }
#reader-selection-pill[hidden] { display: none !important; }
#reader-selection-pill button { padding: 0.38rem 0.8rem; border-radius: 9999px; font-size: calc(0.875rem * var(--ui-scale, 1)); font-weight: 500; color: var(--text-muted); white-space: nowrap; transition: background-color 0.14s ease, color 0.14s ease; }
#reader-selection-pill button:hover { background: color-mix(in oklab, var(--accent) 16%, transparent); color: var(--text); }
#reader-selection-pill button.sel-primary { background: color-mix(in oklab, var(--accent) 16%, transparent); color: var(--accent); }
#reader-selection-pill button.sel-primary:hover { background: var(--accent); color: var(--text-on-accent); }
.md-editor-area { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; line-height: 1.65; tab-size: 2; resize: vertical; }
</style>"""

EDITOR_MODALS_HTML: str = r"""<dialog id="save-guide-modal" closedby="any" aria-labelledby="save-guide-title" class="m-auto rounded-2xl bg-[#0B1020] text-[#EEF2F8] border border-white/15 p-6 shadow-2xl gap-4">
  <div class="flex items-center justify-between border-b border-white/10 pb-3 shrink-0">
    <h2 id="save-guide-title" data-i18n="sg_modal_title" class="text-lg font-semibold text-[#EEF2F8]">Save as Library Guide</h2>
    <button id="close-save-guide-btn" type="button" aria-label="Close save guide dialog" class="h-8 w-8 rounded-full text-[#738196] hover:text-[#EEF2F8] hover:bg-white/[0.06] flex items-center justify-center text-sm shrink-0">✕</button>
  </div>
  <form id="save-guide-form">
    <div class="flex flex-col gap-1">
      <label for="sg-title-input" data-i18n="sg_title_lbl" class="text-xs text-[#A0B0C8]">Guide Title</label>
      <input id="sg-title-input" name="title" type="text" required maxlength="160" autofocus class="rounded-lg bg-[#04060F] border border-white/15 focus:border-[#4BB8E8] px-3 py-2 text-sm text-[#EEF2F8] outline-none" />
    </div>
    <div class="sg-meta-grid">
      <div class="flex flex-col gap-1">
        <label for="sg-area-select" data-i18n="up_save_area" class="text-xs text-[#A0B0C8]">Save to area:</label>
        <select id="sg-area-select" name="area" class="rounded-lg bg-[#04060F] border border-white/15 px-3 py-2 text-xs text-[#EEF2F8] outline-none"></select>
      </div>
      <div class="flex flex-col gap-1">
        <label for="sg-subfolder-input" data-i18n="up_save_sub" class="text-xs text-[#A0B0C8]">Save in subfolder</label>
        <input id="sg-subfolder-input" name="subfolder" type="text" maxlength="120" data-i18n-placeholder="sg_sub_ph" placeholder="Optional (e.g. notes/research)" class="rounded-lg bg-[#04060F] border border-white/15 px-3 py-2 text-xs text-[#EEF2F8] outline-none" />
      </div>
      <div class="flex flex-col gap-1">
        <label for="sg-tags-input" data-i18n="sg_tags_lbl" class="text-xs text-[#A0B0C8]">Tags (comma-separated)</label>
        <input id="sg-tags-input" name="tags" type="text" maxlength="160" placeholder="synthesis, research" class="rounded-lg bg-[#04060F] border border-white/15 px-3 py-2 text-xs text-[#EEF2F8] outline-none" />
      </div>
    </div>
    <div class="flex flex-col gap-1">
      <label for="sg-content-input" data-i18n="sg_content_lbl" class="text-xs text-[#A0B0C8]">Markdown Content</label>
      <textarea id="sg-content-input" name="content" required rows="10" class="md-editor-area rounded-xl bg-[#04060F] border border-white/15 focus:border-[#4BB8E8] p-3 text-xs text-[#EEF2F8] outline-none"></textarea>
    </div>
    <p id="sg-status" role="status" class="text-xs text-[#A0B0C8]"></p>
    <div class="flex justify-end gap-2.5 pt-1">
      <button id="cancel-save-guide-btn" type="button" data-i18n="cancel" class="rounded-xl border border-white/15 px-4 py-2 text-xs text-[#A0B0C8] hover:text-[#EEF2F8]">Cancel</button>
      <button id="submit-save-guide-btn" type="submit" data-i18n="sg_save_btn" class="rounded-xl bg-[#4BB8E8] text-[#04060F] px-4 py-2 text-xs font-semibold hover:brightness-110 transition">Save &amp; Index Guide</button>
    </div>
  </form>
</dialog>
<div id="reader-selection-pill" hidden role="toolbar" aria-label="Selected passage actions">
  <button id="sel-explain-btn" type="button" class="sel-primary" data-i18n="sel_explain">Explain simply</button>
  <button id="sel-ask-agent-btn" type="button" data-i18n="sel_ask_agent">Ask Agent</button>
  <button id="sel-quote-btn" type="button" data-i18n="sel_quote">Quote in chat</button>
</div>"""
