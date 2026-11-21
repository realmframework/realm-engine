"""Active Recall Flashcard Studio modal with AI generation, custom cards, Anki export & WebKit-safe CSS."""

STUDY_STYLES_CSS: str = r"""<style>
#study-modal { inline-size: min(44rem, calc(100vw - 2rem)); max-block-size: 88vh; overflow: hidden; }
#study-modal[open] { display: flex; flex-direction: column; }
.study-toolbar { display: flex; align-items: center; gap: 0.45rem; flex-wrap: wrap; padding: 0.55rem 0.7rem; border-radius: 0.85rem; background: var(--background); border: 1px solid var(--border-subtle); flex-shrink: 0; }
.study-select { min-block-size: 2rem !important; border-radius: 0.55rem !important; background: var(--surface-raised) !important; border: 1px solid var(--border) !important; color: var(--text) !important; font-size: 0.75rem !important; padding: 0.28rem 1.8rem 0.28rem 0.6rem !important; outline: none; cursor: pointer; }
.study-gen-btn { display: inline-flex; align-items: center; gap: 0.35rem; min-block-size: 2rem; padding: 0.32rem 0.8rem; border-radius: 0.55rem; background: var(--accent); color: var(--text-on-accent); font-size: 0.75rem; font-weight: 600; border: 0; cursor: pointer; }
.study-gen-btn:disabled { opacity: 0.5; cursor: wait; }
.study-sub-btn { display: inline-flex; align-items: center; min-block-size: 2rem; padding: 0.32rem 0.65rem; border-radius: 0.55rem; border: 1px solid var(--border); background: transparent; color: var(--text-muted); font-size: 0.75rem; cursor: pointer; }
.study-sub-btn:hover { color: var(--text); border-color: var(--accent); }
.study-add-panel { display: flex; flex-direction: column; gap: 0.5rem; padding: 0.75rem; border-radius: 0.85rem; background: var(--background); border: 1px solid var(--border); flex-shrink: 0; }
.study-add-panel[hidden] { display: none !important; }
#study-card-stage { flex: 1 1 auto; min-block-size: 15.5rem; max-block-size: 54vh; overflow-y: auto; display: flex; flex-direction: column; gap: 0.85rem; padding-block: 0.25rem; }
.study-progress-track { width: 100%; height: 4px; border-radius: 9999px; background: var(--border-subtle); overflow: hidden; }
.study-progress-fill { height: 100%; background: var(--accent); transition: width 0.2s ease; }
.study-card-face { min-block-size: 13rem; padding: 1.35rem; border-radius: 1rem; background: var(--background); border: 1px solid var(--border); display: flex; flex-direction: column; justify-content: space-between; gap: 0.9rem; cursor: pointer; }
.study-card-face:hover { border-color: color-mix(in oklab, var(--accent) 55%, var(--border)); }
.study-btn-hard { padding: 0.42rem 0.85rem; border-radius: 0.6rem; font-size: 0.78rem; font-weight: 500; background: color-mix(in oklab, var(--status-warn) 14%, transparent); border: 1px solid color-mix(in oklab, var(--status-warn) 45%, transparent); color: var(--status-warn); cursor: pointer; }
.study-btn-hard:hover { background: color-mix(in oklab, var(--status-warn) 24%, transparent); }
.study-btn-good { padding: 0.42rem 0.85rem; border-radius: 0.6rem; font-size: 0.78rem; font-weight: 500; background: color-mix(in oklab, var(--accent) 16%, transparent); border: 1px solid color-mix(in oklab, var(--accent) 42%, transparent); color: var(--accent); cursor: pointer; }
.study-btn-good:hover { background: color-mix(in oklab, var(--accent) 26%, transparent); }
.study-btn-easy { padding: 0.42rem 0.85rem; border-radius: 0.6rem; font-size: 0.78rem; font-weight: 500; background: color-mix(in oklab, var(--status-ok) 14%, transparent); border: 1px solid color-mix(in oklab, var(--status-ok) 45%, transparent); color: var(--status-ok); cursor: pointer; }
.study-btn-easy:hover { background: color-mix(in oklab, var(--status-ok) 24%, transparent); }
</style>"""

