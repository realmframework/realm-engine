"""Phase 3 modals: Multi-Agent Second Opinion / Cross-Examine and Contradiction & Gap Finder."""

WORKFLOW_STYLES_CSS: str = r"""<style>
#cross-examine-modal { inline-size: min(32rem, calc(100vw - 2rem)); max-block-size: 84vh; overflow: hidden; }
#gap-analysis-modal { inline-size: min(42rem, calc(100vw - 2rem)); max-block-size: 86vh; overflow: hidden; }
#cross-examine-modal[open], #gap-analysis-modal[open] { display: flex; flex-direction: column; }
#cx-agent-list { flex: 1 1 auto; min-block-size: 10rem; max-block-size: 22rem; overflow-y: auto; display: flex; flex-direction: column; gap: 0.5rem; padding-inline-end: 0.25rem; }
#gap-results-body { flex: 1 1 auto; min-block-size: 14rem; max-block-size: 58vh; overflow-y: auto; display: flex; flex-direction: column; gap: 1rem; padding-inline-end: 0.25rem; }
</style>"""

WORKFLOW_MODALS_HTML: str = r"""<dialog id="cross-examine-modal" closedby="any" aria-labelledby="cross-examine-title" class="m-auto rounded-2xl bg-[#0B1020] text-[#EEF2F8] border border-white/15 p-6 shadow-2xl gap-4">
  <div class="flex items-center justify-between border-b border-white/10 pb-3 shrink-0">
    <div>
      <h2 id="cross-examine-title" data-i18n="cx_title" class="text-lg font-semibold text-[#EEF2F8]">Second Opinion</h2>
      <p data-i18n="cx_sub" class="text-xs text-[#738196] mt-0.5">Invite another agent into this thread to challenge assumptions, verify facts, or inspect risks.</p>
    </div>
    <button id="close-cx-modal" type="button" aria-label="Close second opinion dialog" class="h-8 w-8 rounded-full text-[#738196] hover:text-[#EEF2F8] hover:bg-white/[0.06] flex items-center justify-center text-sm shrink-0">✕</button>
  </div>
  <div class="flex flex-col gap-1.5 shrink-0">
    <label for="cx-angle-input" data-i18n="cx_angle_lbl" class="text-xs text-[#A0B0C8]">Optional focus angle</label>
    <input id="cx-angle-input" type="text" maxlength="200" data-i18n-placeholder="cx_angle_ph" placeholder="e.g. Check numbers, spot missing edge cases, or challenge conclusions…" class="rounded-lg bg-[#04060F] border border-white/15 focus:border-[#4BB8E8] px-3 py-2 text-xs text-[#EEF2F8] outline-none" />
  </div>
  <div id="cx-agent-list"></div>
</dialog>
<dialog id="gap-analysis-modal" closedby="any" aria-labelledby="gap-analysis-title" class="m-auto rounded-2xl bg-[#0B1020] text-[#EEF2F8] border border-white/15 p-6 shadow-2xl gap-4">
  <div class="flex items-center justify-between border-b border-white/10 pb-3 shrink-0">
    <div>
      <h2 id="gap-analysis-title" data-i18n="gap_title" class="text-lg font-semibold text-[#EEF2F8]">Contradiction &amp; Knowledge-Gap Scan</h2>
      <p id="gap-summary-line" data-i18n="gap_sub" class="text-xs text-[#738196] mt-0.5">Instant local scan across your active workspace — zero external calls.</p>
    </div>
    <button id="close-gap-modal" type="button" aria-label="Close gap scan dialog" class="h-8 w-8 rounded-full text-[#738196] hover:text-[#EEF2F8] hover:bg-white/[0.06] flex items-center justify-center text-sm shrink-0">✕</button>
  </div>
  <div id="gap-results-body"></div>
</dialog>"""
