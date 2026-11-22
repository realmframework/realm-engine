"""Adaptive Dark/Light/System, dual-tone palette tokens, and Supernova ambient backdrop CSS."""

from features.ui.theme_overrides import THEME_OVERRIDES_CSS

THEME_BRIDGE_CSS: str = (
    r"""<style id="realm-theme-bridge">
:root {
  color-scheme: light dark;
  --in-oklab: ;
  --accent-seed: #4BB8E8;
  --accent-glow: #6366F1;
  --bg-dark: color-mix(in oklab, #04060F 93%, var(--accent-seed));
  --surface-dark: color-mix(in oklab, #0B1020 90%, var(--accent-seed));
  --surface-soft-dark: color-mix(in oklab, #141C33 86%, var(--accent-seed));
  --glass-dark: color-mix(in oklab, var(--surface-dark) 72%, transparent); --glass-strong-dark: color-mix(in oklab, var(--surface-dark) 82%, transparent); --glass-soft-dark: color-mix(in oklab, var(--surface-soft-dark) 56%, transparent);
  --specular-dark: rgba(255, 255, 255, 0.085);
  --card-shadow-dark: inset 0 1px 0 var(--specular-dark), 0 10px 28px -12px rgba(2, 4, 12, 0.62), 0 2px 6px rgba(2, 4, 12, 0.28);
  --card-hover-dark: inset 0 1px 0 rgba(255, 255, 255, 0.14), 0 16px 36px -12px color-mix(in oklab, var(--accent-seed) 24%, rgba(2, 4, 12, 0.72)), 0 0 0 1px color-mix(in oklab, var(--accent-dark) 30%, transparent);
  --accent-dark: color-mix(in oklab, var(--accent-seed) 88%, white);
  --border-dark: color-mix(in oklab, rgba(238, 242, 248, 0.24) 80%, var(--accent-seed));
  --border-subtle-dark: color-mix(in oklab, rgba(238, 242, 248, 0.12) 84%, var(--accent-seed));
  --border-control-dark: color-mix(in oklab, rgba(238, 242, 248, 0.38) 84%, var(--accent-seed));
  --aura-a-dark: color-mix(in oklab, var(--accent-seed) 46%, transparent);
  --aura-b-dark: color-mix(in oklab, var(--accent-glow) 52%, transparent);
  --aura-core-dark: color-mix(in oklab, white 26%, var(--accent-seed));
  --hover-tint-dark: rgba(238, 242, 248, 0.06);
  --shadow-dark: 0 22px 48px rgba(0, 0, 0, 0.45);
  --bg-light: color-mix(in oklab, #F3F7FC 92%, var(--accent-seed));
  --surface-light: color-mix(in oklab, #FFFFFF 96%, var(--accent-seed));
  --surface-soft-light: color-mix(in oklab, #E8F0FA 88%, var(--accent-seed));
  --glass-light: color-mix(in oklab, #FFFFFF 78%, transparent); --glass-strong-light: color-mix(in oklab, #FFFFFF 86%, transparent); --glass-soft-light: color-mix(in oklab, var(--surface-soft-light) 68%, transparent);
  --specular-light: rgba(255, 255, 255, 0.92);
  --card-shadow-light: inset 0 1px 0 var(--specular-light), 0 10px 28px -12px rgba(15, 23, 42, 0.12), 0 2px 6px rgba(15, 23, 42, 0.05);
  --card-hover-light: inset 0 1px 0 var(--specular-light), 0 16px 36px -12px color-mix(in oklab, var(--accent-seed) 22%, rgba(15, 23, 42, 0.16)), 0 0 0 1px color-mix(in oklab, var(--accent-light) 26%, transparent);
  --accent-light: color-mix(in oklab, var(--accent-seed) 50%, #04060F);
  --border-light: color-mix(in oklab, rgba(11, 16, 32, 0.28) 82%, var(--accent-seed));
  --border-subtle-light: color-mix(in oklab, rgba(11, 16, 32, 0.14) 84%, var(--accent-seed));
  --border-control-light: color-mix(in oklab, rgba(11, 16, 32, 0.48) 86%, var(--accent-seed));
  --aura-a-light: color-mix(in oklab, var(--accent-seed) 28%, transparent);
  --aura-b-light: color-mix(in oklab, var(--accent-glow) 26%, transparent);
  --aura-core-light: color-mix(in oklab, var(--accent-seed) 40%, white);
  --hover-tint-light: rgba(11, 16, 32, 0.055);
  --shadow-light: 0 18px 40px rgba(15, 23, 42, 0.12);
  --background: var(--bg-light); --surface-raised: var(--surface-light); --surface-soft: var(--surface-soft-light);
  --surface-glass: var(--glass-light); --surface-glass-strong: var(--glass-strong-light); --surface-glass-soft: var(--glass-soft-light);
  --specular-edge: var(--specular-light); --card-shadow: var(--card-shadow-light); --card-shadow-hover: var(--card-hover-light);
  --text: #0B1020; --text-muted: #334155; --text-subtle: #4B5563; --prose: #1E293B; --accent: var(--accent-light);
  --status-ok: #047857; --status-warn: #92400E; --status-danger: #B91C1C;
  --surface-pill: rgba(11, 16, 32, 0.055);
  --border: var(--border-light); --border-subtle: var(--border-subtle-light); --border-control: var(--border-control-light);
  --aura-a: var(--aura-a-light); --aura-b: var(--aura-b-light); --aura-core: var(--aura-core-light);
  --hover-tint: var(--hover-tint-light); --dialog-shadow: var(--shadow-light);
  --scrollbar-thumb: #4B5563; --scrollbar-track: var(--surface-light); --text-on-accent: #FFFFFF;
  --accent-sheen: radial-gradient(120% 95% at 0% 0%, color-mix(in oklab, var(--accent) 11%, transparent) 0%, transparent 58%);
  --chrome-sheen: linear-gradient(180deg var(--in-oklab), color-mix(in oklab, var(--accent) 7%, transparent) 0%, transparent 26%, color-mix(in oklab, var(--accent-glow) 6%, transparent) 100%);
}
@supports (background: linear-gradient(in oklab, white, black)) { :root { --in-oklab: in oklab; } }
:root:has(> head > meta[name="color-scheme"][content="dark"]) { color-scheme: dark; }
:root:has(> head > meta[name="color-scheme"][content="light"]) { color-scheme: light; }
@media (prefers-color-scheme: dark) {
  :root {
    --background: var(--bg-dark); --surface-raised: var(--surface-dark); --surface-soft: var(--surface-soft-dark);
    --surface-glass: var(--glass-dark); --surface-glass-strong: var(--glass-strong-dark); --surface-glass-soft: var(--glass-soft-dark);
    --specular-edge: var(--specular-dark); --card-shadow: var(--card-shadow-dark); --card-shadow-hover: var(--card-hover-dark);
    --text: #EEF2F8; --text-muted: #A0B0C8; --text-subtle: #8A99AE; --prose: #C8D4E6; --accent: var(--accent-dark);
    --status-ok: #38D399; --status-warn: #FCD34D; --status-danger: #FCA5A5;
    --surface-pill: rgba(238, 242, 248, 0.055);
    --border: var(--border-dark); --border-subtle: var(--border-subtle-dark); --border-control: var(--border-control-dark);
    --aura-a: var(--aura-a-dark); --aura-b: var(--aura-b-dark); --aura-core: var(--aura-core-dark);
    --hover-tint: var(--hover-tint-dark); --dialog-shadow: var(--shadow-dark);
    --scrollbar-thumb: #8A99AE; --scrollbar-track: var(--surface-dark); --text-on-accent: #04060F;
  }
}
@supports (color: light-dark(white, black)) {
  :root {
    --background: light-dark(var(--bg-light), var(--bg-dark)); --surface-raised: light-dark(var(--surface-light), var(--surface-dark));
    --surface-soft: light-dark(var(--surface-soft-light), var(--surface-soft-dark));
    --surface-glass: light-dark(var(--glass-light), var(--glass-dark)); --surface-glass-strong: light-dark(var(--glass-strong-light), var(--glass-strong-dark));
    --surface-glass-soft: light-dark(var(--glass-soft-light), var(--glass-soft-dark)); --specular-edge: light-dark(var(--specular-light), var(--specular-dark));
    --card-shadow: light-dark(var(--card-shadow-light), var(--card-shadow-dark)); --card-shadow-hover: light-dark(var(--card-hover-light), var(--card-hover-dark));
    --text: light-dark(#0B1020, #EEF2F8); --text-muted: light-dark(#334155, #A0B0C8); --text-subtle: light-dark(#4B5563, #8A99AE);
    --prose: light-dark(#1E293B, #C8D4E6); --accent: light-dark(var(--accent-light), var(--accent-dark));
    --status-ok: light-dark(#047857, #38D399); --status-warn: light-dark(#92400E, #FCD34D); --status-danger: light-dark(#B91C1C, #FCA5A5);
    --surface-pill: light-dark(rgba(11, 16, 32, 0.055), rgba(238, 242, 248, 0.055));
    --border: light-dark(var(--border-light), var(--border-dark)); --border-subtle: light-dark(var(--border-subtle-light), var(--border-subtle-dark));
    --border-control: light-dark(var(--border-control-light), var(--border-control-dark));
    --aura-a: light-dark(var(--aura-a-light), var(--aura-a-dark)); --aura-b: light-dark(var(--aura-b-light), var(--aura-b-dark)); --aura-core: light-dark(var(--aura-core-light), var(--aura-core-dark));
    --hover-tint: light-dark(var(--hover-tint-light), var(--hover-tint-dark)); --dialog-shadow: light-dark(var(--shadow-light), var(--shadow-dark));
    --scrollbar-thumb: light-dark(#4B5563, #8A99AE); --scrollbar-track: light-dark(var(--surface-light), var(--surface-dark));
    --text-on-accent: light-dark(#FFFFFF, #04060F);
  }
}
@supports (color: color(from red xyz-d65 0 0 0)) {
  :root { --text-on-accent: color(from var(--accent) xyz-d65 calc(max(0, sign(0.17913 - y)) * 0.9505) max(0, sign(0.17913 - y)) calc(max(0, sign(0.17913 - y)) * 1.089)); }
}
@supports (color: contrast-color(red)) { :root { --text-on-accent: contrast-color(var(--accent)); } }
html, body { background-color: var(--background) !important; color: var(--text) !important; accent-color: var(--accent); }
#main-shell { background-color: transparent !important; background-image: none !important; }
.ambient-stage { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; content-visibility: auto; contain-intrinsic-size: auto 100vw auto 100vh; transition: opacity 0.45s ease; }
.ambient-stage.is-dimmed { opacity: 0.48; }
.ambient-stage.is-dimmed.is-speaking { opacity: 0.66; }
.ambient-stage.is-off { display: none; }
.turn-themed { --turn-accent: color-mix(in oklab, var(--turn-seed, var(--accent-seed)) 50%, #04060F); }
.turn-author-heading { color: var(--turn-accent, var(--accent)); }
.turn-themed .md-list-marker { color: var(--turn-accent, var(--accent)) !important; }
@media (prefers-color-scheme: dark) {
  .turn-themed { --turn-accent: color-mix(in oklab, var(--turn-seed, var(--accent-seed)) 88%, white); }
}
@supports (color: light-dark(white, black)) {
  .turn-themed { --turn-accent: light-dark(color-mix(in oklab, var(--turn-seed, var(--accent-seed)) 50%, #04060F), color-mix(in oklab, var(--turn-seed, var(--accent-seed)) 88%, white)); }
}
.md-body.is-streaming > :is(p, h1, h2, h3, h4, h5, h6, blockquote):last-child::after,
.md-body.is-streaming > :is(ul, ol):last-child > li:last-child::after { content: ""; display: inline-block; width: 0.48em; height: 0.48em; margin-inline-start: 0.35em; vertical-align: 0.08em; border-radius: 9999px; background: var(--turn-accent, var(--accent)); box-shadow: 0 0 8px color-mix(in oklab, var(--turn-accent, var(--accent)) 52%, transparent); }
@media (prefers-reduced-motion: no-preference) {
  .md-body.is-streaming > :is(p, h1, h2, h3, h4, h5, h6, blockquote):last-child::after, .md-body.is-streaming > :is(ul, ol):last-child > li:last-child::after { animation: realm-stream-dot 1.15s ease-in-out infinite; }
}
@keyframes realm-stream-dot { 0%, 100% { opacity: 0.92; transform: scale(1); } 50% { opacity: 0.32; transform: scale(0.8); } }
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
#sidebar { background-color: var(--surface-glass-strong) !important; box-shadow: 1px 0 0 var(--border-subtle) !important; }
#sidebar nav button > span:first-child > span, #open-settings-btn > span:first-child > span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0; }
#sidebar-backdrop { background: light-dark(rgba(11, 16, 32, 0.34), rgba(4, 6, 15, 0.62)); backdrop-filter: blur(2px); -webkit-backdrop-filter: blur(2px); }
#sidebar-backdrop[hidden] { display: none !important; }
@media (max-width: 900px) { #main-shell { padding-left: 0 !important; } }
#prompt-container { background-color: color-mix(in oklab, var(--surface-raised) 86%, transparent) !important; backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); box-shadow: inset 0 0 0 1px var(--border-control), var(--dialog-shadow) !important; }
#prompt-container:focus-within, #prompt-container.is-loading { box-shadow: inset 0 0 0 1.5px var(--accent), 0 0 28px color-mix(in oklab, var(--accent) 26%, transparent) !important; }
.chat-dock { background: transparent !important; }
.chat-dock #prompt-container { background-color: color-mix(in oklab, var(--surface-raised) 92%, transparent) !important; }
.chat-scroll-mask { -webkit-mask-image: linear-gradient(to bottom, #000 calc(100% - 28px), transparent 100%); mask-image: linear-gradient(to bottom, #000 calc(100% - 28px), transparent 100%); }
dialog { background-color: var(--surface-glass-strong) !important; backdrop-filter: blur(24px) saturate(135%); -webkit-backdrop-filter: blur(24px) saturate(135%); color: var(--text) !important; border-color: var(--border) !important; box-shadow: inset 0 1px 0 var(--specular-edge), var(--dialog-shadow) !important; }
dialog::backdrop { background: light-dark(rgba(11, 16, 32, 0.28), rgba(4, 6, 15, 0.54)) !important; }
#onboarding-modal [hidden], #agent-studio-modal [hidden], [data-lai-panel] [hidden], #reset-logo-btn[hidden], #global-drop-overlay[hidden], #web-search-options [hidden], #web-search-lock-note[hidden] { display: none !important; }
.settings-body { --scrollbar-thumb: light-dark(#4B5563, #8A99AE); --scrollbar-track: var(--surface-raised); }
#upload-redaction-inspector { scrollbar-color: var(--scrollbar-thumb) var(--background) !important; }
#upload-redaction-inspector::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb) !important; }
"""
    + THEME_OVERRIDES_CSS
    + "</style>"
)
