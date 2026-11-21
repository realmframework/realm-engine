"""Built-in 4-tab Quick Guide & Shortcuts modal (discoverable via ?, Cmd/Ctrl+/, /help, Cmd/Ctrl+K, Settings)."""

GUIDE_STYLES_CSS: str = r"""<style>
#guide-modal { inline-size: min(48rem, calc(100vw - 2rem)); max-block-size: 86vh; overflow: hidden; }
#guide-modal[open] { display: flex; flex-direction: column; }
#guide-modal-body { flex: 1 1 auto; min-block-size: 16rem; max-block-size: 58vh; overflow-y: auto; display: flex; flex-direction: column; gap: 0.85rem; padding-inline-end: 0.25rem; padding-block-start: 0.5rem; }
.guide-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.75rem; }
@media (max-width: 640px) { .guide-grid { grid-template-columns: 1fr; } }
.guide-card { border-radius: 0.9rem; background: var(--background); border: 1px solid var(--border-subtle); padding: 0.9rem 1rem; display: flex; flex-direction: column; gap: 0.5rem; }
.guide-card-title { font-size: 0.82rem; font-weight: 600; color: var(--text); display: flex; align-items: center; gap: 0.45rem; }
.guide-row { display: flex; align-items: baseline; justify-content: space-between; gap: 0.6rem; font-size: 0.78rem; color: var(--text-muted); line-height: 1.45; }
.guide-kbd { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.7rem; padding: 0.12rem 0.42rem; border-radius: 0.35rem; border: 1px solid var(--border); background: var(--surface-raised); color: var(--accent); white-space: nowrap; flex-shrink: 0; }
.guide-note { font-size: 0.77rem; color: var(--text-muted); line-height: 1.5; margin: 0; }
.guide-footer { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; flex-wrap: wrap; border-top: 1px solid var(--border-subtle); padding-block-start: 0.75rem; }
.guide-jump-btn { padding: 0.35rem 0.7rem; border-radius: 0.7rem; border: 1px solid var(--border); background: var(--background); color: var(--text-muted); font-size: 0.75rem; cursor: pointer; transition: border-color 140ms ease, color 140ms ease; }
.guide-jump-btn:hover { border-color: var(--accent); color: var(--text); }
</style>"""

