"""Calm, human-readable 3-tab Quick Guide modal (discoverable via ? icon, /help, or Settings)."""

GUIDE_STYLES_CSS: str = r"""<style>
#guide-modal { inline-size: min(44rem, calc(100vw - 2rem)); max-block-size: 86vh; overflow: hidden; }
#guide-modal[open] { display: flex; flex-direction: column; }
#guide-modal-body { flex: 1 1 auto; min-block-size: 14rem; max-block-size: 56vh; overflow-y: auto; display: flex; flex-direction: column; gap: 0.9rem; padding-inline-end: 0.25rem; padding-block-start: 0.5rem; }
.guide-stack { display: flex; flex-direction: column; gap: 0.85rem; }
.guide-card { border-radius: 0.95rem; background: var(--background); border: 1px solid var(--border-subtle); padding: 1rem 1.15rem; display: flex; flex-direction: column; gap: 0.55rem; }
.guide-card-title { font-size: calc(1rem * var(--ui-scale, 1)); font-weight: 600; color: var(--text); }
.guide-row { display: flex; align-items: baseline; justify-content: flex-start; gap: 1rem; font-size: calc(0.9375rem * var(--ui-scale, 1)); color: var(--text-muted); line-height: 1.55; }
.guide-kbd { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: calc(0.875rem * var(--ui-scale, 1)); padding: 0.15rem 0.55rem; min-inline-size: 7.75rem; text-align: center; border-radius: 0.4rem; border: 1px solid var(--border); background: var(--surface-raised); color: var(--accent); white-space: nowrap; flex-shrink: 0; }
.guide-note { font-size: calc(0.9375rem * var(--ui-scale, 1)); color: var(--text-muted); line-height: 1.6; margin: 0; }
.guide-footer { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; flex-wrap: wrap; border-top: 1px solid var(--border-subtle); padding-block-start: 0.85rem; }
.guide-jump-btn { padding: 0.45rem 0.85rem; border-radius: 0.7rem; border: 1px solid var(--border); background: var(--background); color: var(--text-muted); font-size: calc(0.875rem * var(--ui-scale, 1)); cursor: pointer; transition: border-color 140ms ease, color 140ms ease; }
.guide-jump-btn:hover { border-color: var(--accent); color: var(--text); }
</style>"""

