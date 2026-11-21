"""Adaptive Dark/Light/System, dual-tone palette tokens, and Supernova ambient backdrop CSS."""

THEME_BRIDGE_CSS: str = r"""<style id="realm-theme-bridge">
:root {
  color-scheme: light dark;
  --accent-seed: #4BB8E8;
  --accent-glow: #6366F1;
  --bg-dark: color-mix(in oklab, #04060F 93%, var(--accent-seed));
  --surface-dark: color-mix(in oklab, #0B1020 90%, var(--accent-seed));
  --surface-soft-dark: color-mix(in oklab, #141C33 86%, var(--accent-seed));
  --accent-dark: var(--accent-seed);
  --border-dark: color-mix(in oklab, rgba(238, 242, 248, 0.16) 78%, var(--accent-seed));
  --border-subtle-dark: color-mix(in oklab, rgba(238, 242, 248, 0.08) 84%, var(--accent-seed));
  --aura-a-dark: color-mix(in oklab, var(--accent-seed) 46%, transparent);
  --aura-b-dark: color-mix(in oklab, var(--accent-glow) 52%, transparent);
  --aura-core-dark: color-mix(in oklab, white 26%, var(--accent-seed));
  --hover-tint-dark: rgba(238, 242, 248, 0.06);
  --shadow-dark: 0 22px 48px rgba(0, 0, 0, 0.45);
  --bg-light: color-mix(in oklab, #F3F7FC 92%, var(--accent-seed));
  --surface-light: color-mix(in oklab, #FFFFFF 96%, var(--accent-seed));
  --surface-soft-light: color-mix(in oklab, #E8F0FA 88%, var(--accent-seed));
  --accent-light: color-mix(in oklab, var(--accent-seed) 76%, #04060F);
  --border-light: color-mix(in oklab, rgba(11, 16, 32, 0.15) 80%, var(--accent-seed));
  --border-subtle-light: color-mix(in oklab, rgba(11, 16, 32, 0.09) 84%, var(--accent-seed));
  --aura-a-light: color-mix(in oklab, var(--accent-seed) 28%, transparent);
  --aura-b-light: color-mix(in oklab, var(--accent-glow) 26%, transparent);
  --aura-core-light: color-mix(in oklab, var(--accent-seed) 40%, white);
  --hover-tint-light: rgba(11, 16, 32, 0.05);
  --shadow-light: 0 18px 40px rgba(15, 23, 42, 0.12);
  --background: var(--bg-light); --surface-raised: var(--surface-light); --surface-soft: var(--surface-soft-light);
  --text: #0B1020; --text-muted: #475569; --text-subtle: #64748B; --accent: var(--accent-light);
  --border: var(--border-light); --border-subtle: var(--border-subtle-light);
  --aura-a: var(--aura-a-light); --aura-b: var(--aura-b-light); --aura-core: var(--aura-core-light);
  --hover-tint: var(--hover-tint-light); --dialog-shadow: var(--shadow-light);
  --scrollbar-thumb: #64748B; --scrollbar-track: var(--surface-light); --text-on-accent: #04060F;
}
:root:has(> head > meta[name="color-scheme"][content="dark"]) { color-scheme: dark; }
:root:has(> head > meta[name="color-scheme"][content="light"]) { color-scheme: light; }
@media (prefers-color-scheme: dark) {
  :root {
    --background: var(--bg-dark); --surface-raised: var(--surface-dark); --surface-soft: var(--surface-soft-dark);
    --text: #EEF2F8; --text-muted: #A0B0C8; --text-subtle: #738196; --accent: var(--accent-dark);
    --border: var(--border-dark); --border-subtle: var(--border-subtle-dark);
    --aura-a: var(--aura-a-dark); --aura-b: var(--aura-b-dark); --aura-core: var(--aura-core-dark);
    --hover-tint: var(--hover-tint-dark); --dialog-shadow: var(--shadow-dark);
    --scrollbar-thumb: #738196; --scrollbar-track: var(--surface-dark);
  }
}
@supports (color: light-dark(white, black)) {
  :root {
    --background: light-dark(var(--bg-light), var(--bg-dark)); --surface-raised: light-dark(var(--surface-light), var(--surface-dark));
    --surface-soft: light-dark(var(--surface-soft-light), var(--surface-soft-dark));
    --text: light-dark(#0B1020, #EEF2F8); --text-muted: light-dark(#475569, #A0B0C8); --text-subtle: light-dark(#64748B, #738196);
    --accent: light-dark(var(--accent-light), var(--accent-dark));
    --border: light-dark(var(--border-light), var(--border-dark)); --border-subtle: light-dark(var(--border-subtle-light), var(--border-subtle-dark));
    --aura-a: light-dark(var(--aura-a-light), var(--aura-a-dark)); --aura-b: light-dark(var(--aura-b-light), var(--aura-b-dark)); --aura-core: light-dark(var(--aura-core-light), var(--aura-core-dark));
    --hover-tint: light-dark(var(--hover-tint-light), var(--hover-tint-dark)); --dialog-shadow: light-dark(var(--shadow-light), var(--shadow-dark));
    --scrollbar-thumb: light-dark(#64748B, #738196); --scrollbar-track: light-dark(var(--surface-light), var(--surface-dark));
  }
}
@supports (color: color(from red xyz-d65 0 0 0)) {
  :root { --text-on-accent: color(from var(--accent) xyz-d65 calc(max(0, sign(0.17913 - y)) * 0.9505) max(0, sign(0.17913 - y)) calc(max(0, sign(0.17913 - y)) * 1.089)); }
}
@supports (color: contrast-color(red)) { :root { --text-on-accent: contrast-color(var(--accent)); } }
html, body { background-color: var(--background) !important; color: var(--text) !important; accent-color: var(--accent); }
#main-shell { background-color: var(--background) !important; background-image: none !important; }
.ambient-stage { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; content-visibility: auto; contain-intrinsic-size: auto 100vw auto 100vh; transition: opacity 0.45s ease; }
.ambient-stage.is-dimmed { opacity: 0.22; }
.ambient-stage.is-dimmed.is-speaking { opacity: 0.44; }
.ambient-stage.is-off { display: none; }
.stream-cursor { display: inline-block; width: 0.5rem; height: 1.05em; margin-inline-start: 0.2rem; vertical-align: -0.15em; border-radius: 2px; background: var(--accent); opacity: 0.85; }
@media (prefers-reduced-motion: no-preference) { .stream-cursor { animation: realm-caret 0.9s steps(2, start) infinite; } }
@keyframes realm-caret { to { opacity: 0.15; } }
#global-drop-overlay { background: color-mix(in oklab, var(--background) 74%, transparent); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); }
#ambient-aurora-canvas { position: absolute; inset: -6%; width: 112%; height: 112%; display: block; filter: blur(22px); opacity: 0.94; transform: translateZ(0); }
#ambient-dots-canvas { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
#hero-logo { border-radius: 0.875rem; object-fit: cover; filter: drop-shadow(0 0 18px color-mix(in oklab, var(--accent) 42%, transparent)); }
#hero-greeting-text { text-shadow: 0 2px 24px color-mix(in oklab, var(--background) 85%, transparent); }
#seed-chips { position: relative; padding-inline-start: 0.5rem; gap: 0.5rem; }
#seed-list { gap: 0.5rem; }
#seed-chips .seed-chip { padding: 0.42rem 0.92rem; border-radius: 9999px; background: color-mix(in oklab, var(--surface-raised) 84%, transparent); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid var(--border-subtle); color: color-mix(in oklab, var(--text) 94%, transparent) !important; box-shadow: 0 4px 16px color-mix(in oklab, var(--background) 44%, transparent); transition: background-color 0.18s ease, border-color 0.18s ease, color 0.18s ease; }
#seed-chips .seed-chip:hover { background: color-mix(in oklab, var(--surface-raised) 94%, transparent); border-color: color-mix(in oklab, var(--accent) 55%, var(--border)); color: var(--text) !important; }
#more-ideas-btn, #home-browse-btn { padding: 0.3rem 0.78rem; border-radius: 9999px; background: color-mix(in oklab, var(--surface-raised) 82%, transparent); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); border: 1px solid var(--border-subtle); color: color-mix(in oklab, var(--text) 88%, transparent) !important; transition: background-color 0.18s ease, border-color 0.18s ease, color 0.18s ease; }
#more-ideas-btn:hover, #home-browse-btn:hover { background: color-mix(in oklab, var(--surface-raised) 90%, transparent); border-color: var(--border); color: var(--text) !important; }
#sidebar { background-color: var(--surface-raised) !important; box-shadow: 1px 0 0 var(--border-subtle) !important; }
#prompt-container { background-color: color-mix(in oklab, var(--surface-raised) 86%, transparent) !important; backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); box-shadow: inset 0 0 0 1px var(--border), var(--dialog-shadow) !important; }
#prompt-container:focus-within { box-shadow: inset 0 0 0 1.5px var(--accent), 0 0 28px color-mix(in oklab, var(--accent) 26%, transparent) !important; }
.chat-dock { background: transparent !important; }
.chat-dock #prompt-container { background-color: color-mix(in oklab, var(--surface-raised) 92%, transparent) !important; }
.chat-scroll-mask { -webkit-mask-image: linear-gradient(to bottom, #000 calc(100% - 28px), transparent 100%); mask-image: linear-gradient(to bottom, #000 calc(100% - 28px), transparent 100%); }
dialog { background-color: var(--surface-raised) !important; color: var(--text) !important; border-color: var(--border) !important; box-shadow: var(--dialog-shadow) !important; }
dialog::backdrop { background: light-dark(rgba(11, 16, 32, 0.28), rgba(4, 6, 15, 0.54)) !important; }
#onboarding-modal [hidden], #reset-logo-btn[hidden], #reset-agent-name-btn[hidden], #global-drop-overlay[hidden], #web-search-options [hidden], #web-search-lock-note[hidden] { display: none !important; }
.settings-body { --scrollbar-thumb: light-dark(#64748B, #738196); --scrollbar-track: var(--surface-raised); }
.bg-\[\#04060F\] { background-color: var(--background) !important; }
.bg-\[\#0B1020\], .bg-\[\#0B1020\]\/95 { background-color: var(--surface-raised) !important; }
.bg-\[\#4BB8E8\] { background-color: var(--accent) !important; color: var(--text-on-accent) !important; }
.bg-\[\#4BB8E8\]\/15 { background-color: color-mix(in oklab, var(--accent) 16%, transparent) !important; }
.bg-\[\#4BB8E8\]\/10 { background-color: color-mix(in oklab, var(--accent) 11%, transparent) !important; }
.bg-white\/10 { background-color: color-mix(in oklab, var(--accent) 16%, transparent) !important; color: var(--text) !important; }
.text-\[\#EEF2F8\] { color: var(--text) !important; }
.text-\[\#A0B0C8\] { color: var(--text-muted) !important; }
.text-\[\#738196\] { color: var(--text-subtle) !important; }
.text-\[\#4BB8E8\] { color: var(--accent) !important; }
.text-\[\#04060F\] { color: var(--text-on-accent) !important; }
.placeholder\:text-\[\#738196\]::placeholder { color: var(--text-subtle) !important; }
.border-\[rgba\(238\,242\,248\,0\.16\)\], .border-\[rgba\(238\,242\,248\,0\.12\)\], .border-white\/15 { border-color: var(--border) !important; }
.border-\[rgba\(238\,242\,248\,0\.08\)\], .border-\[rgba\(238\,242\,248\,0\.10\)\], .border-white\/10 { border-color: var(--border-subtle) !important; }
.border-\[\#4BB8E8\] { border-color: var(--accent) !important; }
.border-\[\#4BB8E8\]\/40 { border-color: color-mix(in oklab, var(--accent) 45%, transparent) !important; }
.hover\:bg-white\/5:hover, .hover\:bg-white\/\[0\.04\]:hover, .hover\:bg-white\/\[0\.06\]:hover, .hover\:bg-\[\#EEF2F8\]\/\[0\.05\]:hover, .hover\:bg-\[\#EEF2F8\]\/10:hover { background-color: var(--hover-tint) !important; }
.hover\:text-\[\#EEF2F8\]:hover, .hover\:text-white:hover { color: var(--text) !important; }
.hover\:text-\[\#4BB8E8\]:hover, .group:hover .group-hover\:text-\[\#4BB8E8\] { color: var(--accent) !important; }
.hover\:border-\[\#4BB8E8\]:hover, .hover\:border-\[\#4BB8E8\]\/50:hover, .focus\:border-\[\#4BB8E8\]:focus { border-color: var(--accent) !important; }
select option { background-color: var(--surface-raised) !important; color: var(--text) !important; }
.md-code-inline, .md-pre-wrap, .md-table-wrap { background: var(--background) !important; border-color: var(--border) !important; }
.md-code-inline, .md-list-marker, .md-link { color: var(--accent) !important; }
.md-pre, .md-table td, .md-quote { color: var(--text) !important; }
.md-table th { color: var(--text) !important; background: var(--hover-tint) !important; border-color: var(--border) !important; }
.md-table td { border-color: var(--border-subtle) !important; }
.md-math { background: color-mix(in oklab, var(--accent) 10%, transparent) !important; border-color: color-mix(in oklab, var(--accent) 28%, transparent) !important; color: var(--text) !important; }
.md-quote { border-inline-start-color: var(--accent) !important; background: color-mix(in oklab, var(--accent) 8%, transparent) !important; }
.rag-slider { --slider-fill-color: var(--accent) !important; --slider-track-color: var(--border) !important; }
.theme-swatch { forced-color-adjust: none; }
@media (prefers-contrast: more) {
  #prompt-container, #seed-chips .seed-chip, #more-ideas-btn, #home-browse-btn { background: var(--surface-raised) !important; border-color: var(--border) !important; color: var(--text) !important; }
}
@media (forced-colors: active) {
  :root { --background: Canvas; --surface-raised: Canvas; --text: CanvasText; --text-muted: CanvasText; --text-subtle: GrayText; --accent: Highlight; --text-on-accent: HighlightText; --border: ButtonBorder; --border-subtle: ButtonBorder; }
  .ambient-stage { display: none !important; }
  #seed-chips .seed-chip, #more-ideas-btn, #home-browse-btn { background: Canvas !important; border: 1px solid ButtonBorder !important; color: ButtonText !important; }
}
</style>"""