GUIDE_MODAL_HTML: str = r"""<dialog id="guide-modal" closedby="any" aria-labelledby="guide-modal-title" class="m-auto rounded-2xl bg-[#0B1020] text-[#EEF2F8] border border-white/15 p-6 shadow-2xl gap-3">
  <div class="flex items-center justify-between gap-3 shrink-0">
    <div>
      <h2 id="guide-modal-title" data-i18n="guide_title" class="text-lg font-semibold text-[#EEF2F8]">Quick Guide &amp; Shortcuts</h2>
      <p data-i18n="guide_sub" class="text-xs text-[#738196] mt-0.5">Everything you can trigger from the keyboard, prompt bar, or Library.</p>
    </div>
    <button id="close-guide-modal" type="button" aria-label="Close guide" data-i18n-aria-label="aria_close_dialog" class="h-8 w-8 rounded-full text-[#738196] hover:text-[#EEF2F8] hover:bg-white/[0.06] flex items-center justify-center text-sm shrink-0">✕</button>
  </div>
  <div id="guide-tabs" role="tablist" aria-label="Guide sections" class="settings-tabs shrink-0">
    <button id="guide-tab-shortcuts" type="button" role="tab" aria-selected="true" aria-controls="guide-panel-shortcuts" tabindex="0" data-guide-tab="shortcuts" data-i18n="gtab_shortcuts">Shortcuts &amp; /</button>
    <button id="guide-tab-chat" type="button" role="tab" aria-selected="false" aria-controls="guide-panel-chat" tabindex="-1" data-guide-tab="chat" data-i18n="gtab_chat">Chat &amp; Agents</button>
    <button id="guide-tab-library" type="button" role="tab" aria-selected="false" aria-controls="guide-panel-library" tabindex="-1" data-guide-tab="library" data-i18n="gtab_library">Library &amp; Study</button>
    <button id="guide-tab-privacy" type="button" role="tab" aria-selected="false" aria-controls="guide-panel-privacy" tabindex="-1" data-guide-tab="privacy" data-i18n="gtab_privacy">Privacy &amp; API</button>
  </div>
  <div id="guide-modal-body">
    <section id="guide-panel-shortcuts" role="tabpanel" aria-labelledby="guide-tab-shortcuts" class="guide-grid">
      <div class="guide-card">
        <h3 data-i18n="guide_slash_t" class="guide-card-title">Prompt Commands ( / )</h3>
        <p data-i18n="guide_slash_intro" class="guide-note">Type / at the start of the prompt to activate a mode chip without cluttering your message:</p>
        <div class="guide-row"><code class="guide-kbd">/quiz</code><span data-i18n="slash_quiz_d">Socratic active-recall quiz with hints</span></div>
        <div class="guide-row"><code class="guide-kbd">/explain</code><span data-i18n="slash_explain_d">Explain clearly in plain language</span></div>
        <div class="guide-row"><code class="guide-kbd">/summarize</code><span data-i18n="slash_summarize_d">Key takeaways &amp; action items</span></div>
        <div class="guide-row"><code class="guide-kbd">/compare</code><span data-i18n="slash_compare_d">Side-by-side pros, cons &amp; trade-offs</span></div>
        <div class="guide-row"><code class="guide-kbd">/factcheck</code><span data-i18n="slash_factcheck_d">Verify claims &amp; flag assumptions</span></div>
        <div class="guide-row"><code class="guide-kbd">/eli5 · /translate</code><span data-i18n="guide_slash_more">Simple analogies or tone-preserving translation</span></div>
        <div class="guide-row"><code class="guide-kbd">/free · /new · /help</code><span data-i18n="guide_slash_modes">Free Chat, fresh chat, or open this guide</span></div>
      </div>
      <div class="guide-card">
        <h3 data-i18n="guide_keys_t" class="guide-card-title">Keyboard Shortcuts</h3>
        <div class="guide-row"><code class="guide-kbd">⌘K / Ctrl+K</code><span data-i18n="guide_k_search">Quick Search across guides, chats &amp; actions</span></div>
        <div class="guide-row"><code class="guide-kbd">⌘I / Ctrl+I</code><span data-i18n="guide_k_inspector">Toggle Engine Inspector &amp; Retrieval X-Ray</span></div>
        <div class="guide-row"><code class="guide-kbd">? · ⌘/</code><span data-i18n="guide_k_help">Open this Quick Guide &amp; Shortcuts dialog</span></div>
        <div class="guide-row"><code class="guide-kbd">Shift + Enter</code><span data-i18n="guide_k_newline">Add a new line inside the prompt box</span></div>
        <div class="guide-row"><code class="guide-kbd">Esc</code><span data-i18n="guide_k_esc">Stop AI generation or close any dialog</span></div>
        <div class="guide-row"><code class="guide-kbd">Space · 1 / 2 / 3</code><span data-i18n="guide_k_study">Flip &amp; rate flashcards in Study Cards</span></div>
        <div class="guide-row"><code class="guide-kbd">⌘S / Ctrl+S</code><span data-i18n="guide_k_save">Save &amp; re-index while editing a document</span></div>
        <div class="guide-row"><code class="guide-kbd">/ (in Graph)</code><span data-i18n="guide_k_graph">Focus the 2D Knowledge Graph filter</span></div>
      </div>
    </section>
    <section id="guide-panel-chat" role="tabpanel" aria-labelledby="guide-tab-chat" hidden class="guide-grid">
      <div class="guide-card">
        <h3 data-i18n="guide_mention_t" class="guide-card-title">Mention Agents ( @ ) &amp; Model Pinning</h3>
        <p data-i18n="guide_mention_d" class="guide-note">Type @ anywhere in your message (e.g. “What do you think @erika?”) to bring another agent into the thread for that turn. They read the full shared conversation without replacing your active agent.</p>
        <p data-i18n="guide_agents_pin" class="guide-note">In Agents, you can pin each specialist to its own local Ollama or cloud model — REALM serializes local Ollama calls and automatically unloads previous local models to protect RAM.</p>
      </div>
      <div class="guide-card">
        <h3 data-i18n="guide_chat_t" class="guide-card-title">Chat, Attachments &amp; Turn Actions</h3>
        <p data-i18n="guide_chat_attach" class="guide-note">Click + in the prompt bar and choose “Attach to Current Chat” to drop files into a thread without adding them to your Library. Attached files appear as removable chips right inside the prompt bar.</p>
        <p data-i18n="guide_chat_more" class="guide-note">Click ··· under any answer for Second Opinion, Answer in Format, Save as Guide, or Fork Chat. Click Sources (N) to inspect cited passages, or export as PDF, Markdown, or TXT.</p>
      </div>
      <div class="guide-card">
        <h3 data-i18n="guide_formats_t" class="guide-card-title">Answer Formats Studio</h3>
        <p data-i18n="guide_formats_d" class="guide-note">Choose from 13 built-in blueprints (SRS, User Stories, ADR, Dossier, Postmortem, Executive Brief) or create custom formats. Pin any format with /&lt;format&gt; or synthesize an entire thread into a structured deliverable.</p>
      </div>
      <div class="guide-card">
        <h3 data-i18n="guide_insp_t" class="guide-card-title">Engine Inspector &amp; Retrieval X-Ray</h3>
        <p data-i18n="guide_insp_d" class="guide-note">Open Inspector (⌘I / Ctrl+I) to monitor live context usage, run lossless Compress Context, inspect BM25/Vector/RRF scores per passage, and Pin or Mute sources before re-running.</p>
      </div>
    </section>
    <section id="guide-panel-library" role="tabpanel" aria-labelledby="guide-tab-library" hidden class="guide-grid">
      <div class="guide-card">
        <h3 data-i18n="guide_files_t" class="guide-card-title">9 Formats, Linked Folders &amp; Live Sync</h3>
        <p data-i18n="guide_files_d" class="guide-note">Import or drop .md, .pdf, .docx, .xlsx, .pptx, .csv, .tsv, .txt, and .html files — or use Link Local Folder… to index existing folders in place without copying files. A background watcher detects edits automatically.</p>
        <p data-i18n="guide_clip_d" class="guide-note">In Add Documents, clip public web articles cleanly to offline Markdown (available when Local-Only Lock is off).</p>
      </div>
      <div class="guide-card">
        <h3 data-i18n="guide_lib_t" class="guide-card-title">Reader, Highlight-to-Ask &amp; Editor</h3>
        <p data-i18n="guide_lib_highlight" class="guide-note">Highlight any text while reading a document to Explain simply, Ask Agent, or Quote in chat.</p>
        <p data-i18n="guide_editor_d" class="guide-note">Use Edit (Write / Preview + ⌘S) or + New Note to author Markdown directly, and Graph View to explore clusters across active workspaces.</p>
      </div>
      <div class="guide-card">
        <h3 data-i18n="guide_study_t" class="guide-card-title">Study Cards, Socratic Quiz &amp; Gap Scan</h3>
        <p data-i18n="guide_lib_tools" class="guide-note">Inside Library, use Study Cards for instant or AI-generated flashcards (5/10/15 cards), spaced repetition, Socratic Quiz mode, and Anki (.tsv) export. Run Gap Scan to spot contradictions, duplicates, and undocumented topics.</p>
      </div>
      <div class="guide-card">
        <h3 data-i18n="guide_voice_t" class="guide-card-title">Audio Briefings &amp; Hands-Free Voice</h3>
        <p data-i18n="guide_voice_d" class="guide-note">Generate Solo or Two-Voice Duo offline Audio Briefings (.wav + Markdown script) via local Phonon TTS, dictate with Whisper/mic, or enable Hands-Free Voice Loop in Settings → AI &amp; Voice.</p>
      </div>
    </section>
    <section id="guide-panel-privacy" role="tabpanel" aria-labelledby="guide-tab-privacy" hidden class="guide-grid">
      <div class="guide-card">
        <h3 data-i18n="guide_priv_t" class="guide-card-title">Privacy Lock, GDPR Audit &amp; Backups</h3>
        <p data-i18n="guide_priv_d" class="guide-note">Strict Local-Only Lock is ON by default. Preview or scrub personal data (emails, IBANs, dates, addresses), export GDPR &amp; EU AI Act technical reports, enforce daily cloud spend caps, and back up/restore workspaces as ZIPs.</p>
      </div>
      <div class="guide-card">
        <h3 data-i18n="guide_comfort_t" class="guide-card-title">Reading Comfort, Eco Mode &amp; Languages</h3>
        <p data-i18n="guide_comfort_d" class="guide-note">Pick from 15 WCAG 2.1 AA Dark/Light themes, Hyperlegible or Dyslexia fonts, S–XL text sizing, Focus/Normal/Wide width, High-Contrast Focus, Reduce Motion, Eco Mode (8 GB / CPU), and English / Deutsch / Español UI.</p>
      </div>
      <div class="guide-card">
        <h3 data-i18n="guide_api_t" class="guide-card-title">Local OpenAI API, CLI &amp; MCP Bridge</h3>
        <p data-i18n="guide_api_d" class="guide-note">Enable the loopback-only /v1 API in Settings → AI &amp; Voice for VS Code, Cursor, Raycast, or Shortcuts. Run realm-engine ask "..." from your terminal or realm-engine mcp as a stdio MCP server.</p>
      </div>
      <div class="guide-card">
        <h3 data-i18n="guide_diag_t" class="guide-card-title">Diagnostics &amp; Headless Public API</h3>
        <p data-i18n="guide_diag_d" class="guide-note">Check app version, loaded local models, and copy sanitized diagnostics inside Settings → Privacy &amp; GDPR Audit. Launch with --public to publish selected vaults read-only for static sites.</p>
      </div>
    </section>
  </div>
  <div class="guide-footer shrink-0">
    <span data-i18n="guide_jump_lbl" class="text-[11px] font-mono text-[#738196]">Quick jump:</span>
    <div class="flex items-center gap-1.5 flex-wrap">
      <button type="button" data-guide-jump="onboarding" data-i18n="setup_wizard" class="guide-jump-btn">Setup Wizard</button>
      <button type="button" data-guide-jump="agents" data-i18n="agents_nav" class="guide-jump-btn">Agents</button>
      <button type="button" data-guide-jump="formats" data-i18n="formats_nav" class="guide-jump-btn">Answer Formats</button>
      <button type="button" data-guide-jump="settings" data-i18n="settings" class="guide-jump-btn">Settings</button>
    </div>
  </div>
</dialog>"""
