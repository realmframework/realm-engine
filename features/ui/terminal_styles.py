"""Integrated Bottom Panel Terminal styles with Theme-Synced & Classic Neutral modes."""

TERMINAL_STYLES_CSS: str = r"""<style id="realm-terminal-styles">
:root {
  --term-bg-top: light-dark(color-mix(in oklab, var(--surface-raised) 91%, var(--accent-seed) 9%), color-mix(in oklab, var(--surface-raised) 84%, var(--accent-seed) 16%));
  --term-bg-bot: light-dark(color-mix(in oklab, var(--background) 93%, var(--accent-glow) 7%), color-mix(in oklab, var(--background) 90%, var(--accent-glow) 10%));
  --term-bg: linear-gradient(180deg, var(--term-bg-top), var(--term-bg-bot));
  --term-bar-bg: light-dark(color-mix(in oklab, var(--surface-raised) 84%, var(--accent-seed) 10%), color-mix(in oklab, var(--surface-raised) 74%, var(--accent-seed) 12%));
  --term-border: color-mix(in oklab, var(--accent) 26%, var(--border-subtle));
  --term-text: var(--text);
  --term-muted: var(--text-muted);
  --term-subtle: var(--text-subtle);
  --term-prompt: var(--accent);
  --term-pill-bg: color-mix(in oklab, var(--accent) 18%, transparent);
  --term-pill-border: color-mix(in oklab, var(--accent) 38%, transparent);
  --term-red: light-dark(#B91C1C, #F87171); --term-green: light-dark(#15803D, #4ADE80); --term-yellow: light-dark(#A16207, #FBBF24);
  --term-blue: light-dark(color-mix(in oklab, #1D4ED8 68%, var(--accent-light)), color-mix(in oklab, #60A5FA 65%, var(--accent-dark)));
  --term-magenta: light-dark(color-mix(in oklab, #7E22CE 72%, var(--accent-glow)), color-mix(in oklab, #C084FC 68%, var(--accent-glow)));
  --term-cyan: light-dark(color-mix(in oklab, #0369A1 55%, var(--accent-light)), color-mix(in oklab, #38BDF8 52%, var(--accent-dark)));
}
#bottom-terminal-pane[data-term-theme="neutral"] {
  --term-bg-top: light-dark(#FAFAFB, #0D1117);
  --term-bg-bot: light-dark(#F6F8FA, #0B0F14);
  --term-bg: linear-gradient(180deg, var(--term-bg-top), var(--term-bg-bot));
  --term-bar-bg: light-dark(#F1F3F5, #161B22);
  --term-border: light-dark(#D0D7DE, #30363D);
  --term-text: light-dark(#1F2328, #E6EDF3);
  --term-muted: light-dark(#59636E, #8B949E);
  --term-subtle: light-dark(#656D76, #6E7681);
  --term-prompt: light-dark(#1F2328, #E6EDF3);
  --term-pill-bg: light-dark(rgba(15, 23, 42, 0.08), rgba(240, 246, 252, 0.1));
  --term-pill-border: light-dark(rgba(15, 23, 42, 0.2), rgba(240, 246, 252, 0.22));
  --term-blue: light-dark(#1D4ED8, #58A6FF); --term-magenta: light-dark(#7E22CE, #BC8CFF); --term-cyan: light-dark(#0369A1, #39C5CF);
}
#bottom-terminal-pane[hidden], #bottom-panel-frame[hidden], .wb-embed-frame[hidden] { display: none !important; }
.term-pane { flex: 1 1 auto; min-height: 0; height: 100%; display: flex; flex-direction: column; overflow: hidden; background: var(--term-bg); color: var(--term-text); }
.term-bar { flex: none; display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; padding: 0.28rem 0.65rem; border-bottom: 1px solid var(--term-border); background: var(--term-bar-bg); }
.term-sessions { display: flex; align-items: center; gap: 0.25rem; min-width: 0; overflow-x: auto; scrollbar-width: none; }
.term-sessions::-webkit-scrollbar { display: none; }
.term-pill { display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.18rem 0.52rem; border-radius: 0.45rem; border: 1px solid transparent; background: transparent; color: var(--term-muted); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: calc(0.74rem * var(--ui-scale, 1)); cursor: pointer; white-space: nowrap; transition: background-color 0.12s ease, color 0.12s ease, border-color 0.12s ease; }
.term-pill:hover { background: var(--hover-tint); color: var(--term-text); }
.term-pill[aria-selected="true"] { background: var(--term-pill-bg); border-color: var(--term-pill-border); color: var(--term-text); font-weight: 500; }
.term-pill-dot { width: 0.42rem; height: 0.42rem; border-radius: 999px; background: var(--term-green); flex-shrink: 0; }
.term-pill-dot.is-exited { background: var(--term-subtle); }
.term-pill-x { display: inline-flex; align-items: center; justify-content: center; width: 1rem; height: 1rem; border-radius: 999px; font-size: 0.68rem; color: var(--term-subtle); }
.term-pill-x:hover { background: var(--hover-tint); color: var(--term-text); }
.term-bar-right { display: flex; align-items: center; gap: 0.3rem; flex-shrink: 0; }
.term-cwd { max-width: 16rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: calc(0.71rem * var(--ui-scale, 1)); color: var(--term-subtle); padding-inline: 0.3rem; }
#term-theme-btn[aria-pressed="true"] { border-color: var(--term-pill-border); background: var(--term-pill-bg); color: var(--term-prompt); }
.term-out { flex: 1 1 auto; min-height: 0; overflow-y: auto; overscroll-behavior: contain; margin: 0; padding: 0.65rem 0.9rem; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: calc(0.82rem * var(--ui-scale, 1)); line-height: 1.5; color: var(--term-text); white-space: pre-wrap; word-break: break-word; user-select: text; -webkit-user-select: text; cursor: text; }
.term-input-row { flex: none; display: flex; align-items: center; gap: 0.45rem; padding: 0.38rem 0.85rem; border-top: 1px solid var(--term-border); background: var(--term-bar-bg); }
.term-prompt { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: calc(0.84rem * var(--ui-scale, 1)); font-weight: 700; color: var(--term-prompt); user-select: none; flex-shrink: 0; }
.term-input { flex: 1 1 auto; min-width: 0; border: 0; outline: none; background: transparent; color: var(--term-text); font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: calc(0.83rem * var(--ui-scale, 1)); }
.term-input::placeholder { color: var(--term-subtle); }
.ansi-b { font-weight: 600; } .ansi-d { opacity: 0.68; } .ansi-i { font-style: italic; } .ansi-u { text-decoration: underline; }
.ansi-30, .ansi-90 { color: var(--term-subtle); } .ansi-31, .ansi-91 { color: var(--term-red); }
.ansi-32, .ansi-92 { color: var(--term-green); } .ansi-33, .ansi-93 { color: var(--term-yellow); }
.ansi-34, .ansi-94 { color: var(--term-blue); } .ansi-35, .ansi-95 { color: var(--term-magenta); }
.ansi-36, .ansi-96 { color: var(--term-cyan); } .ansi-37, .ansi-97 { color: var(--term-text); }
</style>"""
