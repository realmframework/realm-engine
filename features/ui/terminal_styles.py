"""Integrated Bottom Panel Terminal styles with WCAG Dark & Light adaptive ANSI color tokens."""

TERMINAL_STYLES_CSS: str = r"""<style id="realm-terminal-styles">
:root {
  --term-bg: light-dark(color-mix(in oklab, var(--surface-raised) 94%, transparent), color-mix(in oklab, var(--background) 92%, transparent));
  --term-red: light-dark(#B91C1C, #F87171); --term-green: light-dark(#15803D, #4ADE80); --term-yellow: light-dark(#A16207, #FBBF24);
  --term-blue: light-dark(#1D4ED8, #60A5FA); --term-magenta: light-dark(#7E22CE, #C084FC); --term-cyan: light-dark(#0369A1, #38BDF8);
}
#bottom-terminal-pane[hidden], #bottom-panel-frame[hidden], .wb-embed-frame[hidden] { display: none !important; }
.term-pane { flex: 1 1 auto; min-height: 0; height: 100%; display: flex; flex-direction: column; overflow: hidden; background: var(--term-bg); }
.term-bar { flex: none; display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; padding: 0.28rem 0.65rem; border-bottom: 1px solid var(--border-subtle); background: color-mix(in oklab, var(--surface-raised) 65%, transparent); }
.term-sessions { display: flex; align-items: center; gap: 0.25rem; min-width: 0; overflow-x: auto; scrollbar-width: none; }
.term-sessions::-webkit-scrollbar { display: none; }
.term-pill { display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.18rem 0.52rem; border-radius: 0.45rem; border: 1px solid transparent; background: transparent; color: var(--text-muted); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: calc(0.74rem * var(--ui-scale, 1)); cursor: pointer; white-space: nowrap; transition: background-color 0.12s ease, color 0.12s ease, border-color 0.12s ease; }
.term-pill:hover { background: var(--hover-tint); color: var(--text); }
.term-pill[aria-selected="true"] { background: color-mix(in oklab, var(--accent) 14%, transparent); border-color: color-mix(in oklab, var(--accent) 32%, transparent); color: var(--text); font-weight: 500; }
.term-pill-dot { width: 0.42rem; height: 0.42rem; border-radius: 999px; background: var(--term-green); flex-shrink: 0; }
.term-pill-dot.is-exited { background: var(--text-subtle); }
.term-pill-x { display: inline-flex; align-items: center; justify-content: center; width: 1rem; height: 1rem; border-radius: 999px; font-size: 0.68rem; color: var(--text-subtle); }
.term-pill-x:hover { background: var(--hover-tint); color: var(--text); }
.term-bar-right { display: flex; align-items: center; gap: 0.3rem; flex-shrink: 0; }
.term-cwd { max-width: 16rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: calc(0.71rem * var(--ui-scale, 1)); color: var(--text-subtle); padding-inline: 0.3rem; }
.term-out { flex: 1 1 auto; min-height: 0; overflow-y: auto; overscroll-behavior: contain; margin: 0; padding: 0.65rem 0.9rem; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: calc(0.82rem * var(--ui-scale, 1)); line-height: 1.5; color: var(--text); white-space: pre-wrap; word-break: break-word; user-select: text; -webkit-user-select: text; cursor: text; }
.term-input-row { flex: none; display: flex; align-items: center; gap: 0.45rem; padding: 0.38rem 0.85rem; border-top: 1px solid var(--border-subtle); background: color-mix(in oklab, var(--surface-raised) 74%, transparent); }
.term-prompt { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: calc(0.84rem * var(--ui-scale, 1)); font-weight: 700; color: var(--accent); user-select: none; flex-shrink: 0; }
.term-input { flex: 1 1 auto; min-width: 0; border: 0; outline: none; background: transparent; color: var(--text); font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: calc(0.83rem * var(--ui-scale, 1)); }
.term-input::placeholder { color: var(--text-subtle); }
.ansi-b { font-weight: 600; } .ansi-d { opacity: 0.68; } .ansi-i { font-style: italic; } .ansi-u { text-decoration: underline; }
.ansi-30, .ansi-90 { color: var(--text-subtle); } .ansi-31, .ansi-91 { color: var(--term-red); }
.ansi-32, .ansi-92 { color: var(--term-green); } .ansi-33, .ansi-93 { color: var(--term-yellow); }
.ansi-34, .ansi-94 { color: var(--term-blue); } .ansi-35, .ansi-95 { color: var(--term-magenta); }
.ansi-36, .ansi-96 { color: var(--term-cyan); } .ansi-37, .ansi-97 { color: var(--text); }
</style>"""