GUIDE_MODAL_HTML: str = r"""<dialog id="guide-modal" closedby="any" aria-labelledby="guide-modal-title" class="m-auto rounded-2xl bg-[#0B1020] text-[#EEF2F8] border border-white/15 p-6 shadow-2xl gap-3">
  <div class="flex items-center justify-between gap-3 shrink-0">
    <div>
      <h2 id="guide-modal-title" data-i18n="guide_title" class="text-lg font-semibold text-[#EEF2F8]">Quick Guide</h2>
      <p data-i18n="guide_sub" class="text-sm text-[#A0B0C8] mt-0.5">A simple overview of what you can do in Chat, Library, and Privacy.</p>
    </div>
    <button id="close-guide-modal" type="button" aria-label="Close guide" data-i18n-aria-label="aria_close_dialog" class="h-8 w-8 rounded-full text-[#738196] hover:text-[#EEF2F8] hover:bg-white/[0.06] flex items-center justify-center text-sm shrink-0">✕</button>
  </div>
  <div id="guide-tabs" role="tablist" aria-label="Guide sections" class="settings-tabs shrink-0">
    <button id="guide-tab-chat" type="button" role="tab" aria-selected="true" aria-controls="guide-panel-chat" tabindex="0" data-guide-tab="chat" data-i18n="gtab_chat">Chat &amp; Commands</button>
    <button id="guide-tab-library" type="button" role="tab" aria-selected="false" aria-controls="guide-panel-library" tabindex="-1" data-guide-tab="library" data-i18n="gtab_library">Library &amp; Reading</button>
    <button id="guide-tab-privacy" type="button" role="tab" aria-selected="false" aria-controls="guide-panel-privacy" tabindex="-1" data-guide-tab="privacy" data-i18n="gtab_privacy">Privacy &amp; Basics</button>
  </div>
  <div id="guide-modal-body">
    <section id="guide-panel-chat" role="tabpanel" aria-labelledby="guide-tab-chat" class="guide-stack">
      <div class="guide-card">
        <h3 data-i18n="guide_slash_t" class="guide-card-title">Quick Commands ( / )</h3>
        <p data-i18n="guide_slash_intro" class="guide-note">Type / at the start of your message to choose a helpful mode:</p>
        <div class="guide-row"><code class="guide-kbd">/explain</code><span data-i18n="slash_explain_d">Explain clearly in plain language</span></div>
        <div class="guide-row"><code class="guide-kbd">/summarize</code><span data-i18n="slash_summarize_d">Key takeaways &amp; action items</span></div>
        <div class="guide-row"><code class="guide-kbd">/quiz</code><span data-i18n="slash_quiz_d">Socratic active-recall quiz with hints</span></div>
        <div class="guide-row"><code class="guide-kbd">/compare</code><span data-i18n="slash_compare_d">Side-by-side pros, cons &amp; trade-offs</span></div>
        <div class="guide-row"><code class="guide-kbd">/factcheck</code><span data-i18n="slash_factcheck_d">Verify claims &amp; flag assumptions</span></div>
        <div class="guide-row"><code class="guide-kbd">/translate</code><span data-i18n="slash_translate_d">Translate naturally while preserving tone</span></div>
      </div>
      <div class="guide-card">
        <h3 data-i18n="guide_mention_t" class="guide-card-title">Ask Another Agent ( @ )</h3>
        <p data-i18n="guide_mention_d" class="guide-note">Type @ anywhere in your message (for example “What do you think @erika?”) to ask another specialist in the same chat. You can also assign each agent its own model in Agents.</p>
      </div>
      <div class="guide-card">
        <h3 data-i18n="guide_copilot_t" class="guide-card-title">Right Sidebar Copilot ( #file )</h3>
        <p data-i18n="guide_copilot_d" class="guide-note">Press ⌘J to open Copilot beside any document, code file, board, or workflow. Highlight text to ask or edit selections, type # to attach extra files, and review diffs with 1-click Apply &amp; Undo.</p>
      </div>
      <div class="guide-card">
        <h3 data-i18n="guide_chat_t" class="guide-card-title">Attachments &amp; Answer Actions</h3>
        <p data-i18n="guide_chat_attach" class="guide-note">Click + in the prompt bar to attach files just for the current chat. Click ··· under any reply for a Second Opinion, structured Answer Format, or PDF export.</p>
      </div>
    </section>
    <section id="guide-panel-library" role="tabpanel" aria-labelledby="guide-tab-library" hidden class="guide-stack">
      <div class="guide-card">
        <h3 data-i18n="guide_files_t" class="guide-card-title">Documents &amp; Linked Folders</h3>
        <p data-i18n="guide_files_d" class="guide-note">Drop PDFs, Word, Excel, PowerPoint, or Markdown notes into your Library — or choose Link Local Folder… to use an existing folder on your computer without copying files.</p>
      </div>
      <div class="guide-card">
        <h3 data-i18n="guide_lib_t" class="guide-card-title">Reading, Editing &amp; Graph View</h3>
        <p data-i18n="guide_lib_highlight" class="guide-note">Highlight any text while reading a document to explain it simply, ask an agent, or quote it in chat. Edit notes directly or explore connections in Graph View.</p>
      </div>
      <div class="guide-card">
        <h3 data-i18n="guide_study_t" class="guide-card-title">Study Cards &amp; Audio Briefings</h3>
        <p data-i18n="guide_lib_tools" class="guide-note">Inside Library, create flashcards with Study Cards (including Anki export), scan for gaps across your notes, or generate spoken Audio Briefings.</p>
      </div>
    </section>
    <section id="guide-panel-privacy" role="tabpanel" aria-labelledby="guide-tab-privacy" hidden class="guide-stack">
      <div class="guide-card">
        <h3 data-i18n="guide_priv_t" class="guide-card-title">Private &amp; Local by Default</h3>
        <p data-i18n="guide_priv_d" class="guide-note">Local-Only Lock is on by default so your documents stay on your computer. In Settings you can review or redact personal details, back up workspaces as ZIPs, or adjust text size and colors.</p>
      </div>
      <div class="guide-card">
        <h3 data-i18n="guide_keys_t" class="guide-card-title">Useful Shortcuts</h3>
        <div class="guide-row"><code id="guide-kbd-search" class="guide-kbd">⌘K</code><span data-i18n="guide_k_search">Search documents, chats &amp; actions</span></div>
        <div class="guide-row"><code id="guide-kbd-files" class="guide-kbd">⌘P</code><span data-i18n="guide_k_files">Quick open any Markdown or code file</span></div>
        <div class="guide-row"><code id="guide-kbd-copilot" class="guide-kbd">⌘J</code><span data-i18n="guide_k_copilot">Toggle Right Sidebar Copilot</span></div>
        <div class="guide-row"><code id="guide-kbd-save" class="guide-kbd">⌘S</code><span data-i18n="guide_k_save">Save active file tab</span></div>
        <div class="guide-row"><code class="guide-kbd">Shift + Enter</code><span data-i18n="guide_k_newline">Add a new line in the prompt box</span></div>
        <div class="guide-row"><code class="guide-kbd">Esc</code><span data-i18n="guide_k_esc">Stop an answer or close a popup</span></div>
      </div>
    </section>
  </div>
  <div class="guide-footer shrink-0">
    <span data-i18n="guide_jump_lbl" class="text-xs text-[#738196]">Open:</span>
    <div class="flex items-center gap-2 flex-wrap">
      <button type="button" data-guide-jump="onboarding" data-i18n="setup_wizard" class="guide-jump-btn">Setup Wizard</button>
      <button type="button" data-guide-jump="agents" data-i18n="agents_nav" class="guide-jump-btn">Agents</button>
      <button type="button" data-guide-jump="formats" data-i18n="formats_nav" class="guide-jump-btn">Answer Formats</button>
      <button type="button" data-guide-jump="settings" data-i18n="settings" class="guide-jump-btn">Settings</button>
    </div>
  </div>
</dialog>"""