STUDY_MODAL_HTML: str = r"""<dialog id="study-modal" closedby="any" aria-labelledby="study-modal-title" class="m-auto rounded-2xl bg-[#0B1020] text-[#EEF2F8] border border-white/15 p-6 shadow-2xl gap-3">
  <div class="flex items-center justify-between gap-3 border-b border-white/10 pb-3 shrink-0">
    <div class="min-w-0">
      <div class="flex items-center gap-2 flex-wrap">
        <h2 id="study-modal-title" data-i18n="study_title" class="text-lg font-semibold text-[#EEF2F8]">Active Recall &amp; Flashcards</h2>
        <span id="study-scope-pill" hidden class="px-2 py-0.5 rounded-full bg-[#4BB8E8]/15 text-[#4BB8E8] border border-[#4BB8E8]/35 text-[11px] font-mono truncate max-w-[14rem]"></span>
      </div>
      <p id="study-meta-line" class="text-xs text-[#738196] mt-0.5"></p>
    </div>
    <div class="flex items-center gap-2 shrink-0">
      <button id="study-socratic-btn" type="button" data-i18n="study_socratic_btn" class="px-3 py-1.5 rounded-xl bg-[#4BB8E8]/15 border border-[#4BB8E8]/40 text-xs font-medium text-[#4BB8E8] hover:bg-[#4BB8E8]/25 transition">Socratic Quiz</button>
      <button id="close-study-modal" type="button" aria-label="Close study dialog" class="h-8 w-8 rounded-full text-[#738196] hover:text-[#EEF2F8] hover:bg-white/[0.06] flex items-center justify-center text-sm shrink-0">✕</button>
    </div>
  </div>
  <div class="study-toolbar">
    <select id="study-count-select" aria-label="Number of flashcards" class="study-select">
      <option value="5" data-i18n="study_cards_5">5 cards</option>
      <option value="10" selected data-i18n="study_cards_10">10 cards</option>
      <option value="15" data-i18n="study_cards_15">15 cards</option>
    </select>
    <select id="study-style-select" aria-label="Flashcard style" class="study-select">
      <option value="concepts" data-i18n="study_style_concepts">Key Concepts</option>
      <option value="exam" data-i18n="study_style_exam">Exam Q&amp;A</option>
      <option value="applied" data-i18n="study_style_applied">Applied Scenarios</option>
    </select>
    <button id="study-generate-btn" type="button" data-i18n="study_gen_ai" class="study-gen-btn">✦ Generate AI Cards</button>
    <button id="study-add-toggle-btn" type="button" data-i18n="study_add_card" class="study-sub-btn ml-auto">+ Add Card</button>
    <button id="study-export-anki-btn" type="button" data-i18n="study_export_anki" class="study-sub-btn">↓ Anki</button>
  </div>
  <form id="study-add-form" hidden class="study-add-panel">
    <label for="study-new-front" data-i18n="study_question_lbl" class="visually-hidden">Prompt</label>
    <input id="study-new-front" type="text" maxlength="260" required data-i18n-placeholder="study_new_q_ph" placeholder="Question or prompt…" class="w-full rounded-lg bg-[#0B1020] border border-white/15 px-3 py-1.5 text-xs text-[#EEF2F8] outline-none focus:border-[#4BB8E8]" />
    <label for="study-new-back" data-i18n="study_answer_lbl" class="visually-hidden">Answer</label>
    <textarea id="study-new-back" rows="2" maxlength="800" required data-i18n-placeholder="study_new_a_ph" placeholder="Concise answer…" class="w-full rounded-lg bg-[#0B1020] border border-white/15 px-3 py-1.5 text-xs text-[#EEF2F8] outline-none focus:border-[#4BB8E8]"></textarea>
    <div class="flex items-center justify-end gap-2">
      <button id="study-add-cancel-btn" type="button" data-i18n="cancel" class="study-sub-btn">Cancel</button>
      <button type="submit" data-i18n="study_save_card" class="study-gen-btn">Save Card</button>
    </div>
  </form>
  <p id="study-status-msg" role="status" class="text-xs text-[#4BB8E8]" style="margin:0"></p>
  <div id="study-card-stage"></div>
  <div id="study-controls-bar" class="flex items-center justify-between gap-2 pt-3 border-t border-white/10 flex-wrap shrink-0">
    <span data-i18n="study_kbd_hint" class="text-[11px] font-mono text-[#738196]">Space: flip · 1 Hard · 2 Good · 3 Easy</span>
    <div id="study-rate-btns" class="flex items-center gap-2"></div>
  </div>
</dialog>"""
