"""Native <dialog> for the REALM Agent Team (persona.md roster, editor & custom agent builder)."""

AGENT_MODAL_HTML: str = r"""<dialog id="agent-studio-modal" closedby="any" aria-labelledby="agent-studio-title" class="m-auto w-full max-w-3xl max-h-[88vh] overflow-hidden flex-col gap-4 rounded-2xl bg-[#0B1020] text-[#EEF2F8] border border-[rgba(238,242,248,0.16)] p-6 shadow-2xl">
  <div class="shrink-0 flex items-center justify-between gap-3 border-b border-[rgba(238,242,248,0.08)] pb-3">
    <div class="flex flex-col gap-0.5 min-w-0">
      <h2 id="agent-studio-title" data-i18n="agents_title" class="text-lg font-semibold text-[#EEF2F8]">Agent Team</h2>
      <p data-i18n="agents_sub" class="text-xs text-[#A0B0C8]">Switch your active analytical lens anytime — even mid-chat — or customize and create agents.</p>
    </div>
    <div class="flex items-center gap-2 shrink-0">
      <button id="reveal-agents-folder-btn" type="button" data-i18n="agents_show_folder" class="px-2.5 py-1.5 rounded-lg bg-[#04060F] border border-white/15 hover:border-[#4BB8E8] text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition">Show Folder</button>
      <button id="close-agent-studio-modal" type="button" aria-label="Close Agent Studio" class="h-8 w-8 rounded-full text-[#738196] hover:text-[#EEF2F8] hover:bg-white/[0.06] flex items-center justify-center text-sm">✕</button>
    </div>
  </div>
  <div class="shrink-0 flex items-center justify-between gap-3 flex-wrap">
    <div role="tablist" aria-label="Agent Studio sections" class="inline-flex bg-[#04060F] p-1 rounded-xl border border-white/10 gap-1 overflow-x-auto">
      <button id="agent-tab-roster" type="button" role="tab" aria-selected="true" tabindex="0" data-i18n="agents_tab_list" class="px-3.5 py-1.5 rounded-lg text-xs font-medium bg-[#4BB8E8] text-[#04060F] shrink-0 transition">Your Agents</button>
      <button id="agent-tab-builder" type="button" role="tab" aria-selected="false" tabindex="-1" data-i18n="agents_tab_builder" class="px-3.5 py-1.5 rounded-lg text-xs font-medium text-[#A0B0C8] hover:text-[#EEF2F8] shrink-0 transition">✦ Build with Chat</button>
      <button id="agent-tab-editor" type="button" role="tab" aria-selected="false" tabindex="-1" data-i18n="agents_tab_create" class="px-3.5 py-1.5 rounded-lg text-xs font-medium text-[#A0B0C8] hover:text-[#EEF2F8] shrink-0 transition">+ Create Agent</button>
    </div>
    <div class="flex items-center gap-3 flex-wrap">
      <button id="restore-agents-btn" type="button" hidden data-i18n="agents_restore_defaults" class="text-xs text-[#4BB8E8] hover:underline">Restore Default Team</button>
    </div>
  </div>
  <div id="agent-roster-pane" role="tabpanel" aria-labelledby="agent-tab-roster" class="min-h-0 flex-1 overflow-y-auto overscroll-contain flex flex-col gap-3 pr-1">
    <div id="agent-cards-grid" class="grid grid-cols-1 sm:grid-cols-2 gap-3 pb-2"></div>
  </div>
  <section id="agent-builder-pane" role="tabpanel" aria-labelledby="agent-tab-builder" hidden class="min-h-0 flex-1 flex flex-col gap-3 overflow-hidden">
    <div id="agent-builder-messages" class="min-h-0 flex-1 overflow-y-auto overscroll-contain flex flex-col gap-2.5 pr-1"></div>
    <div id="agent-builder-preview" hidden class="shrink-0 rounded-xl bg-[#04060F] border border-[#4BB8E8]/40 p-3.5 flex flex-col gap-2"></div>
    <form id="agent-builder-form" class="shrink-0 flex flex-col gap-2 pt-2 border-t border-white/10">
      <div class="flex items-end gap-2">
        <textarea id="agent-builder-input" rows="2" maxlength="2000" aria-label="Describe your custom agent" data-i18n-placeholder="ab_placeholder" placeholder="Describe what this agent should do for you…" class="flex-1 rounded-xl bg-[#04060F] border border-white/15 focus:border-[#4BB8E8] px-3 py-2 text-sm text-[#EEF2F8] outline-none resize-none"></textarea>
        <button id="ab-send-btn" type="submit" data-i18n="ab_send" class="px-4 py-2 rounded-xl bg-[#4BB8E8] text-[#04060F] font-semibold text-xs hover:brightness-110 shrink-0 transition">Send</button>
      </div>
      <div class="flex items-center justify-between gap-2 flex-wrap">
        <span id="agent-builder-status" role="status" class="text-xs text-amber-300"></span>
        <div class="flex items-center gap-2">
          <button id="ab-reset-btn" type="button" data-i18n="ab_restart" class="px-2.5 py-1 rounded-lg border border-white/15 text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition">Restart</button>
          <button id="ab-draft-btn" type="button" disabled data-i18n="ab_draft_now" class="px-3 py-1 rounded-lg bg-[#4BB8E8]/15 border border-[#4BB8E8]/40 text-xs font-medium text-[#4BB8E8] hover:bg-[#4BB8E8]/25 disabled:opacity-40 transition">Draft Now</button>
        </div>
      </div>
    </form>
  </section>
  <form id="agent-editor-form" role="tabpanel" aria-labelledby="agent-tab-editor" hidden class="min-h-0 flex-1 overflow-y-auto overscroll-contain flex flex-col gap-3 pr-1">
    <input id="agent-edit-id" type="hidden" value="" />
    <div class="flex items-center justify-between gap-2 flex-wrap">
      <span id="agent-editor-heading" data-i18n="agents_new_heading" class="text-xs font-mono uppercase tracking-wider text-[#4BB8E8]">New Custom Agent</span>
      <div role="group" aria-label="Editor mode" class="inline-flex bg-[#04060F] p-0.5 rounded-lg border border-white/10 gap-1">
        <button id="agent-mode-guided-btn" type="button" aria-pressed="true" data-i18n="agents_mode_guided" class="px-2.5 py-1 rounded-md text-xs font-medium bg-[#4BB8E8] text-[#04060F] transition">Guided</button>
        <button id="agent-mode-raw-btn" type="button" aria-pressed="false" data-i18n="agents_mode_raw" class="px-2.5 py-1 rounded-md text-xs font-medium text-[#A0B0C8] hover:text-[#EEF2F8] transition">Raw persona.md</button>
      </div>
    </div>
    <div id="agent-guided-pane" class="flex flex-col gap-3">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <label class="flex flex-col gap-1"><span data-i18n="agents_ed_name" class="text-xs text-[#A0B0C8]">Agent Name</span><input id="agent-ed-name" type="text" maxlength="40" placeholder="e.g. IREB Examiner" class="w-full rounded-xl bg-[#04060F] border border-white/15 px-3 py-2 text-sm" /></label>
        <label class="flex flex-col gap-1"><span data-i18n="agents_ed_role" class="text-xs text-[#A0B0C8]">Role / Craft</span><input id="agent-ed-role" type="text" maxlength="64" placeholder="e.g. Requirements Reviewer" class="w-full rounded-xl bg-[#04060F] border border-white/15 px-3 py-2 text-sm" /></label>
      </div>
      <label class="flex flex-col gap-1"><span data-i18n="agents_ed_tagline" class="text-xs text-[#A0B0C8]">Tagline (1-sentence superpower)</span><input id="agent-ed-tagline" type="text" maxlength="160" placeholder="What analytical lens this agent brings to every answer" class="w-full rounded-xl bg-[#04060F] border border-white/15 px-3 py-2 text-sm" /></label>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <label class="flex flex-col gap-1"><span data-i18n="agents_ed_palette" class="text-xs text-[#A0B0C8]">Palette</span><select id="agent-ed-palette" class="w-full rounded-xl bg-[#04060F] border border-white/15 px-3 py-2 text-sm"></select></label>
        <label class="flex flex-col gap-1"><span data-i18n="agents_ed_format" class="text-xs text-[#A0B0C8]">Default Format (Optional)</span><select id="agent-ed-format" class="w-full rounded-xl bg-[#04060F] border border-white/15 px-3 py-2 text-sm"></select></label>
        <label class="flex flex-col gap-1"><span data-i18n="agents_ed_temp" class="text-xs text-[#A0B0C8]">Temperature (0.0 – 1.0)</span><input id="agent-ed-temp" type="number" min="0" max="1" step="0.05" value="0.2" class="w-full rounded-xl bg-[#04060F] border border-white/15 px-3 py-2 text-sm font-mono" /></label>
      </div>
      <div class="flex flex-col gap-1.5 rounded-xl bg-[#04060F] border border-white/10 p-3">
        <div class="comfort-two-col">
          <label class="flex flex-col gap-1"><span data-i18n="agents_ed_provider" class="text-xs text-[#A0B0C8]">Pinned Provider (Optional)</span><select id="agent-ed-provider" class="w-full rounded-xl bg-[#0B1020] border border-white/15 px-3 py-2 text-sm"></select></label>
          <label class="flex flex-col gap-1"><span data-i18n="agents_ed_model" class="text-xs text-[#A0B0C8]">Pinned Model (Optional)</span><select id="agent-ed-model" disabled class="w-full rounded-xl bg-[#0B1020] border border-white/15 px-3 py-2 text-sm disabled:opacity-50"></select></label>
        </div>
        <p data-i18n="agents_ed_model_hint" class="text-xs text-[#738196]">Leave on default to follow the prompt bar. Mixing 1 local Ollama model + cloud models uses zero extra RAM; switching between two local models auto-unloads the previous one.</p>
      </div>
      <label class="flex flex-col gap-1"><span data-i18n="agents_ed_body" class="text-xs text-[#A0B0C8]">Analytical Lens, Signature Moves, Style &amp; Boundaries</span><textarea id="agent-ed-instructions" rows="7" maxlength="3000" placeholder="## Analytical Lens&#10;What this agent checks, questions, and prioritizes.&#10;&#10;## Signature Moves&#10;- Specific habits (e.g., flag contradictions, end with 2 sharp questions).&#10;&#10;## Communication Style&#10;Tone, cadence, and structure.&#10;&#10;## Boundaries&#10;What this agent never does." class="w-full rounded-xl bg-[#04060F] border border-white/15 px-3 py-2 text-sm font-mono text-[#EEF2F8] outline-none focus:border-[#4BB8E8]"></textarea></label>
    </div>
    <div id="agent-raw-pane" hidden class="flex flex-col gap-1.5">
      <label for="agent-ed-raw" data-i18n="agents_ed_raw_lbl" class="text-xs text-[#A0B0C8]">Direct persona.md source (YAML frontmatter + Markdown)</label>
      <textarea id="agent-ed-raw" rows="13" maxlength="4500" class="w-full rounded-xl bg-[#04060F] border border-white/15 px-3 py-2.5 text-xs font-mono text-[#EEF2F8] leading-relaxed outline-none focus:border-[#4BB8E8]"></textarea>
    </div>
    <div class="flex items-center justify-between gap-2 pt-2">
      <span id="agent-ed-status" role="status" class="text-xs text-[#4BB8E8]"></span>
      <div class="flex items-center gap-2">
        <button id="agent-ed-cancel-btn" type="button" data-i18n="cancel" class="px-3.5 py-2 rounded-xl border border-white/15 text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition">Cancel</button>
        <button id="agent-ed-save-btn" type="submit" data-i18n="agents_ed_save" class="px-4 py-2 rounded-xl bg-[#4BB8E8] text-[#04060F] font-semibold text-xs hover:brightness-110 transition">Save Agent</button>
      </div>
    </div>
  </form>
</dialog>"""
