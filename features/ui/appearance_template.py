"""Appearance customization panel and safe workspace settings reset controls."""

APPEARANCE_FIELDS = r"""    <div class="flex flex-col gap-3 text-sm">
      <div class="flex items-center justify-between gap-2"><span data-i18n="appearance_logo_title" class="text-xs uppercase tracking-wider text-[#738196] font-mono">Workspace Logo</span><button id="reset-logo-btn" type="button" hidden data-i18n="reset_logo" class="text-xs text-[#4BB8E8] hover:underline">Reset Logo</button></div>
      <div class="flex items-center gap-3 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] p-3.5">
        <img id="settings-logo-preview" src="/static/logo-512.png" width="40" height="40" class="w-10 h-10 rounded-lg object-cover shrink-0" alt="Workspace logo preview" />
        <div class="flex-1 min-w-0">
          <div data-i18n="appearance_logo_sub" class="text-sm font-medium text-[#EEF2F8]">Personalize Your Icon</div>
          <div id="logo-upload-status" role="status" data-i18n="logo_backup_note" class="text-xs text-[#A0B0C8] truncate">Original REALM logo is always kept as backup (PNG, JPG, WebP · max 2 MB)</div>
        </div>
        <input id="workspace-logo-input" type="file" accept="image/png,image/jpeg,image/webp" class="visually-hidden" />
        <label for="workspace-logo-input" data-i18n="change_logo" class="cursor-pointer px-3 py-1.5 rounded-lg bg-[#0B1020] border border-[rgba(238,242,248,0.12)] hover:border-[#4BB8E8] text-xs font-medium text-[#4BB8E8] shrink-0 transition">Change Logo</label>
      </div>
    </div>
    <div class="flex flex-col gap-3 pt-3 border-t border-[rgba(238,242,248,0.08)] text-sm">
      <div class="flex items-center justify-between gap-2"><span data-i18n="appearance_theme_title" class="text-xs uppercase tracking-wider text-[#738196] font-mono">Theme &amp; Colors</span><button id="reset-theme-btn" type="button" data-i18n="reset_colors" class="text-xs text-[#4BB8E8] hover:underline">Reset Colors</button></div>
      <div class="flex flex-col gap-1.5">
        <span data-i18n="theme_mode" class="text-xs text-[#A0B0C8]">Theme Mode</span>
        <div role="group" aria-label="Theme Mode" class="comfort-seg-3">
          <button type="button" data-theme-mode="system" aria-pressed="true" data-i18n="theme_system" class="py-1.5 px-2.5 rounded-lg text-xs font-medium transition bg-[#4BB8E8] text-[#04060F]">System</button>
          <button type="button" data-theme-mode="dark" aria-pressed="false" data-i18n="theme_dark" class="py-1.5 px-2.5 rounded-lg text-xs font-medium transition text-[#A0B0C8] hover:text-[#EEF2F8]">Dark</button>
          <button type="button" data-theme-mode="light" aria-pressed="false" data-i18n="theme_light" class="py-1.5 px-2.5 rounded-lg text-xs font-medium transition text-[#A0B0C8] hover:text-[#EEF2F8]">Light (Clear)</button>
        </div>
      </div>
      <label for="theme-fixed-toggle" class="flex items-center justify-between gap-3 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] px-4 py-3 cursor-pointer select-none">
        <span><span data-i18n="fixed_theme_title" class="block text-sm font-medium text-[#EEF2F8]">Fix Global Theme</span><span id="theme-fixed-hint" class="block text-xs text-[#A0B0C8] mt-0.5">Theme follows the active agent (Saga · Realm). Turn on to lock a global theme across all agents.</span></span>
        <input id="theme-fixed-toggle" type="checkbox" switch role="switch" class="shrink-0" />
      </label>
      <div id="theme-custom-controls" class="flex flex-col gap-3 transition-opacity theme-custom-locked">
        <div class="flex flex-col gap-1.5">
          <span data-i18n="starter_palettes" class="text-xs text-[#A0B0C8]">Color Palettes</span>
          <div id="theme-presets-bar" role="group" aria-label="Color palettes" class="flex flex-wrap gap-1.5"></div>
        </div>
        <div class="comfort-two-col">
          <label class="flex items-center justify-between gap-2 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] px-3.5 py-2.5 cursor-pointer">
            <span class="flex flex-col"><span data-i18n="primary_accent" class="text-sm text-[#EEF2F8]">Primary Accent</span><span id="theme-accent-hex" class="text-xs font-mono text-[#A0B0C8]">#4BB8E8</span></span>
            <input id="theme-accent-picker" type="color" value="#4BB8E8" disabled aria-label="Primary accent color" class="theme-swatch w-8 h-8 rounded-lg border-0 bg-transparent cursor-pointer shrink-0" />
          </label>
          <label class="flex items-center justify-between gap-2 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] px-3.5 py-2.5 cursor-pointer">
            <span class="flex flex-col"><span data-i18n="ambient_glow" class="text-sm text-[#EEF2F8]">Ambient Glow</span><span id="theme-glow-hex" class="text-xs font-mono text-[#A0B0C8]">#6366F1</span></span>
            <input id="theme-glow-picker" type="color" value="#6366F1" disabled aria-label="Secondary ambient glow color" class="theme-swatch w-8 h-8 rounded-lg border-0 bg-transparent cursor-pointer shrink-0" />
          </label>
        </div>
      </div>
      <label for="theme-ambient-toggle" class="flex items-center justify-between gap-3 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] px-4 py-3 cursor-pointer select-none">
        <span><span data-i18n="ambient_toggle" class="block text-sm font-medium text-[#EEF2F8]">Ambient Background</span><span data-i18n="ambient_desc" class="block text-xs text-[#A0B0C8] mt-0.5">Subtle animated light gradient and interactive dot grid.</span></span>
        <input id="theme-ambient-toggle" type="checkbox" switch role="switch" checked class="shrink-0" />
      </label>
    </div>
    <div class="flex flex-col gap-3 pt-3 border-t border-[rgba(238,242,248,0.08)] text-sm">
      <div class="flex items-center justify-between gap-2"><span data-i18n="a11y_section_title" class="text-xs uppercase tracking-wider text-[#738196] font-mono">Accessibility &amp; Reading Comfort</span></div>
      <div class="flex flex-col gap-1.5">
        <span data-i18n="a11y_font_lbl" class="text-xs text-[#A0B0C8]">Reading Font</span>
        <div role="group" aria-label="Reading Font" class="comfort-seg-3">
          <button type="button" data-reading-font="default" aria-pressed="true" data-i18n="a11y_font_default" class="py-1.5 px-2 rounded-lg text-xs font-medium transition bg-[#4BB8E8] text-[#04060F]">Default</button>
          <button type="button" data-reading-font="legible" aria-pressed="false" data-i18n="a11y_font_legible" class="py-1.5 px-2 rounded-lg text-xs font-medium transition text-[#A0B0C8] hover:text-[#EEF2F8]">Hyperlegible</button>
          <button type="button" data-reading-font="dyslexic" aria-pressed="false" data-i18n="a11y_font_dyslexic" class="py-1.5 px-2 rounded-lg text-xs font-medium transition text-[#A0B0C8] hover:text-[#EEF2F8]">Dyslexia</button>
        </div>
      </div>
      <div class="comfort-two-col">
        <div class="flex flex-col gap-1.5">
          <span data-i18n="a11y_size_lbl" class="text-xs text-[#A0B0C8]">Text Size</span>
          <div role="group" aria-label="Reading Text Size" class="comfort-seg-4">
            <button type="button" data-reading-scale="sm" aria-pressed="false" class="py-1.5 rounded-lg text-xs font-medium transition text-[#A0B0C8] hover:text-[#EEF2F8]">S</button>
            <button type="button" data-reading-scale="md" aria-pressed="true" class="py-1.5 rounded-lg text-xs font-medium transition bg-[#4BB8E8] text-[#04060F]">M</button>
            <button type="button" data-reading-scale="lg" aria-pressed="false" class="py-1.5 rounded-lg text-xs font-medium transition text-[#A0B0C8] hover:text-[#EEF2F8]">L</button>
            <button type="button" data-reading-scale="xl" aria-pressed="false" class="py-1.5 rounded-lg text-xs font-medium transition text-[#A0B0C8] hover:text-[#EEF2F8]">XL</button>
          </div>
        </div>
        <div class="flex flex-col gap-1.5">
          <span data-i18n="a11y_width_lbl" class="text-xs text-[#A0B0C8]">Reading Width</span>
          <div role="group" aria-label="Reading Line Width" class="comfort-seg-3">
            <button type="button" data-reading-width="narrow" aria-pressed="false" data-i18n="a11y_width_narrow" class="py-1.5 px-1.5 rounded-lg text-xs font-medium transition text-[#A0B0C8] hover:text-[#EEF2F8]">Focus</button>
            <button type="button" data-reading-width="standard" aria-pressed="true" data-i18n="a11y_width_std" class="py-1.5 px-1.5 rounded-lg text-xs font-medium transition bg-[#4BB8E8] text-[#04060F]">Normal</button>
            <button type="button" data-reading-width="wide" aria-pressed="false" data-i18n="a11y_width_wide" class="py-1.5 px-1.5 rounded-lg text-xs font-medium transition text-[#A0B0C8] hover:text-[#EEF2F8]">Wide</button>
          </div>
        </div>
      </div>
      <div class="comfort-preview-box"><p data-i18n="a11y_preview_sample" class="comfort-preview-sample">Preview: Answers and Library guides update live to match your reading size and font.</p></div>
      <label for="a11y-hc-focus-toggle" class="flex items-center justify-between gap-3 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] px-4 py-3 cursor-pointer select-none">
        <span><span data-i18n="a11y_hc_focus" class="block text-sm font-medium text-[#EEF2F8]">High-Contrast Focus &amp; Borders</span><span data-i18n="a11y_hc_focus_desc" class="block text-xs text-[#A0B0C8] mt-0.5">Stronger focus outlines and crisper card edges for keyboard navigation.</span></span>
        <input id="a11y-hc-focus-toggle" type="checkbox" switch role="switch" class="shrink-0" />
      </label>
      <label for="a11y-reduce-motion-toggle" class="flex items-center justify-between gap-3 rounded-xl bg-[#04060F] border border-[rgba(238,242,248,0.10)] px-4 py-3 cursor-pointer select-none">
        <span><span data-i18n="a11y_reduce_motion" class="block text-sm font-medium text-[#EEF2F8]">Reduce Motion</span><span data-i18n="a11y_reduce_motion_desc" class="block text-xs text-[#A0B0C8] mt-0.5">Calms 2D Graph physics, pauses ambient effects, and disables motion transitions.</span></span>
        <input id="a11y-reduce-motion-toggle" type="checkbox" switch role="switch" class="shrink-0" />
      </label>
      <div class="pt-2 border-t border-[rgba(238,242,248,0.08)] flex items-center justify-between gap-3">
        <span data-i18n="reset_appearance_note" class="text-xs text-[#738196]">Restore original REALM logo, System mode, and Realm palette.</span>
        <button id="reset-appearance-btn" type="button" data-i18n="reset_appearance" class="shrink-0 px-3 py-1.5 rounded-lg border border-[rgba(238,242,248,0.12)] hover:border-[#4BB8E8] text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition">Reset All Appearance</button>
      </div>
    </div>"""

RESET_ALL_PANEL = r"""<section class="rounded-xl border border-white/10 bg-[#04060F] p-4" aria-labelledby="reset-defaults-heading">
  <div class="flex items-center justify-between gap-3">
    <div>
      <h3 id="reset-defaults-heading" data-i18n="reset_defaults_title" class="text-sm font-medium text-[#EEF2F8]">Reset All Settings to REALM Defaults</h3>
      <p data-i18n="reset_defaults_desc" class="text-xs text-[#738196] mt-1">Restores default title, language, REALM logo, colors, local-only policy, budget caps, and search sliders. Your documents, folders, and chat history stay untouched.</p>
    </div>
    <button id="reset-all-settings-btn" type="button" data-i18n="reset_defaults_btn" class="shrink-0 rounded-lg border border-white/15 hover:border-[#4BB8E8] px-3 py-2 text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition">Reset Defaults</button>
  </div>
  <p id="reset-all-status" role="status" class="text-xs text-[#4BB8E8] mt-2"></p>
</section>"""
