"""Zero-jargon Built-in Private AI setup & control panel shared by Onboarding and Settings."""

from __future__ import annotations

_SHIELD_SVG = (
    '<svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
    'class="text-[#4BB8E8] shrink-0">'
    '<path d="M12 3l7 4v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V7l7-4Z"/>'
    '<path d="m9 12 2 2 4-4"/></svg>'
)


def builtin_ai_panel(prefix: str) -> str:
    """Render one accessible, jargon-free Built-in Private AI card for Onboarding or Settings."""
    picker_open = " open" if prefix == "settings" else ""
    return (
        f'<section id="{prefix}-lai-panel" data-lai-panel="{prefix}" aria-labelledby="{prefix}-lai-heading" '
        'class="rounded-xl border border-[#4BB8E8]/30 bg-[#04060F] p-4 flex flex-col gap-3 text-left">'
        '<div class="flex items-center justify-between gap-2 flex-wrap">'
        f'<div class="flex items-center gap-2 min-w-0">{_SHIELD_SVG}'
        f'<h3 id="{prefix}-lai-heading" data-i18n="lai_title" class="text-sm font-semibold text-[#EEF2F8]">Built-in Private AI</h3>'
        f'<span id="{prefix}-lai-offline-badge" hidden data-i18n="lai_offline_badge" '
        'class="px-2 py-0.5 rounded-full bg-[#38D399]/15 border border-[#38D399]/40 text-2xs font-mono font-semibold text-[#38D399]">100% Offline</span>'
        '</div>'
        f'<span id="{prefix}-lai-state-pill" class="text-2xs font-mono text-[#738196]"></span>'
        '</div>'
        '<p data-i18n="lai_desc" class="text-xs text-[#A0B0C8] leading-relaxed">'
        'Runs privately on your computer — no extra apps or API keys required.</p>'
        f'<p id="{prefix}-lai-fit-note" class="text-xs text-[#4BB8E8] leading-relaxed"></p>'
        f'<p id="{prefix}-lai-low-ram" hidden data-i18n="lai_low_ram_warn" '
        'class="text-xs text-amber-300 leading-relaxed rounded-lg border border-amber-400/25 bg-[#0B1020] px-3 py-2">'
        'This computer has limited memory, so local AI answers may feel slow. You can still try Ultra-Light, or use instant offline Search &amp; Privacy Shield with zero AI memory load.</p>'
        '<div class="flex items-center gap-2 flex-wrap">'
        f'<button id="{prefix}-lai-setup-btn" type="button" data-lai-setup-btn="{prefix}" data-i18n="lai_setup_btn" '
        'class="px-4 py-2 rounded-xl bg-[#4BB8E8] text-[#04060F] text-xs font-semibold hover:brightness-110 shrink-0 transition">Set Up Private AI</button>'
        '</div>'
        f'<details id="{prefix}-lai-size-details"{picker_open} class="flex flex-col gap-2">'
        '<summary data-i18n="lai_customize_size" class="text-xs text-[#A0B0C8] hover:text-[#EEF2F8] cursor-pointer select-none">Choose another size</summary>'
        '<div class="pt-2 flex flex-col gap-1">'
        f'<label for="{prefix}-lai-tier-select" data-i18n="lai_tier_lbl" class="text-xs text-[#A0B0C8]">Private AI Size</label>'
        f'<select id="{prefix}-lai-tier-select" data-lai-tier-select="{prefix}" '
        'class="w-full rounded-lg bg-[#0B1020] border border-[rgba(238,242,248,0.14)] focus:border-[#4BB8E8] px-3 py-1.5 text-sm text-[#EEF2F8] outline-none cursor-pointer"></select>'
        '</div></details>'
        f'<div id="{prefix}-lai-progress-box" hidden class="rounded-xl bg-[#0B1020] border border-[#4BB8E8]/35 px-3.5 py-2.5 flex flex-col gap-2">'
        '<div class="flex items-center justify-between gap-2 text-xs">'
        f'<span id="{prefix}-lai-progress-stage" class="text-[#EEF2F8] font-medium truncate"></span>'
        f'<span id="{prefix}-lai-progress-meta" class="font-mono text-[#4BB8E8] shrink-0"></span>'
        '</div>'
        '<div class="w-full h-2 rounded-full bg-white/10 overflow-hidden">'
        f'<div id="{prefix}-lai-progress-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" '
        'aria-label="Private AI setup progress" data-i18n-aria-label="lai_prog_aria" '
        'class="h-full rounded-full bg-[#4BB8E8] transition-all duration-200" style="width:0%"></div>'
        '</div>'
        '<div class="flex justify-end">'
        f'<button id="{prefix}-lai-cancel-btn" type="button" data-lai-cancel-btn="{prefix}" data-i18n="cancel" '
        'class="px-3 py-1 rounded-lg border border-white/15 text-xs text-[#A0B0C8] hover:text-[#EEF2F8] transition">Cancel</button>'
        '</div></div>'
        f'<div id="{prefix}-lai-controls-box" hidden class="flex flex-col gap-2.5 pt-2 border-t border-[rgba(238,242,248,0.08)]">'
        '<div class="flex items-center justify-between gap-2 flex-wrap">'
        '<span data-i18n="lai_profile_lbl" class="text-xs text-[#A0B0C8]">Fan &amp; Battery Mode</span>'
        '<div role="group" aria-label="Fan and battery profile" data-i18n-aria-label="lai_profile_lbl" '
        'class="inline-flex gap-1 bg-[#0B1020] p-1 rounded-xl border border-[rgba(238,242,248,0.10)]">'
        f'<button type="button" data-lai-profile="eco" aria-pressed="true" data-i18n="lai_prof_eco" '
        'class="px-3 py-1 rounded-lg text-xs font-medium transition bg-[#4BB8E8] text-[#04060F]">Quiet / Eco</button>'
        f'<button type="button" data-lai-profile="performance" aria-pressed="false" data-i18n="lai_prof_perf" '
        'class="px-3 py-1 rounded-lg text-xs font-medium transition text-[#A0B0C8] hover:text-[#EEF2F8]">Performance</button>'
        '</div></div>'
        f'<p id="{prefix}-lai-profile-note" class="text-xs text-[#738196]"></p>'
        '<div class="flex items-center justify-between gap-2 flex-wrap">'
        f'<button type="button" data-lai-sleep-btn="{prefix}" data-i18n="lai_sleep_btn" '
        'class="px-3 py-1.5 rounded-lg border border-white/15 text-xs text-[#A0B0C8] hover:text-[#EEF2F8] hover:border-[#4BB8E8] transition">Sleep Now (Free RAM)</button>'
        f'<button type="button" data-lai-remove-btn="{prefix}" '
        'class="px-3 py-1.5 rounded-lg border border-[#EF4444]/40 text-xs text-[#FCA5A5] hover:border-[#EF4444] transition">Remove Local AI</button>'
        '</div></div>'
        f'<p id="{prefix}-lai-status" role="status" aria-live="polite" class="text-xs text-[#A0B0C8]"></p>'
        '</section>'
    )


BUILTIN_AI_SETTINGS_PANEL: str = builtin_ai_panel("settings")
BUILTIN_AI_ONBOARDING_PANEL: str = builtin_ai_panel("onboarding")
