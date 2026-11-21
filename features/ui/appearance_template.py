"""Appearance customization panel and safe workspace settings reset controls."""

APPEARANCE_FIELDS = r"""    <div class="flex flex-col gap-3 text-sm">
      <div class="flex items-center justify-between gap-2"><span data-i18n="agent_name_title" class="text-xs uppercase tracking-wider text-[#738196] font-mono">Name Your Agent</span><button id="reset-agent-name-btn" type="button" hidden data-i18n="reset_agent_name" class="text-xs text-[#4BB8E8] hover:underline">Reset to Saga</button></div>
      <div class="flex flex-col gap-1.5 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] p-3">
        <label for="agent-name-input" data-i18n="agent_name_label" class="text-xs font-medium text-[#EEF2F8]">Agent Display Name</label>
        <input id="agent-name-input" type="text" maxlength="40" value="Saga" placeholder="Saga" class="bg-[#0B1020] border border-[rgba(238,242,248,0.12)] focus:border-[#4BB8E8] rounded-lg px-3 py-1.5 text-sm text-[#EEF2F8] outline-none" />
        <span data-i18n="agent_name_desc" class="text-[11px] text-[#738196]">Shown on every AI reply and exported note (default: Saga — the face of REALM).</span>
      </div>
    </div>
    <div class="flex flex-col gap-3 pt-3 border-t border-[rgba(238,242,248,0.08)] text-sm">
      <div class="flex items-center justify-between gap-2"><span data-i18n="appearance_logo_title" class="text-xs uppercase tracking-wider text-[#738196] font-mono">Workspace Logo</span><button id="reset-logo-btn" type="button" hidden data-i18n="reset_logo" class="text-xs text-[#4BB8E8] hover:underline">Reset Logo</button></div>
      <div class="flex items-center gap-3 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] p-3">
        <img id="settings-logo-preview" src="/static/logo-512.png" width="40" height="40" class="w-10 h-10 rounded-lg object-cover shrink-0" alt="Workspace logo preview" />
        <div class="flex-1 min-w-0">
          <div data-i18n="appearance_logo_sub" class="text-xs font-medium text-[#EEF2F8]">Personalize Your Icon</div>
          <div id="logo-upload-status" role="status" class="text-[11px] text-[#738196] truncate">Original REALM logo is always kept as backup (PNG, JPG, WebP · max 2 MB)</div>
        </div>
        <input id="workspace-logo-input" type="file" accept="image/png,image/jpeg,image/webp" class="visually-hidden" />
        <label for="workspace-logo-input" data-i18n="change_logo" class="cursor-pointer px-3 py-1.5 rounded-lg bg-[#0B1020] border border-[rgba(238,242,248,0.12)] hover:border-[#4BB8E8] text-xs font-medium text-[#4BB8E8] shrink-0 transition">Change Logo</label>
      </div>
    </div>
    <div class="flex flex-col gap-3 pt-3 border-t border-[rgba(238,242,248,0.08)] text-sm">
      <div class="flex items-center justify-between gap-2"><span data-i18n="appearance_theme_title" class="text-xs uppercase tracking-wider text-[#738196] font-mono">Theme &amp; Futuristic Colors</span><button id="reset-theme-btn" type="button" data-i18n="reset_colors" class="text-xs text-[#4BB8E8] hover:underline">Reset Colors</button></div>
      <div class="flex flex-col gap-1.5">
        <span data-i18n="theme_mode" class="text-xs text-[#A0B0C8]">Theme Mode</span>
        <div role="group" aria-label="Theme Mode" class="grid grid-cols-3 gap-1.5 bg-[#04060F] p-1 rounded-xl border border-[rgba(238,242,248,0.10)]">
          <button type="button" data-theme-mode="system" aria-pressed="true" class="py-1.5 px-2.5 rounded-lg text-xs font-medium transition bg-[#4BB8E8] text-[#04060F]">System</button>
          <button type="button" data-theme-mode="dark" aria-pressed="false" data-i18n="theme_dark" class="py-1.5 px-2.5 rounded-lg text-xs font-medium transition text-[#A0B0C8] hover:text-[#EEF2F8]">Dark</button>
          <button type="button" data-theme-mode="light" aria-pressed="false" data-i18n="theme_light" class="py-1.5 px-2.5 rounded-lg text-xs font-medium transition text-[#A0B0C8] hover:text-[#EEF2F8]">Light (Clear)</button>
        </div>
      </div>
      <div class="flex flex-col gap-1.5">
        <span data-i18n="starter_palettes" class="text-xs text-[#A0B0C8]">Futuristic Starter Palettes</span>
        <div id="theme-presets-bar" role="group" aria-label="Starter color palettes" class="flex flex-wrap gap-1.5"></div>
      </div>
      <div class="grid grid-cols-2 gap-2.5">
        <label class="flex items-center justify-between gap-2 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] px-3 py-2 cursor-pointer">
          <span class="flex flex-col"><span data-i18n="primary_accent" class="text-xs text-[#EEF2F8]">Primary Accent</span><span id="theme-accent-hex" class="text-[11px] font-mono text-[#738196]">#4BB8E8</span></span>
          <input id="theme-accent-picker" type="color" value="#4BB8E8" aria-label="Primary accent color" class="theme-swatch w-8 h-8 rounded-lg border-0 bg-transparent cursor-pointer shrink-0" />
        </label>
        <label class="flex items-center justify-between gap-2 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] px-3 py-2 cursor-pointer">
          <span class="flex flex-col"><span data-i18n="ambient_glow" class="text-xs text-[#EEF2F8]">Ambient Glow</span><span id="theme-glow-hex" class="text-[11px] font-mono text-[#738196]">#6366F1</span></span>
          <input id="theme-glow-picker" type="color" value="#6366F1" aria-label="Secondary ambient glow color" class="theme-swatch w-8 h-8 rounded-lg border-0 bg-transparent cursor-pointer shrink-0" />
        </label>
      </div>
      <label for="theme-ambient-toggle" class="flex items-center justify-between gap-3 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] px-3.5 py-2.5 cursor-pointer select-none">
        <span><span data-i18n="ambient_toggle" class="block text-xs font-medium text-[#EEF2F8]">Supernova &amp; Interactive Dots</span><span data-i18n="ambient_desc" class="block text-[11px] text-[#738196] mt-0.5">Sweeping cosmic glow and magnetic dot grid that reacts to your cursor.</span></span>
        <input id="theme-ambient-toggle" type="checkbox" switch checked class="shrink-0" />
      </label>
      <div class="pt-2 border-t border-[rgba(238,242,248,0.08)] flex items-center justify-between gap-3">
        <span class="text-xs text-[#738196]">Restore Saga, original REALM logo, System mode, and Realm palette.</span>
        <button id="reset-appearance-btn" type="button" data-i18n="reset_appearance" class="shrink-0 px-3 py-1.5 rounded-lg border border-[rgba(238,242,248,0.12)] hover:border-[#4BB8E8] text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition">Reset All Appearance</button>
      </div>
    </div>"""

RESET_ALL_PANEL = r"""<section class="rounded-xl border border-white/10 bg-[#04060F] p-4" aria-labelledby="reset-defaults-heading">
  <div class="flex items-center justify-between gap-3">
    <div>
      <h3 id="reset-defaults-heading" data-i18n="reset_defaults_title" class="text-sm font-medium text-[#EEF2F8]">Reset All Settings to REALM Defaults</h3>
      <p class="text-xs text-[#738196] mt-1">Restores default title, language, REALM logo, colors, local-only policy, budget caps, and search sliders. Your documents, folders, and chat history stay untouched.</p>
    </div>
    <button id="reset-all-settings-btn" type="button" data-i18n="reset_defaults_btn" class="shrink-0 rounded-lg border border-white/15 hover:border-[#4BB8E8] px-3 py-2 text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition">Reset Defaults</button>
  </div>
  <p id="reset-all-status" role="status" class="text-xs text-[#4BB8E8] mt-2"></p>
</section>"""
