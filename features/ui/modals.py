"""Native Upload, consolidated Settings and Setup Wizard dialogs."""

from features.ui.experience_template import INSTALLER_PANEL
from features.ui.settings_template import SETTINGS_HTML
from features.ui.setup_template import mode_cards

MODALS_HTML: str = f"""<dialog id="upload-modal" closedby="any" aria-labelledby="upload-modal-title" class="m-auto w-full max-w-2xl max-h-[85vh] overflow-hidden flex-col gap-4 rounded-2xl bg-[#0B1020] text-[#EEF2F8] border border-[rgba(238,242,248,0.16)] p-6 shadow-2xl">
  <div class="shrink-0 flex flex-col gap-3 text-left">
    <div class="flex items-center justify-between border-b border-[rgba(238,242,248,0.08)] pb-3"><h2 id="upload-modal-title" class="text-base font-medium text-[#EEF2F8]">Add Documents</h2><button id="close-upload-modal" type="button" aria-label="Close upload dialog" class="h-7 w-7 rounded-full text-[#738196] hover:text-[#EEF2F8] hover:bg-white/[0.06] flex items-center justify-center text-sm">✕</button></div>
    <div id="upload-dropzone" class="bg-[#04060F] border border-dashed border-[rgba(238,242,248,0.16)] hover:border-[#4BB8E8] rounded-2xl p-3 text-center transition flex flex-col items-center justify-center gap-1.5">
      <input id="upload-file-input" type="file" accept=".md,.pdf,.docx,.txt,.html" multiple class="visually-hidden" />
      <label for="upload-file-input" class="cursor-pointer w-full flex flex-col items-center gap-1.5"><span class="text-sm font-medium text-[#EEF2F8]">Drop PDF, Word (.docx), Markdown, or TXT files</span><span class="text-xs text-[#738196]">Click to browse or drag files to stage for upload</span></label>
      <div id="upload-staged-list" class="text-xs font-mono text-[#4BB8E8] mt-1 line-clamp-2 break-all"></div>
    </div>
    <div id="upload-save-area-group" hidden><label for="upload-save-area" class="block mb-1 text-xs text-[#A0B0C8]">Save to area:</label><select id="upload-save-area" name="area" class="w-full rounded-lg bg-[#04060F] border border-white/15 px-3 py-2 text-sm"></select></div>
    <div class="flex flex-col gap-1.5">
      <div class="flex gap-3"><div class="flex-1 min-w-0">
      <label for="upload-subfolder" class="block mb-1 text-xs text-[#A0B0C8]">Save in subfolder</label>
      <select id="upload-subfolder" name="subfolder" class="w-full rounded-lg bg-[#04060F] border border-white/15 px-3 py-2 text-sm"><option value="">Area root</option></select></div>
      <div id="upload-new-subfolder-group" class="hidden flex-1 min-w-0"><label for="upload-new-subfolder" class="block text-xs text-[#A0B0C8] mb-1">New subfolder path</label><input id="upload-new-subfolder" name="new_subfolder" type="text" maxlength="255" placeholder="architecture/backend" autocapitalize="none" spellcheck="false" aria-describedby="upload-folder-help" class="w-full rounded-lg bg-[#04060F] border border-white/15 px-3 py-2 text-sm"/></div></div>
      <p id="upload-folder-help" class="text-[11px] text-[#738196]">Folders share this area's search and chats. Use / for nested folders.</p>
    </div>
    <div class="flex flex-col gap-1.5 pt-1">
      <label for="cfg-anonymize-uploads" class="flex items-center gap-2 text-xs text-[#A0B0C8] cursor-pointer select-none"><input id="cfg-anonymize-uploads" type="checkbox" checked class="rounded" /><span><span data-everyday-only>Hide personal details before saving</span><span data-specialist-only>Anonymize personal names, emails, IBANs &amp; phones (DSGVO)</span></span></label>
      <p class="text-xs text-[#738196] leading-relaxed">Extracts text into a Markdown guide inside your active Library folder.</p>
    </div>
  </div>
  <section id="upload-redaction-inspector" aria-label="Governance and redaction preview" class="hidden min-h-0 flex-1 max-h-[42vh] overflow-y-auto overscroll-contain p-4 rounded-xl border border-white/10 bg-[#04060F]"></section>
  <div class="shrink-0 flex items-center justify-between gap-2 pt-2 border-t border-[rgba(238,242,248,0.08)]">
    <span id="upload-status" role="status" aria-live="polite" class="text-xs text-[#4BB8E8] truncate"></span>
    <div class="flex items-center gap-2 shrink-0">
      <button id="cancel-upload-btn" type="button" class="px-3.5 py-1.5 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.12)] text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition">Cancel</button>
      <button id="confirm-upload-btn" type="button" class="px-4 py-1.5 rounded-xl bg-[#4BB8E8] text-[#04060F] font-semibold text-xs hover:brightness-110 transition">Upload &amp; Index</button>
    </div>
  </div>
</dialog>
<dialog id="move-guide-modal" closedby="any" aria-labelledby="move-guide-title" aria-describedby="move-guide-description" class="m-auto w-[calc(100%_-_2rem)] max-w-md max-h-[85vh] overflow-y-auto rounded-2xl border border-white/15 bg-[#0B1020] p-6 text-[#EEF2F8] shadow-2xl">
  <h2 id="move-guide-title" class="text-lg font-medium">Move guide</h2>
  <p id="move-guide-description" class="mt-2 mb-4 text-sm text-[#A0B0C8] break-words"></p>
  <form id="card-move-form" action="/api/guides/" method="post" class="flex flex-col gap-4">
    <div id="move-guide-fields"></div>
    <p id="card-move-status" role="status" class="text-xs text-[#A0B0C8]"></p>
    <div class="flex justify-end gap-2">
      <button type="submit" formmethod="dialog" formnovalidate value="cancel" class="rounded-lg border border-white/15 px-3 py-2 text-sm">Cancel</button>
      <button id="card-move-submit" type="submit" class="rounded-lg bg-[#4BB8E8] px-3 py-2 text-sm font-medium text-[#04060F]">Move guide</button>
    </div>
  </form>
</dialog>
{SETTINGS_HTML}
<dialog id="onboarding-modal" closedby="any" aria-labelledby="onboarding-modal-title" class="m-auto w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-2xl bg-[#0B1020] text-[#EEF2F8] border border-[rgba(238,242,248,0.16)] p-6 shadow-2xl">
  <div class="flex flex-col gap-4 text-left">
    <div class="flex items-center justify-between border-b border-[rgba(238,242,248,0.08)] pb-3"><div class="flex items-center gap-2"><img src="/static/logo-192.png" width="20" height="20" class="w-5 h-5" alt=""><h2 id="onboarding-modal-title" class="text-base font-medium text-[#EEF2F8]">Quick Setup Wizard</h2></div><button id="close-onboarding-modal" type="button" autofocus aria-label="Close setup wizard" class="h-7 w-7 rounded-full text-[#738196] hover:text-[#EEF2F8] hover:bg-white/[0.06] flex items-center justify-center text-sm">✕</button></div>
    {mode_cards("onboarding")}
    {INSTALLER_PANEL}
    <div class="flex flex-col gap-2 text-sm">
      <span class="text-xs uppercase tracking-wider text-[#738196] font-mono">1. AI Connection Check</span>
      <div id="onboarding-status-text" role="status" class="bg-[#04060F] border border-[rgba(238,242,248,0.08)] rounded-xl px-3.5 py-2 text-xs font-mono text-[#4BB8E8]">● Checking local Ollama &amp; retrieval engine...</div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        <label class="flex flex-col gap-1"><span class="text-xs text-[#A0B0C8]">Default Provider</span><select id="onboarding-provider" class="bg-[#04060F] border border-[rgba(238,242,248,0.12)] focus:border-[#4BB8E8] rounded-lg px-3 py-1.5 text-sm text-[#EEF2F8] outline-none cursor-pointer"><option value="ollama">Ollama Local</option><option value="openai">OpenAI</option><option value="gemini">Gemini</option><option value="kimi">Kimi</option><option value="deepseek">DeepSeek</option><option value="anthropic">Anthropic</option><option value="xai">xAI</option><option value="mistral">Mistral</option></select></label>
        <label class="flex flex-col gap-1"><span class="text-xs text-[#A0B0C8]">Model</span><select id="onboarding-model" aria-label="Setup AI Model" class="bg-[#04060F] border border-[rgba(238,242,248,0.12)] focus:border-[#4BB8E8] rounded-lg px-3 py-1.5 text-sm text-[#EEF2F8] outline-none cursor-pointer"></select></label>
      </div>
      <div id="onboarding-privacy-notice" role="status" class="text-xs text-[#738196]">Local execution — data stays on this device</div>
      <div id="onboarding-api-key-group" class="hidden flex-col gap-1"><label for="onboarding-api-key" id="onboarding-api-key-label" class="text-xs text-[#A0B0C8]">API Key (Saved on this computer)</label><div class="flex items-center gap-2"><input id="onboarding-api-key" type="password" autocomplete="off" placeholder="Saved securely on this computer" class="flex-1 bg-[#04060F] border border-[rgba(238,242,248,0.12)] focus:border-[#4BB8E8] rounded-lg px-3 py-1.5 text-sm text-[#EEF2F8] outline-none" /><button id="onboarding-save-key-btn" type="button" class="px-3 py-1.5 rounded-lg bg-[#04060F] border border-[rgba(238,242,248,0.12)] hover:border-[#4BB8E8] text-xs font-medium text-[#4BB8E8] shrink-0 transition">Save Key</button></div></div>
      <div id="onboarding-keys-bar" aria-label="Configured providers" class="flex flex-wrap gap-1.5"></div>
    </div>
    <div class="flex flex-col gap-2 pt-2 border-t border-[rgba(238,242,248,0.08)] text-sm">
      <div class="flex items-center justify-between"><span class="text-xs uppercase tracking-wider text-[#738196] font-mono">2. Workspace Identity &amp; Folder Creator</span><button id="onboarding-new-folder-btn" type="button" class="text-xs text-[#4BB8E8] hover:underline">+ New Folder</button></div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        <label class="flex flex-col gap-1"><span class="text-xs text-[#A0B0C8]">Workspace Title</span><input id="onboarding-title" type="text" value="My Knowledge Base" placeholder="e.g. Study Notes, Recipes, Work" class="bg-[#04060F] border border-[rgba(238,242,248,0.12)] focus:border-[#4BB8E8] rounded-lg px-3 py-1.5 text-sm text-[#EEF2F8] outline-none" /></label>
        <div class="flex flex-col gap-1"><label for="onboarding-folder-select" class="text-xs text-[#A0B0C8]">Knowledge Folder</label><select id="onboarding-folder-select" class="bg-[#04060F] border border-[rgba(238,242,248,0.12)] focus:border-[#4BB8E8] rounded-lg px-3 py-1.5 text-sm font-mono text-[#EEF2F8] outline-none cursor-pointer"><option value="knowledge_base">knowledge_base</option></select><input id="onboarding-folder" type="text" value="knowledge_base" placeholder="e.g. study_notes" class="hidden bg-[#04060F] border border-[rgba(238,242,248,0.12)] focus:border-[#4BB8E8] rounded-lg px-3 py-1.5 text-sm font-mono text-[#EEF2F8] outline-none" /><span id="onboarding-folder-helper" class="text-[11px] font-mono text-[#738196]">Saved locally in your library folder (knowledge_base/)</span></div>
      </div>
    </div>
    <div class="flex flex-col gap-2 pt-2 border-t border-[rgba(238,242,248,0.08)]">
      <span class="text-xs uppercase tracking-wider text-[#738196] font-mono">3. Ready to Launch</span>
      <div class="flex items-center justify-end gap-2.5 pt-1">
        <button id="onboarding-upload-btn" type="button" class="px-3.5 py-2 rounded-xl bg-[#04060F] border border-[#4BB8E8]/40 text-[#4BB8E8] hover:bg-[#4BB8E8]/10 text-xs font-medium transition">Upload First PDF / Word / MD Files</button>
        <button id="onboarding-start-btn" type="button" class="px-4 py-2 rounded-xl bg-[#4BB8E8] text-[#04060F] font-semibold text-xs hover:brightness-110 transition">Start Exploring</button>
      </div>
    </div>
  </div>
</dialog>"""
