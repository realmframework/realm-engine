"""Native Upload, consolidated Settings, and skippable 4-step Welcome Setup dialogs."""

from features.ui.agent_modals import AGENT_MODAL_HTML
from features.ui.experience_template import INSTALLER_PANEL
from features.ui.settings_template import SETTINGS_HTML
from features.ui.setup_template import mode_cards
from features.ui.studio_modals import STUDIO_MODAL_HTML

MODALS_HTML: str = f"""<dialog id="upload-modal" closedby="any" aria-labelledby="upload-modal-title" class="m-auto w-full max-w-2xl max-h-[85vh] overflow-hidden flex-col gap-4 rounded-2xl bg-[#0B1020] text-[#EEF2F8] border border-[rgba(238,242,248,0.16)] p-6 shadow-2xl">
  <div class="shrink-0 flex flex-col gap-3 text-left">
    <div class="flex items-center justify-between border-b border-[rgba(238,242,248,0.08)] pb-3"><h2 id="upload-modal-title" data-i18n="up_title" class="text-lg font-semibold text-[#EEF2F8]">Add Documents</h2><button id="close-upload-modal" type="button" aria-label="Close upload dialog" class="h-8 w-8 rounded-full text-[#738196] hover:text-[#EEF2F8] hover:bg-white/[0.06] flex items-center justify-center text-sm shrink-0">✕</button></div>
    <div id="upload-mode-bar" role="group" aria-label="Upload destination mode" class="grid grid-cols-2 gap-1.5 bg-[#04060F] p-1 rounded-xl border border-[rgba(238,242,248,0.10)]">
      <button id="upload-mode-vault-btn" type="button" aria-pressed="true" data-i18n="up_tab_lib" class="py-1.5 px-3 rounded-lg text-xs font-medium bg-[#4BB8E8] text-[#04060F] transition">Add to Library</button>
      <button id="upload-mode-chat-btn" type="button" aria-pressed="false" data-i18n="up_tab_chat" class="py-1.5 px-3 rounded-lg text-xs font-medium text-[#A0B0C8] hover:text-[#EEF2F8] transition">Attach to Current Chat</button>
    </div>
    <div id="upload-dropzone" class="bg-[#04060F] border border-dashed border-[rgba(238,242,248,0.16)] hover:border-[#4BB8E8] rounded-2xl p-4 text-center transition flex flex-col items-center justify-center gap-2">
      <input id="upload-file-input" type="file" accept=".md,.pdf,.docx,.txt,.html,.csv,.tsv,.xlsx,.pptx" multiple class="visually-hidden" />
      <input id="upload-folder-input" type="file" webkitdirectory directory multiple hidden tabindex="-1" aria-hidden="true" />
      <span data-i18n="up_drop_hint" class="text-sm font-medium text-[#EEF2F8]">Drop files or whole folders here (PDF, Word, Excel, PowerPoint, CSV, MD)</span>
      <div class="flex flex-wrap items-center justify-center gap-2.5 pt-1">
        <label for="upload-file-input" data-i18n="browse_files" class="cursor-pointer px-3.5 py-2 rounded-xl bg-[#0B1020] border border-[rgba(238,242,248,0.14)] hover:border-[#4BB8E8] text-xs font-medium text-[#EEF2F8] transition">Browse Files</label>
        <button id="import-native-folder-btn" type="button" data-i18n="import_folder" class="cursor-pointer px-3.5 py-2 rounded-xl bg-[#4BB8E8]/15 border border-[#4BB8E8]/40 hover:bg-[#4BB8E8]/25 text-xs font-medium text-[#4BB8E8] transition">Import Folder (with Subfolders)</button>
        <button id="upload-link-vault-btn" type="button" data-i18n="open_vault" class="cursor-pointer px-3.5 py-2 rounded-xl bg-[#0B1020] border border-[#4BB8E8]/35 hover:border-[#4BB8E8] text-xs font-medium text-[#EEF2F8] transition">Link Local Folder…</button>
      </div>
      <p data-i18n="up_link_note" class="text-xs text-[#A0B0C8]">Import Folder copies into Library · Link Local Folder connects in place with zero copies so you can unlink anytime without deleting files.</p>
      <div id="upload-staged-list" class="text-xs font-mono text-[#4BB8E8] mt-0.5 line-clamp-2 break-all"></div>
    </div>
    <div class="flex flex-col gap-1 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] px-3.5 py-2.5">
      <label for="clip-url-input" data-i18n="clip_lbl" class="text-xs text-[#A0B0C8]">Clip Web Page to Offline Markdown (when Local-Only Lock is OFF)</label>
      <div class="flex items-center gap-2">
        <input id="clip-url-input" type="url" placeholder="https://example.com/article" class="flex-1 bg-[#0B1020] border border-white/15 focus:border-[#4BB8E8] rounded-lg px-3 py-1.5 text-xs text-[#EEF2F8] outline-none" />
        <button id="clip-url-btn" type="button" data-i18n="clip_btn" class="px-3 py-1.5 rounded-lg bg-[#4BB8E8]/15 border border-[#4BB8E8]/35 text-xs font-medium text-[#4BB8E8] hover:bg-[#4BB8E8]/25 shrink-0 transition">Clip URL</button>
      </div>
    </div>
    <div id="upload-save-area-group" hidden><label for="upload-save-area" data-i18n="up_save_area" class="block mb-1 text-xs text-[#A0B0C8]">Save to area:</label><select id="upload-save-area" name="area" class="w-full rounded-lg bg-[#04060F] border border-white/15 px-3 py-2 text-sm"></select></div>
    <div class="flex flex-col gap-1.5">
      <div class="flex gap-3"><div class="flex-1 min-w-0">
      <label for="upload-subfolder" data-i18n="up_save_sub" class="block mb-1 text-xs text-[#A0B0C8]">Save in subfolder</label>
      <select id="upload-subfolder" name="subfolder" class="w-full rounded-lg bg-[#04060F] border border-white/15 px-3 py-2 text-sm"><option value="" data-i18n="up_area_root">Area root</option></select></div>
      <div id="upload-new-subfolder-group" class="hidden flex-1 min-w-0"><label for="upload-new-subfolder" data-i18n="up_new_sub_lbl" class="block text-xs text-[#A0B0C8] mb-1">New subfolder path</label><input id="upload-new-subfolder" name="new_subfolder" type="text" maxlength="255" placeholder="architecture/backend" autocapitalize="none" spellcheck="false" aria-describedby="upload-folder-help" class="w-full rounded-lg bg-[#04060F] border border-white/15 px-3 py-2 text-sm"/></div></div>
      <p id="upload-folder-help" data-i18n="up_sub_help" class="text-xs text-[#A0B0C8]">Folders share this area's search and chats. Use / for nested folders.</p>
    </div>
    <label for="cfg-anonymize-uploads" class="flex items-center justify-between gap-3 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] px-4 py-3 cursor-pointer select-none">
      <span class="flex flex-col gap-0.5"><span class="text-sm font-medium text-[#EEF2F8]"><span data-everyday-only data-i18n="up_anon_title">Hide personal details before saving</span><span data-specialist-only data-i18n="up_anon_spec">Anonymize personal names, emails, IBANs &amp; phones (GDPR)</span></span><span data-i18n="up_anon_desc" class="text-xs text-[#738196]">Extracts text into a Markdown guide inside your active Library folder.</span></span>
      <input id="cfg-anonymize-uploads" type="checkbox" switch role="switch" checked class="shrink-0" />
    </label>
    <div id="upload-progress-panel" hidden class="rounded-xl bg-[#04060F] border border-[#4BB8E8]/40 px-4 py-3 flex flex-col gap-2">
      <div class="flex items-center justify-between gap-2">
        <div class="flex items-center gap-2.5 min-w-0">
          <svg aria-hidden="true" class="w-4 h-4 text-[#4BB8E8] shrink-0 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9" opacity="0.22"/><path stroke-linecap="round" d="M21 12a9 9 0 0 0-9-9"/></svg>
          <span id="upload-progress-title" class="text-sm font-medium text-[#EEF2F8] truncate">Preparing import…</span>
        </div>
        <span id="upload-progress-count" class="text-xs font-mono text-[#4BB8E8] shrink-0"></span>
      </div>
      <div class="w-full h-2 rounded-full bg-white/10 overflow-hidden"><div id="upload-progress-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" aria-label="Import progress" class="h-full rounded-full bg-[#4BB8E8] transition-all duration-200" style="width:0%"></div></div>
      <div id="upload-progress-file" class="text-xs font-mono text-[#738196] truncate"></div>
    </div>
  </div>
  <section id="upload-redaction-inspector" aria-label="Governance and redaction preview" class="hidden min-h-0 flex-1 max-h-[42vh] overflow-y-auto overscroll-contain p-4 rounded-xl border border-white/10 bg-[#04060F]"></section>
  <div class="shrink-0 flex items-center justify-between gap-2 pt-2 border-t border-[rgba(238,242,248,0.08)]">
    <span id="upload-status" role="status" aria-live="polite" class="text-xs text-[#4BB8E8] truncate"></span>
    <div class="flex items-center gap-2 shrink-0">
      <button id="cancel-upload-btn" type="button" data-i18n="cancel" class="px-3.5 py-1.5 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.12)] text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition">Cancel</button>
      <button id="confirm-upload-btn" type="button" data-i18n="up_confirm_lib" class="px-4 py-1.5 rounded-xl bg-[#4BB8E8] text-[#04060F] font-semibold text-xs hover:brightness-110 transition">Upload &amp; Index</button>
    </div>
  </div>
</dialog>
<dialog id="move-guide-modal" closedby="any" aria-labelledby="move-guide-title" aria-describedby="move-guide-description" class="m-auto w-[calc(100%_-_2rem)] max-w-md max-h-[85vh] overflow-y-auto rounded-2xl border border-white/15 bg-[#0B1020] p-6 text-[#EEF2F8] shadow-2xl">
  <h2 id="move-guide-title" data-i18n="reader_move_btn" class="text-lg font-semibold">Move guide</h2>
  <p id="move-guide-description" class="mt-2 mb-4 text-sm text-[#A0B0C8] break-words"></p>
  <form id="card-move-form" action="/api/guides/" method="post" class="flex flex-col gap-4">
    <div id="move-guide-fields"></div>
    <p id="card-move-status" role="status" class="text-xs text-[#A0B0C8]"></p>
    <div class="flex justify-end gap-2">
      <button type="submit" formmethod="dialog" formnovalidate value="cancel" data-i18n="cancel" class="rounded-xl border border-white/15 px-3.5 py-2 text-sm">Cancel</button>
      <button id="card-move-submit" type="submit" data-i18n="reader_move_btn" class="rounded-xl bg-[#4BB8E8] px-3.5 py-2 text-sm font-medium text-[#04060F]">Move guide</button>
    </div>
  </form>
</dialog>
{SETTINGS_HTML}
{STUDIO_MODAL_HTML}
{AGENT_MODAL_HTML}
<dialog id="onboarding-modal" closedby="any" aria-labelledby="onboarding-modal-title" class="m-auto w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-2xl bg-[#0B1020] text-[#EEF2F8] border border-[rgba(238,242,248,0.16)] p-6 shadow-2xl">
  <div class="flex flex-col gap-4 text-left">
    <div class="flex items-center justify-between gap-2 border-b border-[rgba(238,242,248,0.08)] pb-3">
      <div class="flex items-center gap-2.5"><img id="onboarding-logo" src="/static/logo-192.png" width="22" height="22" class="w-5 h-5 rounded object-cover" alt=""><h2 id="onboarding-modal-title" data-i18n="ob_title" class="text-lg font-semibold text-[#EEF2F8]">Welcome to REALM Engine</h2><span id="onboarding-step-badge" class="px-2 py-0.5 rounded-full bg-[#04060F] border border-[rgba(238,242,248,0.12)] text-2xs font-mono text-[#738196]">1 / 4</span></div>
      <div class="flex items-center gap-2"><button id="onboarding-skip-btn" type="button" data-i18n="ob_skip" class="text-xs text-[#738196] hover:text-[#EEF2F8] transition">Skip for now</button><button id="close-onboarding-modal" type="button" autofocus aria-label="Close setup wizard" class="h-8 w-8 rounded-full text-[#738196] hover:text-[#EEF2F8] hover:bg-white/[0.06] flex items-center justify-center text-sm shrink-0">✕</button></div>
    </div>

    <section id="onboarding-step-1" class="flex flex-col gap-4">
      <div><h3 data-i18n="ob_s1_head" class="text-lg font-medium text-[#EEF2F8]">Your Private, Local-First Knowledge Engine</h3><p data-i18n="ob_s1_sub" class="text-xs text-[#A0B0C8] mt-1">Choose your language and see what REALM Engine can do for you.</p></div>
      <div class="flex flex-col gap-1.5">
        <span data-i18n="language_label" class="text-xs uppercase tracking-wider text-[#738196] font-mono">Interface Language</span>
        <div role="group" aria-label="Choose language" class="grid grid-cols-3 gap-1.5 bg-[#04060F] p-1 rounded-xl border border-[rgba(238,242,248,0.10)]">
          <button type="button" data-lang-choice="en" aria-pressed="true" class="py-1.5 px-3 rounded-lg text-xs font-medium transition bg-[#4BB8E8] text-[#04060F]">English</button>
          <button type="button" data-lang-choice="de" aria-pressed="false" class="py-1.5 px-3 rounded-lg text-xs font-medium transition text-[#A0B0C8] hover:text-[#EEF2F8]">Deutsch</button>
          <button type="button" data-lang-choice="es" aria-pressed="false" class="py-1.5 px-3 rounded-lg text-xs font-medium transition text-[#A0B0C8] hover:text-[#EEF2F8]">Español</button>
        </div>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        <div class="rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] p-3.5 flex flex-col gap-2"><svg aria-hidden="true" class="w-5 h-5 text-[#4BB8E8]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 0 1 2-2h5l2 2h5a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6Z"/></svg><div data-i18n="ob_f1_t" class="text-sm font-medium text-[#EEF2F8]">Private Document Vault</div><p data-i18n="ob_f1_d" class="text-xs text-[#A0B0C8] leading-relaxed">Drop PDFs, Word files, Markdown, or notes — everything stays cleanly on your computer.</p></div>
        <div class="rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] p-3.5 flex flex-col gap-2"><svg aria-hidden="true" class="w-5 h-5 text-[#4BB8E8]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.3-4.3M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z"/></svg><div data-i18n="ob_f2_t" class="text-sm font-medium text-[#EEF2F8]">Local or Cloud AI</div><p data-i18n="ob_f2_d" class="text-xs text-[#A0B0C8] leading-relaxed">Ask grounded questions with citations using free offline Ollama or your own paid API keys.</p></div>
        <div class="rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] p-3.5 flex flex-col gap-2"><svg aria-hidden="true" class="w-5 h-5 text-[#4BB8E8]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3l7 4v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V7l7-4Z"/></svg><div data-i18n="ob_f3_t" class="text-sm font-medium text-[#EEF2F8]">2D Graph &amp; Privacy Shield</div><p data-i18n="ob_f3_d" class="text-xs text-[#A0B0C8] leading-relaxed">Explore connections visually and detect or redact personal data (GDPR) before sharing.</p></div>
      </div>
    </section>

    <section id="onboarding-step-2" hidden class="flex flex-col gap-3.5 text-sm">
      <div><h3 data-i18n="ob_s2_head" class="text-lg font-medium text-[#EEF2F8]">Make This Workspace Yours</h3><p data-i18n="ob_s2_sub" class="text-xs text-[#A0B0C8] mt-1">Name your workspace, choose a logo, and preview a color theme live.</p></div>
      <div class="flex items-center justify-between"><span data-i18n="ob_ws_identity" class="text-xs uppercase tracking-wider text-[#738196] font-mono">Workspace Identity</span><button id="onboarding-new-folder-btn" type="button" data-i18n="new_folder" class="text-xs text-[#4BB8E8] hover:underline">+ New Folder</button></div>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        <label class="flex flex-col gap-1"><span data-i18n="workspace_title" class="text-xs text-[#A0B0C8]">Workspace Title</span><input id="onboarding-title" type="text" value="My Knowledge Base" placeholder="e.g. Study Notes, Recipes, Work" class="bg-[#04060F] border border-[rgba(238,242,248,0.12)] focus:border-[#4BB8E8] rounded-lg px-3 py-1.5 text-sm text-[#EEF2F8] outline-none" /></label>
        <label class="flex flex-col gap-1"><span data-i18n="agent_name_title" class="text-xs text-[#A0B0C8]">Name Your Agent</span><input id="onboarding-agent-name" type="text" maxlength="40" value="Saga" placeholder="Saga" class="bg-[#04060F] border border-[rgba(238,242,248,0.12)] focus:border-[#4BB8E8] rounded-lg px-3 py-1.5 text-sm text-[#EEF2F8] outline-none" /></label>
        <div class="flex flex-col gap-1"><label for="onboarding-folder-select" data-i18n="knowledge_folder" class="text-xs text-[#A0B0C8]">Knowledge Folder</label><select id="onboarding-folder-select" class="bg-[#04060F] border border-[rgba(238,242,248,0.12)] focus:border-[#4BB8E8] rounded-lg px-3 py-1.5 text-sm font-mono text-[#EEF2F8] outline-none cursor-pointer"></select><input id="onboarding-folder" type="text" value="" aria-label="New folder name" placeholder="e.g. study_notes" class="hidden bg-[#04060F] border border-[rgba(238,242,248,0.12)] focus:border-[#4BB8E8] rounded-lg px-3 py-1.5 text-sm font-mono text-[#EEF2F8] outline-none" /><span id="onboarding-folder-helper" data-i18n="folder_saved_generic" class="text-xs font-mono text-[#738196]">Saved locally in your active workspace folder</span></div>
      </div>
      <div class="flex items-center gap-3 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] p-3">
        <img id="onboarding-logo-preview" src="/static/logo-512.png" width="36" height="36" class="w-9 h-9 rounded-lg object-cover shrink-0" alt="Workspace logo" />
        <div class="flex-1 min-w-0"><div data-i18n="appearance_logo_title" class="text-sm font-medium text-[#EEF2F8]">Workspace Logo</div><div data-i18n="logo_onboarding_note" class="text-xs text-[#A0B0C8]">Upload PNG, JPG, or WebP — or keep the REALM logo.</div></div>
        <input id="onboarding-logo-input" type="file" accept="image/png,image/jpeg,image/webp" class="visually-hidden" />
        <label for="onboarding-logo-input" data-i18n="change_logo" class="cursor-pointer px-3 py-1.5 rounded-lg bg-[#0B1020] border border-[rgba(238,242,248,0.12)] hover:border-[#4BB8E8] text-xs font-medium text-[#4BB8E8] shrink-0 transition">Change Logo</label>
      </div>
      <div class="grid grid-cols-3 gap-1.5 bg-[#04060F] p-1 rounded-xl border border-[rgba(238,242,248,0.10)]" role="group" aria-label="Setup Theme Mode">
        <button type="button" data-theme-mode="system" aria-pressed="true" data-i18n="theme_system" class="py-1.5 px-2.5 rounded-lg text-xs font-medium transition bg-[#4BB8E8] text-[#04060F]">System</button>
        <button type="button" data-theme-mode="dark" aria-pressed="false" data-i18n="theme_dark" class="py-1.5 px-2.5 rounded-lg text-xs font-medium transition text-[#A0B0C8] hover:text-[#EEF2F8]">Dark</button>
        <button type="button" data-theme-mode="light" aria-pressed="false" data-i18n="theme_light" class="py-1.5 px-2.5 rounded-lg text-xs font-medium transition text-[#A0B0C8] hover:text-[#EEF2F8]">Light (Clear)</button>
      </div>
      <div id="onboarding-presets-bar" role="group" aria-label="Setup starter color palettes" class="flex flex-wrap gap-1.5"></div>
      <label for="onboarding-ambient-toggle" class="flex items-center justify-between gap-3 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] px-4 py-2.5 cursor-pointer select-none"><span data-i18n="ambient_toggle" class="text-sm text-[#EEF2F8]">Ambient Background</span><input id="onboarding-ambient-toggle" type="checkbox" switch role="switch" checked class="shrink-0" /></label>
      <label for="onboarding-sync-agent-palette" class="flex items-center justify-between gap-3 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] px-4 py-2.5 cursor-pointer select-none"><span><span data-i18n="sync_agent_palette_title" class="block text-sm text-[#EEF2F8]">Sync Theme Palette with Active Agent</span><span data-i18n="sync_agent_palette_desc" class="block text-xs text-[#A0B0C8] mt-0.5">Automatically adapt colors when switching between Saga, Lisbeth, Milton, and other agents (change anytime in Agents).</span></span><input id="onboarding-sync-agent-palette" type="checkbox" switch role="switch" checked class="shrink-0" /></label>
    </section>

    <section id="onboarding-step-3" hidden class="flex flex-col gap-3.5 text-sm">
      <div><h3 data-i18n="ob_s3_head" class="text-lg font-medium text-[#EEF2F8]">Choose How AI Runs</h3><p data-i18n="ob_s3_sub" class="text-xs text-[#A0B0C8] mt-1">Run 100% offline with Ollama, combine Ollama with paid cloud API keys, or start with instant search only.</p></div>
      {mode_cards("onboarding")}
      {INSTALLER_PANEL}
      <div class="flex flex-col gap-2 text-sm">
        <div id="onboarding-status-text" role="status" class="bg-[#04060F] border border-[rgba(238,242,248,0.08)] rounded-xl px-3.5 py-2 text-xs font-mono text-[#4BB8E8]">● Checking local Ollama &amp; retrieval engine...</div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          <label class="flex flex-col gap-1"><span data-i18n="ob_def_provider" class="text-xs text-[#A0B0C8]">Default Provider</span><select id="onboarding-provider" class="bg-[#04060F] border border-[rgba(238,242,248,0.12)] focus:border-[#4BB8E8] rounded-lg px-3 py-1.5 text-sm text-[#EEF2F8] outline-none cursor-pointer"><option value="ollama">Ollama Local</option><option value="openai">OpenAI</option><option value="gemini">Gemini</option><option value="kimi">Kimi</option><option value="deepseek">DeepSeek</option><option value="anthropic">Anthropic</option><option value="xai">xAI</option><option value="mistral">Mistral</option></select></label>
          <label class="flex flex-col gap-1"><span data-i18n="ob_model_lbl" class="text-xs text-[#A0B0C8]">Model</span><select id="onboarding-model" aria-label="Setup AI Model" class="bg-[#04060F] border border-[rgba(238,242,248,0.12)] focus:border-[#4BB8E8] rounded-lg px-3 py-1.5 text-sm text-[#EEF2F8] outline-none cursor-pointer"></select></label>
        </div>
        <div id="onboarding-privacy-notice" role="status" data-i18n="local_exec_notice" class="text-xs text-[#738196]">Local execution — data stays on this device</div>
        <div id="onboarding-api-key-group" class="hidden flex-col gap-1.5">
          <label for="onboarding-api-key" id="onboarding-api-key-label" data-i18n="ob_api_key_lbl" class="text-xs text-[#A0B0C8]">API Key (Saved on this computer)</label>
          <div id="onboarding-key-connected" hidden class="rounded-xl bg-[#04060F] border border-[#38D399]/40 px-3.5 py-2.5 flex flex-wrap items-center justify-between gap-2">
            <div class="flex items-center gap-2"><span aria-hidden="true" class="w-2.5 h-2.5 rounded-full bg-[#38D399]"></span><span id="onboarding-key-badge" data-i18n="key_connected" class="text-xs font-semibold text-[#38D399]">Connected</span><code id="onboarding-key-mask" class="px-2 py-0.5 rounded bg-[#0B1020] border border-white/10 font-mono text-xs text-[#EEF2F8]">••••</code></div>
            <div class="flex items-center gap-2"><button id="onboarding-replace-key-btn" type="button" data-i18n="key_replace_btn" class="px-2.5 py-1 rounded-lg bg-[#0B1020] border border-white/15 hover:border-[#4BB8E8] text-xs font-medium text-[#EEF2F8]">Replace</button><button id="onboarding-remove-key-btn" type="button" data-i18n="key_remove_btn" class="px-2.5 py-1 rounded-lg bg-[#0B1020] border border-[#EF4444]/40 text-xs font-medium text-[#FCA5A5]">Remove</button></div>
          </div>
          <div id="onboarding-key-entry-row" class="flex items-center gap-2">
            <div class="relative flex-1 flex items-center"><input id="onboarding-api-key" type="password" autocomplete="off" autocorrect="off" autocapitalize="none" spellcheck="false" placeholder="Paste your API key" data-i18n-placeholder="api_key_enter_ph" class="key-secret-input w-full bg-[#04060F] border border-[rgba(238,242,248,0.12)] focus:border-[#4BB8E8] rounded-lg px-3 py-1.5 text-sm text-[#EEF2F8] outline-none" /><button id="toggle-onboarding-key-visibility" type="button" aria-pressed="false" aria-label="Show API key" class="key-eye-btn"></button></div>
            <button id="onboarding-save-key-btn" type="button" data-i18n="save_key" class="px-3.5 py-2 rounded-lg bg-[#4BB8E8] text-[#04060F] text-xs font-semibold hover:brightness-110 shrink-0 transition">Save Key</button>
            <button id="onboarding-cancel-replace-btn" type="button" hidden data-i18n="cancel" class="px-3 py-2 rounded-lg bg-[#04060F] border border-white/15 text-xs text-[#A0B0C8] shrink-0">Cancel</button>
          </div>
        </div>
        <div id="onboarding-keys-bar" role="group" aria-label="Configured providers" class="flex flex-wrap gap-1.5"></div>
      </div>
    </section>

    <section id="onboarding-step-4" hidden class="flex flex-col gap-4">
      <div><h3 data-i18n="ob_s4_head" class="text-lg font-medium text-[#EEF2F8]">You're All Set!</h3><p data-i18n="ob_s4_sub" class="text-xs text-[#A0B0C8] mt-1">You can customize anything anytime in Settings. Ready to explore your workspace?</p></div>
      <div id="onboarding-summary" class="rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] px-4 py-2"></div>
    </section>

    <div class="flex items-center justify-between gap-3 pt-3 border-t border-[rgba(238,242,248,0.08)]">
      <div class="flex items-center gap-1.5" role="group" aria-label="Setup progress">
        <button type="button" data-onboarding-dot="1" aria-label="Step 1" class="h-2 w-6 rounded-full bg-[#4BB8E8]"></button>
        <button type="button" data-onboarding-dot="2" aria-label="Step 2" class="h-2 w-2 rounded-full bg-[rgba(238,242,248,0.22)]"></button>
        <button type="button" data-onboarding-dot="3" aria-label="Step 3" class="h-2 w-2 rounded-full bg-[rgba(238,242,248,0.22)]"></button>
        <button type="button" data-onboarding-dot="4" aria-label="Step 4" class="h-2 w-2 rounded-full bg-[rgba(238,242,248,0.22)]"></button>
      </div>
      <div class="flex items-center gap-2">
        <button id="onboarding-back-btn" type="button" hidden data-i18n="ob_back" class="px-3.5 py-2 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.12)] text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition">← Back</button>
        <button id="onboarding-next-btn" type="button" data-i18n="ob_next" class="px-4 py-2 rounded-xl bg-[#4BB8E8] text-[#04060F] font-semibold text-xs hover:brightness-110 transition">Next →</button>
        <div id="onboarding-final-actions" hidden class="flex items-center gap-2">
          <button id="onboarding-upload-btn" type="button" data-i18n="ob_upload_btn" class="px-3.5 py-2 rounded-xl bg-[#04060F] border border-[#4BB8E8]/40 text-[#4BB8E8] hover:bg-[#4BB8E8]/10 text-xs font-medium transition">Upload First PDF / Word / MD Files</button>
          <button id="onboarding-start-btn" type="button" data-i18n="ob_start_btn" class="px-4 py-2 rounded-xl bg-[#4BB8E8] text-[#04060F] font-semibold text-xs hover:brightness-110 transition">Start Exploring →</button>
        </div>
      </div>
    </div>
  </div>
</dialog>"""
