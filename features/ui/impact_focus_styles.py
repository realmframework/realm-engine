"""Theme-adaptive CSS for Focus & Goals (native <progress> ring & bars) and Time & Impact."""

IMPACT_FOCUS_STYLES_CSS: str = r"""<style id="realm-impact-focus-styles">
@property --value { syntax: "<number>"; inherits: true; initial-value: 0; }
#focus-view [hidden], #impact-view [hidden], #deep-focus-modal [hidden], #impact-entry-modal [hidden] { display: none !important; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(12.5rem, 1fr)); gap: 0.75rem; }
.kpi-card { background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: 0.95rem; padding: 0.95rem 1.05rem; display: flex; flex-direction: column; gap: 0.25rem; }
.kpi-lbl { font-size: calc(0.78rem * var(--ui-scale, 1)); color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em; font-family: ui-monospace, monospace; }
.kpi-val { font-size: calc(1.45rem * var(--ui-scale, 1)); font-weight: 700; letter-spacing: -0.02em; color: var(--text); }
.kpi-val.is-ok { color: var(--status-ok); }
.kpi-val.is-warn { color: var(--status-danger); }
.kpi-sub { font-size: calc(0.8rem * var(--ui-scale, 1)); color: var(--text-subtle); }
.timer-bar { display: grid; grid-template-columns: minmax(12rem, 1fr) auto auto auto; align-items: center; gap: 0.6rem; padding: 0.85rem 1rem; border-radius: 1rem; background: var(--surface-raised); border: 1px solid var(--border); }
@media (max-width: 820px) { .timer-bar { grid-template-columns: 1fr 1fr; } .timer-bar > :first-child { grid-column: 1 / -1; } }
.timer-clock { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: calc(1.25rem * var(--ui-scale, 1)); font-weight: 700; color: var(--accent); min-width: 5.5rem; text-align: center; }
.impact-card { background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: 1rem; padding: 1rem 1.15rem; display: flex; flex-direction: column; gap: 0.55rem; margin-bottom: 0.65rem; }
.impact-card:hover { border-color: var(--border); }
.impact-q-lbl { font-size: calc(0.75rem * var(--ui-scale, 1)); text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-subtle); font-family: ui-monospace, monospace; }
.roi-table { width: 100%; border-collapse: collapse; background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: 0.95rem; overflow: hidden; font-size: calc(0.875rem * var(--ui-scale, 1)); }
.roi-table th { text-align: left; padding: 0.65rem 0.9rem; color: var(--text-muted); font-weight: 600; background: var(--surface-soft); border-bottom: 1px solid var(--border-subtle); }
.roi-table td { padding: 0.65rem 0.9rem; border-top: 1px solid var(--border-subtle); color: var(--text); }
.goal-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(19rem, 1fr)); gap: 0.9rem; }
.goal-card { background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: 1rem; padding: 1.05rem 1.15rem; display: flex; flex-direction: column; gap: 0.65rem; }
.goal-pace-ahead, .goal-pace-behind, .goal-pace-on_track { white-space: nowrap; flex-shrink: 0; }
.goal-pace-ahead { color: var(--status-ok); border-color: color-mix(in oklab, var(--status-ok) 45%, transparent); background: color-mix(in oklab, var(--status-ok) 12%, transparent); }
.goal-pace-behind { color: var(--status-danger); border-color: color-mix(in oklab, var(--status-danger) 45%, transparent); background: color-mix(in oklab, var(--status-danger) 12%, transparent); }
.goal-pace-on_track { color: var(--accent); border-color: color-mix(in oklab, var(--accent) 45%, transparent); background: color-mix(in oklab, var(--accent) 12%, transparent); }
progress.goal-progress { appearance: none; -webkit-appearance: none; width: 100%; height: 0.55rem; border: 0 solid; border-radius: 999px; overflow: clip; background: var(--surface-pill); }
progress.goal-progress::-webkit-progress-bar { background: transparent; }
progress.goal-progress::-webkit-progress-value { background: var(--accent); border-radius: 999px; transition: inline-size 0.3s ease; }
progress.goal-progress::-moz-progress-bar { background: var(--accent); border-radius: 999px; transition: inline-size 0.3s ease; }
.focus-ring-wrapper { position: relative; display: grid; place-items: center; margin: 0.5rem auto; }
progress.focus-ring { --size: 13.5rem; --thickness: 0.85rem; --track-color: var(--surface-soft); --fill-color: var(--accent); --value: attr(value type(<number>)); appearance: none; -webkit-appearance: none; width: var(--size); height: var(--size); border-radius: 50%; background: conic-gradient(var(--fill-color) calc(var(--value) * 1%), var(--track-color) 0); background-clip: border-area; border: var(--thickness) solid transparent; background-origin: border-box; transition: --value 0s linear; }
@media (prefers-reduced-motion: no-preference) { progress.focus-ring { transition-duration: 0.35s; } }
@supports not (background-clip: border-area) { progress.focus-ring { border: 0; -webkit-mask-image: radial-gradient(transparent calc(50% - var(--thickness)), black calc(50% - var(--thickness) + 0.5px)); mask-image: radial-gradient(transparent calc(50% - var(--thickness)), black calc(50% - var(--thickness) + 0.5px)); } }
@media (forced-colors: active) { progress.focus-ring { forced-color-adjust: none; --fill-color: CanvasText; --track-color: Canvas; } }
progress.focus-ring[value="100"] { --fill-color: var(--status-ok); }
progress.focus-ring::-webkit-progress-bar { display: none; background: none; }
progress.focus-ring::-webkit-progress-value { display: none; background: none; }
progress.focus-ring::-moz-progress-bar { display: none; background: none; }
progress.focus-ring::slider-fill { display: none; background: none; }
.focus-ring-content { position: absolute; display: flex; flex-direction: column; align-items: center; gap: 0.2rem; pointer-events: none; }
.focus-ring-time { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: calc(2.1rem * var(--ui-scale, 1)); font-weight: 700; letter-spacing: -0.02em; color: var(--text); }
.focus-ring-sub { font-size: calc(0.78rem * var(--ui-scale, 1)); color: var(--text-muted); }
.focus-dialog { margin: auto; width: calc(100% - 2rem); max-width: 38rem; max-height: 90vh; overflow-y: auto; border-radius: 1.3rem; background: var(--surface-raised); color: var(--text); border: 1px solid var(--border); padding: 1.6rem; box-shadow: var(--dialog-shadow); }
.quality-row { display: flex; gap: 0.45rem; justify-content: center; flex-wrap: wrap; }
.quality-btn { min-width: 2.6rem; height: 2.4rem; border-radius: 0.65rem; border: 1px solid var(--border); background: var(--surface-soft); color: var(--text); font-weight: 600; cursor: pointer; }
.quality-btn[aria-pressed="true"] { background: var(--accent); color: var(--text-on-accent); border-color: transparent; }
.plan-card { background: var(--surface-raised); border: 1px solid color-mix(in oklab, var(--accent) 40%, var(--border)); border-radius: 1rem; padding: 1rem 1.15rem; display: flex; flex-direction: column; gap: 0.7rem; }
</style>"""
