"""Theme-adaptive CSS for Native Local Workflow & Agent Pipeline Studio (Interactive Canvas + Gateways)."""

WORKFLOW_STUDIO_STYLES_CSS: str = r"""<style id="realm-workflow-studio-styles">
#workflows-view [hidden], #wf-templates-modal [hidden], #wf-run-modal [hidden] { display: none !important; }
.wf-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.45rem; padding: 0.55rem 0.75rem; border-radius: 0.9rem; background: var(--surface-raised); border: 1px solid var(--border-subtle); }
.wf-tb-group { display: inline-flex; align-items: center; gap: 0.3rem; flex-wrap: wrap; }
.wf-tb-sep { inline-size: 1px; block-size: 1.4rem; border-inline-start: 1px solid var(--border); margin-inline: 0.2rem; }
.wf-tb-btn { min-inline-size: 2rem; min-block-size: 2rem; padding: 0.35rem 0.7rem; border-radius: 0.6rem; border: 1px solid var(--border); background: var(--surface-soft); color: var(--text); font-size: calc(0.84rem * var(--ui-scale, 1)); font-weight: 500; cursor: pointer; display: inline-flex; align-items: center; gap: 0.35rem; }
.wf-tb-btn[aria-pressed="true"] { background: var(--accent); color: var(--text-on-accent); border-color: transparent; font-weight: 600; }
.wf-tb-btn[aria-disabled="true"] { opacity: 0.48; cursor: not-allowed; }
@media (hover: hover) { .wf-tb-btn:hover:not([aria-pressed="true"]):not([aria-disabled="true"]) { border-color: var(--accent); color: var(--accent); } }
@media (pointer: coarse) { .wf-tb-btn { min-inline-size: 2.6rem; min-block-size: 2.6rem; } }
@media (prefers-reduced-motion: no-preference) { .wf-tb-btn, .wf-node-card { transition: border-color 0.16s ease, box-shadow 0.16s ease, background-color 0.16s ease; } }
@media (forced-colors: active) { .wf-tb-btn[aria-pressed="true"] { background: Highlight; color: HighlightText; border-color: Highlight; } .wf-tb-sep { border-color: ButtonText; } }
.wf-meta-bar { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: flex-end; padding: 0.72rem 0.9rem; border-radius: 0.9rem; background: var(--surface-raised); border: 1px solid var(--border-subtle); }
.wf-meta-bar > .wb-field { flex: 1 1 12rem; min-width: 0; }
.wf-meta-bar > .wb-field:first-child { flex: 1.6 1 15rem; }
#wf-sched-wrap { flex: 0 0 auto; }
.wf-workspace-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(19.5rem, 24rem); gap: 0.9rem; align-items: start; min-height: 29rem; }
@media (max-width: 1080px) { .wf-workspace-grid { grid-template-columns: 1fr; } }
.wf-canvas-viewport { position: relative; overflow: hidden; min-height: 29rem; height: 64vh; border-radius: 1rem; border: 1px solid var(--border-subtle); background-color: var(--surface-soft); background-image: radial-gradient(color-mix(in oklab, var(--text-subtle) 28%, transparent) 1px, transparent 1px); background-size: 20px 20px; cursor: grab; touch-action: none; }
.wf-canvas-viewport.is-panning { cursor: grabbing; }
.wf-canvas-viewport.is-step-mode { overflow: auto; cursor: default; touch-action: auto; height: auto; max-height: 68vh; }
.wf-canvas-stage { position: absolute; inset: 0; width: 100%; height: 100%; transform-origin: 0 0; overflow: visible; }
.wf-svg-layer { position: absolute; inset: 0; width: 1px; height: 1px; pointer-events: none; overflow: visible; }
.wf-edge-path { fill: none; stroke: color-mix(in oklab, var(--accent) 68%, var(--border)); stroke-width: 2.3; }
.wf-edge-path.is-true { stroke: var(--status-ok); }
.wf-edge-path.is-false { stroke: var(--status-danger); stroke-dasharray: 6 4; }
.wf-edge-path.is-draft { stroke: var(--accent); stroke-dasharray: 5 4; opacity: 0.85; }
.wf-edge-pill { pointer-events: auto; cursor: pointer; }
.wf-edge-pill rect { fill: var(--surface-raised); stroke: var(--border); stroke-width: 1; }
.wf-edge-pill.is-true rect { stroke: var(--status-ok); }
.wf-edge-pill.is-false rect { stroke: var(--status-danger); }
.wf-edge-pill:hover rect { stroke: var(--status-danger); }
.wf-edge-label { font-family: ui-monospace, monospace; font-size: 10px; font-weight: 600; fill: var(--text-muted); text-anchor: middle; dominant-baseline: central; pointer-events: none; }
.wf-edge-pill.is-true .wf-edge-label { fill: var(--status-ok); }
.wf-edge-pill.is-false .wf-edge-label { fill: var(--status-danger); }
.wf-node-card { position: absolute; width: 12.75rem; min-height: 6rem; border-radius: 0.9rem; background: var(--surface-raised); border: 1.5px solid var(--border); box-shadow: 0 6px 18px rgba(4, 6, 15, 0.16); padding: 0.6rem 0.8rem; display: flex; flex-direction: column; gap: 0.32rem; cursor: grab; user-select: none; -webkit-user-select: none; touch-action: none; }
.wf-node-card.is-dragging { cursor: grabbing; z-index: 20; box-shadow: 0 12px 28px rgba(4, 6, 15, 0.28); }
.wf-node-card.is-gateway { border-style: dashed; border-color: color-mix(in oklab, var(--status-warn) 65%, var(--border)); }
.wf-node-card.is-selected { border-style: solid; border-color: var(--accent); box-shadow: 0 0 0 2px color-mix(in oklab, var(--accent) 28%, transparent); }
.wf-node-card.is-drop-target { border-color: var(--status-ok); box-shadow: 0 0 0 3px color-mix(in oklab, var(--status-ok) 32%, transparent); }
.wf-node-card.is-running { border-color: var(--accent); box-shadow: 0 0 0 4px color-mix(in oklab, var(--accent) 32%, transparent); }
.wf-node-card.is-completed { border-color: var(--status-ok); }
.wf-node-card.is-failed { border-color: var(--status-danger); }
.wf-node-card.is-skipped { opacity: 0.56; border-style: dashed; }
.wf-node-head { display: flex; align-items: center; justify-content: space-between; gap: 0.3rem; }
.wf-node-badge { font-family: ui-monospace, monospace; font-size: calc(0.68rem * var(--ui-scale, 1)); text-transform: uppercase; letter-spacing: 0.04em; padding: 0.14rem 0.45rem; border-radius: 999px; background: var(--surface-soft); color: var(--accent); border: 1px solid var(--border-subtle); white-space: nowrap; flex-shrink: 0; max-width: 100%; overflow: hidden; text-overflow: ellipsis; }
.wf-node-card.is-gateway .wf-node-badge { color: var(--status-warn); border-color: color-mix(in oklab, var(--status-warn) 40%, transparent); }
.wf-drag-handle { cursor: grab; border: 0; background: transparent; color: var(--text-subtle); width: 1.5rem; height: 1.5rem; border-radius: 0.4rem; display: inline-flex; align-items: center; justify-content: center; }
.wf-node-title { font-size: calc(0.9rem * var(--ui-scale, 1)); font-weight: 600; color: var(--text); line-height: 1.3; word-break: break-word; }
.wf-node-sub { font-size: calc(0.78rem * var(--ui-scale, 1)); color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.wf-port { position: absolute; width: 0.85rem; height: 0.85rem; border-radius: 999px; border: 2px solid var(--surface-raised); background: var(--accent); padding: 0; cursor: crosshair; z-index: 5; transition: transform 0.12s ease; }
.wf-port:hover { transform: scale(1.3); }
.wf-port-in { left: -0.46rem; top: 50%; margin-top: -0.425rem; background: var(--border-control); pointer-events: none; }
.wf-port-out { right: -0.46rem; top: 50%; margin-top: -0.425rem; }
.wf-port-true { right: -0.46rem; top: 38%; margin-top: -0.425rem; background: var(--status-ok); }
.wf-port-false { right: -0.46rem; top: 76%; margin-top: -0.425rem; background: var(--status-danger); }
.wf-port-tag { position: absolute; right: 0.75rem; font-family: ui-monospace, monospace; font-size: 9px; font-weight: 700; letter-spacing: 0.03em; pointer-events: none; }
.wf-port-tag.is-true { top: calc(38% - 0.42rem); color: var(--status-ok); }
.wf-port-tag.is-false { top: calc(76% - 0.42rem); color: var(--status-danger); }
.wf-zoom-hud { position: absolute; right: 0.75rem; bottom: 0.75rem; z-index: 25; display: inline-flex; align-items: center; gap: 0.15rem; padding: 0.22rem; border-radius: 999px; background: color-mix(in oklab, var(--surface-raised) 92%, transparent); border: 1px solid var(--border); backdrop-filter: blur(8px); box-shadow: 0 4px 14px rgba(4, 6, 15, 0.22); }
.wf-hud-btn { min-width: 1.85rem; height: 1.85rem; padding: 0 0.45rem; border: 0; border-radius: 999px; background: transparent; color: var(--text-muted); font-size: calc(0.84rem * var(--ui-scale, 1)); font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; }
.wf-hud-btn:hover { background: var(--hover-tint); color: var(--text); }
.wf-hud-fit { font-size: calc(0.75rem * var(--ui-scale, 1)); font-weight: 500; padding: 0 0.6rem; }
.wf-hud-pct { min-width: 2.9rem; text-align: center; font-family: ui-monospace, monospace; font-size: calc(0.75rem * var(--ui-scale, 1)); color: var(--text-muted); }
.wf-step-list { display: flex; flex-direction: column; gap: 0.55rem; padding: 0.9rem; }
.wf-step-card { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; padding: 0.85rem 1rem; border-radius: 0.9rem; background: var(--surface-raised); border: 1.5px solid var(--border-subtle); cursor: pointer; }
.wf-step-card.is-selected { border-color: var(--accent); }
.wf-step-card.is-completed { border-color: var(--status-ok); }
.wf-step-card.is-running { border-color: var(--accent); }
.wf-side-panel { background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: 1rem; padding: 0.95rem 1.05rem; display: flex; flex-direction: column; gap: 0.75rem; }
.wf-branch-row { display: flex; align-items: center; gap: 0.4rem; }
.wf-branch-row select { flex: 1; min-width: 0; }
.wf-branch-lbl-true { color: var(--status-ok) !important; font-weight: 600 !important; }
.wf-branch-lbl-false { color: var(--status-danger) !important; font-weight: 600 !important; }
.wf-run-step { padding: 0.65rem 0.75rem; border-radius: 0.75rem; background: var(--surface-soft); border: 1px solid var(--border-subtle); display: flex; flex-direction: column; gap: 0.28rem; font-size: calc(0.84rem * var(--ui-scale, 1)); }
.wf-tpl-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(17rem, 1fr)); gap: 0.8rem; }
.wf-tpl-card { background: var(--surface-soft); border: 1px solid var(--border-subtle); border-radius: 0.9rem; padding: 0.95rem 1rem; display: flex; flex-direction: column; gap: 0.5rem; }
</style>"""
