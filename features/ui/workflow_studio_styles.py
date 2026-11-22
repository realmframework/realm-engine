"""Theme-adaptive CSS for Native Local Workflow & Agent Pipeline Studio (Canvas + Step View)."""

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
.wf-workspace-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(19rem, 23.5rem); gap: 0.9rem; align-items: start; min-height: 31rem; }
@media (max-width: 1080px) { .wf-workspace-grid { grid-template-columns: 1fr; } }
.wf-canvas-viewport { position: relative; overflow: auto; min-height: 31rem; max-height: 68vh; border-radius: 1rem; border: 1px solid var(--border-subtle); background-color: var(--surface-soft); background-image: radial-gradient(color-mix(in oklab, var(--text-subtle) 28%, transparent) 1px, transparent 1px); background-size: 20px 20px; scrollbar-width: thin; }
.wf-canvas-stage { position: relative; min-width: 920px; min-height: 440px; }
.wf-svg-layer { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; overflow: visible; }
.wf-edge-path { fill: none; stroke: color-mix(in oklab, var(--accent) 62%, var(--border)); stroke-width: 2.25; }
.wf-edge-path.is-true { stroke: var(--status-ok); }
.wf-edge-path.is-false { stroke: var(--status-danger); stroke-dasharray: 6 4; }
.wf-edge-label { font-family: ui-monospace, monospace; font-size: 11px; fill: var(--text-muted); }
.wf-node-card { position: absolute; width: 12.25rem; border-radius: 0.9rem; background: var(--surface-raised); border: 1.5px solid var(--border); box-shadow: 0 6px 18px rgba(4, 6, 15, 0.16); padding: 0.6rem 0.72rem; display: flex; flex-direction: column; gap: 0.32rem; cursor: pointer; }
.wf-node-card.is-selected { border-color: var(--accent); box-shadow: 0 0 0 2px color-mix(in oklab, var(--accent) 28%, transparent); }
.wf-node-card.is-running { border-color: var(--accent); box-shadow: 0 0 0 4px color-mix(in oklab, var(--accent) 32%, transparent); }
.wf-node-card.is-completed { border-color: var(--status-ok); }
.wf-node-card.is-failed { border-color: var(--status-danger); }
.wf-node-card.is-skipped { opacity: 0.56; border-style: dashed; }
.wf-node-head { display: flex; align-items: center; justify-content: space-between; gap: 0.3rem; }
.wf-node-badge { font-family: ui-monospace, monospace; font-size: calc(0.68rem * var(--ui-scale, 1)); text-transform: uppercase; letter-spacing: 0.04em; padding: 0.14rem 0.45rem; border-radius: 999px; background: var(--surface-soft); color: var(--accent); border: 1px solid var(--border-subtle); white-space: nowrap; flex-shrink: 0; max-width: 100%; overflow: hidden; text-overflow: ellipsis; }
.wf-drag-handle { cursor: grab; touch-action: none; -webkit-user-select: none; user-select: none; border: 0; background: transparent; color: var(--text-subtle); width: 1.7rem; height: 1.7rem; border-radius: 0.45rem; display: inline-flex; align-items: center; justify-content: center; }
.wf-drag-handle.dragging { cursor: grabbing; color: var(--accent); }
.wf-node-title { font-size: calc(0.9rem * var(--ui-scale, 1)); font-weight: 600; color: var(--text); line-height: 1.3; word-break: break-word; }
.wf-node-sub { font-size: calc(0.78rem * var(--ui-scale, 1)); color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.wf-step-list { display: flex; flex-direction: column; gap: 0.55rem; padding: 0.9rem; }
.wf-step-card { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; padding: 0.85rem 1rem; border-radius: 0.9rem; background: var(--surface-raised); border: 1.5px solid var(--border-subtle); cursor: pointer; }
.wf-step-card.is-selected { border-color: var(--accent); }
.wf-step-card.is-completed { border-color: var(--status-ok); }
.wf-step-card.is-running { border-color: var(--accent); }
.wf-side-panel { background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: 1rem; padding: 0.95rem 1.05rem; display: flex; flex-direction: column; gap: 0.75rem; max-height: 68vh; overflow-y: auto; }
.wf-run-step { padding: 0.65rem 0.75rem; border-radius: 0.75rem; background: var(--surface-soft); border: 1px solid var(--border-subtle); display: flex; flex-direction: column; gap: 0.28rem; font-size: calc(0.84rem * var(--ui-scale, 1)); }
.wf-tpl-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(17rem, 1fr)); gap: 0.8rem; }
.wf-tpl-card { background: var(--surface-soft); border: 1px solid var(--border-subtle); border-radius: 0.9rem; padding: 0.95rem 1rem; display: flex; flex-direction: column; gap: 0.5rem; }
</style>"""