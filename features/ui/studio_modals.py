"""Native <dialog> for Output Formats & Requirements Synthesis Studio."""

STUDIO_MODAL_HTML: str = r"""<dialog id="format-studio-modal" closedby="any" aria-labelledby="format-studio-title" class="m-auto w-full max-w-3xl max-h-[88vh] overflow-hidden flex-col gap-4 rounded-2xl bg-[#0B1020] text-[#EEF2F8] border border-[rgba(238,242,248,0.16)] p-6 shadow-2xl">
  <div class="shrink-0 flex items-center justify-between gap-3 border-b border-[rgba(238,242,248,0.08)] pb-3">
    <div class="flex flex-col gap-0.5">
      <h2 id="format-studio-title" data-i18n="fmt_title" class="text-lg font-semibold text-[#EEF2F8]">Format &amp; Synthesis Studio</h2>
      <p data-i18n="fmt_sub" class="text-xs text-[#A0B0C8]">Chat freely first — then synthesize into Requirements Specs, Investigation Dossiers, or your own custom format.</p>
    </div>
    <button id="close-format-studio-modal" type="button" aria-label="Close Format Studio" class="h-8 w-8 rounded-full text-[#738196] hover:text-[#EEF2F8] hover:bg-white/[0.06] flex items-center justify-center text-sm shrink-0">✕</button>
  </div>
  <div class="shrink-0 flex items-center justify-between gap-2 flex-wrap">
    <div role="tablist" aria-label="Format Studio sections" class="inline-flex bg-[#04060F] p-1 rounded-xl border border-white/10 gap-1">
      <button id="format-tab-browse" type="button" role="tab" aria-selected="true" aria-controls="format-browse-pane" tabindex="0" data-i18n="fmt_tab_browse" class="px-3.5 py-1.5 rounded-lg text-xs font-medium bg-[#4BB8E8] text-[#04060F] transition">Blueprints</button>
      <button id="format-tab-custom" type="button" role="tab" aria-selected="false" aria-controls="custom-format-form" tabindex="-1" data-i18n="fmt_tab_custom" class="px-3.5 py-1.5 rounded-lg text-xs font-medium text-[#A0B0C8] hover:text-[#EEF2F8] transition">+ Create Custom Format</button>
    </div>
    <span id="format-pinned-indicator" class="text-xs font-mono text-[#4BB8E8]"></span>
  </div>
  <div id="format-browse-pane" role="tabpanel" aria-labelledby="format-tab-browse" class="min-h-0 flex-1 overflow-y-auto overscroll-contain flex flex-col gap-3 pr-1">
    <label class="flex flex-col gap-1">
      <span data-i18n="fmt_focus_lbl" class="text-xs text-[#A0B0C8]">Optional focus note for synthesis (e.g. "Focus on security &amp; GDPR edge cases")</span>
      <input id="format-extra-focus" type="text" maxlength="240" placeholder="Leave blank to synthesize the entire conversation &amp; attached notes" data-i18n-placeholder="fmt_focus_ph" class="w-full rounded-xl bg-[#04060F] border border-white/15 px-3 py-2 text-sm text-[#EEF2F8]" />
    </label>
    <div id="format-cards-grid" class="grid grid-cols-1 sm:grid-cols-2 gap-3 pb-2"></div>
  </div>
  <form id="custom-format-form" role="tabpanel" aria-labelledby="format-tab-custom" hidden class="min-h-0 flex-1 overflow-y-auto overscroll-contain flex flex-col gap-3 pr-1">
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <label class="flex flex-col gap-1"><span data-i18n="fmt_name" class="text-xs text-[#A0B0C8]">Format Name</span><input id="custom-fmt-name" type="text" required maxlength="80" placeholder="e.g. Stakeholder 4W Brief" class="w-full rounded-xl bg-[#04060F] border border-white/15 px-3 py-2 text-sm" /></label>
      <label class="flex flex-col gap-1"><span data-i18n="fmt_cat" class="text-xs text-[#A0B0C8]">Category</span><input id="custom-fmt-category" type="text" maxlength="32" value="Custom" placeholder="Requirements, Research, Legal..." class="w-full rounded-xl bg-[#04060F] border border-white/15 px-3 py-2 text-sm" /></label>
    </div>
    <label class="flex flex-col gap-1"><span data-i18n="fmt_desc" class="text-xs text-[#A0B0C8]">Short Description</span><input id="custom-fmt-desc" type="text" maxlength="220" placeholder="What this format is best for" class="w-full rounded-xl bg-[#04060F] border border-white/15 px-3 py-2 text-sm" /></label>
    <label class="flex flex-col gap-1"><span data-i18n="fmt_sections" class="text-xs text-[#A0B0C8]">Expected Sections (one per line or comma-separated)</span><textarea id="custom-fmt-sections" rows="4" required placeholder="When&#10;Who&#10;What&#10;How Much&#10;Open Risks" class="w-full rounded-xl bg-[#04060F] border border-white/15 px-3 py-2 text-sm text-[#EEF2F8] outline-none focus:border-[#4BB8E8]"></textarea></label>
    <label class="flex flex-col gap-1"><span data-i18n="fmt_rules" class="text-xs text-[#A0B0C8]">Style &amp; Structure Rules (optional)</span><textarea id="custom-fmt-rules" rows="2" maxlength="1200" placeholder="e.g. Use crisp bullet points, highlight unknowns as TBD, include a table for action items." class="w-full rounded-xl bg-[#04060F] border border-white/15 px-3 py-2 text-sm text-[#EEF2F8] outline-none focus:border-[#4BB8E8]"></textarea></label>
    <div class="flex items-center justify-between gap-2 pt-2">
      <span id="custom-fmt-status" role="status" class="text-xs text-[#4BB8E8]"></span>
      <button id="save-custom-fmt-btn" type="submit" data-i18n="fmt_save_btn" class="px-4 py-2 rounded-xl bg-[#4BB8E8] text-[#04060F] font-semibold text-xs hover:brightness-110 transition">Save Custom Format</button>
    </div>
  </form>
</dialog>
<button id="inspector-toggle-btn" type="button" hidden aria-expanded="false" aria-controls="inspector-sidebar" aria-label="Open Engine Inspector" data-i18n-aria-label="aria_open_inspector" title="Engine Inspector (Context, Tokens &amp; Thinking · ⌘I)" class="fixed right-4 top-4 z-40 h-9 w-9 rounded-full bg-[#0B1020] text-[#A0B0C8] hover:text-[#EEF2F8] shadow-[inset_0_0_0_1px_var(--border)] flex items-center justify-center transition-colors"><svg aria-hidden="true" class="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5M11 8v6M8 11h6"/></svg></button>
<aside id="inspector-sidebar" hidden aria-label="Engine Inspector" class="fixed right-0 top-0 h-screen w-[356px] max-w-[92vw] z-50 bg-[#0B1020] border-l border-[rgba(238,242,248,0.12)] shadow-2xl flex flex-col p-4 gap-4 overflow-y-auto overscroll-contain">
  <div class="shrink-0 flex items-center justify-between gap-2 pb-3 border-b border-[rgba(238,242,248,0.08)]">
    <div class="flex items-center gap-2 text-sm font-medium text-[#EEF2F8]"><svg aria-hidden="true" class="w-4 h-4 text-[#4BB8E8] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg><span data-i18n="insp_title">Engine Inspector</span></div>
    <button id="close-inspector-btn" type="button" aria-label="Close Engine Inspector" data-i18n-aria-label="aria_close_inspector" class="h-8 w-8 rounded-full text-[#738196] hover:text-[#EEF2F8] hover:bg-white/[0.06] flex items-center justify-center text-sm shrink-0">✕</button>
  </div>
  <div id="inspector-sidebar-body" class="flex flex-col gap-4 text-sm shrink-0 pb-10"></div>
</aside>"""
