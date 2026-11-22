"""True-DRY Single-Bar 4-Zone CSS Grid Workbench, Workspace File Tree & 3-Mode Markdown File Tabs."""

SPLIT_STYLES_CSS: str = r"""<style id="realm-split-styles">
#workbench-grid { position: relative; z-index: 10; flex: 1 1 auto; min-height: 0; height: 100vh; height: 100dvh; display: grid; grid-template-columns: minmax(0, 1fr); grid-template-rows: minmax(0, 1fr); overflow: hidden; }
#workbench-grid.has-right { grid-template-columns: minmax(0, 1fr) 6px minmax(18rem, var(--right-w, 348px)); }
#workbench-center-col { position: relative; min-width: 0; min-height: 0; height: 100%; display: grid; grid-template-columns: minmax(0, 1fr); grid-template-rows: minmax(0, 1fr); overflow: hidden; }
#workbench-center-col.has-bottom { grid-template-rows: minmax(11rem, var(--editor-h, 58%)) 6px minmax(11rem, 1fr); }
#workbench-center-col.has-bottom.is-bottom-max { grid-template-rows: 0px minmax(0, 1fr); }
#center-editor-row { min-width: 0; min-height: 0; height: 100%; display: grid; grid-template-columns: minmax(0, 1fr); grid-template-rows: minmax(0, 1fr); overflow: hidden; }
#center-editor-row.has-split { grid-template-columns: minmax(18rem, var(--split-a, 50%)) 6px minmax(18rem, 1fr); }
#center-primary-col { min-width: 0; min-height: 0; height: 100%; display: flex; flex-direction: column; overflow: hidden; }
#main-content { flex: 1 1 auto; min-width: 0; min-height: 0; height: 100%; overflow-y: auto; overscroll-behavior: contain; container: main-pane / inline-size; }
@container main-pane (max-width: 560px) {
  #hero-logo { width: 2.5rem !important; height: 2.5rem !important; margin-bottom: 0.7rem !important; }
  #hero-greeting-text { font-size: clamp(1.35rem, 6.2cqi, 2rem) !important; margin-bottom: 1.15rem !important; }
  #prompt-container { padding: 0.48rem 0.6rem !important; gap: 0.35rem !important; }
  #prompt-container > div:last-child { gap: 0.2rem !important; padding-left: 0 !important; }
  #prompt-upload-btn, #mic-btn, #prompt-submit-btn { width: 2rem !important; height: 2rem !important; }
  #model { max-width: 6.25rem !important; font-size: 0.78rem !important; padding-left: 0.35rem !important; padding-right: 1.4rem !important; background-position: right 0.35rem center !important; }
  #query { min-width: 7.5rem; font-size: 0.875rem !important; }
  #seed-chips { padding-left: 0.25rem !important; margin-top: 0.9rem !important; }
  .seed-chip { font-size: 0.8125rem !important; }
}
#workspace-shell { min-height: 100%; padding-block: 1rem; }
#workspace-shell.h-screen { height: 100% !important; min-height: 0 !important; padding-block: 0 !important; }
.wb-zone-bar { flex: none; display: flex; align-items: center; justify-content: space-between; gap: 0.4rem; padding: 0 0.65rem; height: var(--topbar-h, 44px); min-height: var(--topbar-h, 44px); border-bottom: 1px solid var(--border-subtle); background: color-mix(in oklab, var(--background) 82%, transparent); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); }
.wb-bar-left { display: flex; align-items: center; gap: 0.25rem; min-width: 0; flex: 1 1 auto; height: 100%; }
.wb-tabs-with-add { display: flex; align-items: center; gap: 0.15rem; min-width: 0; flex: 1 1 auto; height: 100%; overflow: hidden; }
.wb-tab-strip { display: flex; align-items: stretch; gap: 0.1rem; overflow-x: auto; flex: 0 1 auto; min-inline-size: 0; height: 100%; scrollbar-width: none; scroll-snap-type: inline proximity; }
.wb-tab-strip::-webkit-scrollbar { display: none; }
.wb-tab-add-btn { flex-shrink: 0; margin-inline-start: 0.15rem; }
.wb-zone-tab { position: relative; flex: none; scroll-snap-align: start; display: inline-flex; align-items: center; gap: 0.38rem; padding: 0 0.72rem; height: 100%; border: 0; border-radius: 0; background: transparent; color: var(--text-muted); font-size: calc(0.83rem * var(--ui-scale, 1)); font-weight: 500; cursor: pointer; max-width: 14rem; white-space: nowrap; transition: color 0.13s ease, background-color 0.13s ease; }
.wb-zone-tab > span { overflow: hidden; text-overflow: ellipsis; }
.wb-zone-tab:hover { background: var(--hover-tint); color: var(--text); }
.wb-zone-tab[aria-selected="true"] { color: var(--text); }
.wb-zone-tab[aria-selected="true"]::after { content: ""; position: absolute; inset: auto 0 0; border-block-end: 2px solid var(--accent); }
.wb-zone-tab[hidden] { display: none !important; }
.wb-tab-dirty { color: var(--accent); font-size: 0.9rem; line-height: 1; }
.wb-tab-x { width: 1.15rem; height: 1.15rem; border-radius: 999px; display: inline-flex; align-items: center; justify-content: center; font-size: calc(0.7rem * var(--ui-scale, 1)); color: var(--text-subtle); flex-shrink: 0; }
.wb-tab-x:hover { background: var(--hover-tint); color: var(--text); }
.wb-bar-actions { display: flex; align-items: center; gap: 0.25rem; flex-shrink: 0; }
.wb-zone-bar .wb-icon-btn { width: 2rem; height: 2rem; border-radius: 0.52rem; }
.wb-compact-select { max-width: 8.5rem; height: 1.8rem; padding: 0 1.65rem 0 0.55rem; border-radius: 0.5rem; border: 1px solid var(--border-subtle); background-color: var(--surface-raised); color: var(--text); font-size: calc(0.78rem * var(--ui-scale, 1)); font-weight: 500; cursor: pointer; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
#workbench-grid:not(.has-right) #center-editor-row:not(.has-split) #center-tabbar,
#workbench-grid:not(.has-right) #center-editor-row.has-split #center-split-pane > .wb-zone-bar,
#workbench-grid:not(.has-right) #workbench-center-col.is-bottom-max #bottom-panel > .wb-zone-bar { padding-right: calc(var(--center-ctrl-w, 32px) + 0.65rem + 40px); }
#workbench-grid.has-right #center-editor-row:not(.has-split) #center-tabbar,
#workbench-grid.has-right #center-editor-row.has-split #center-split-pane > .wb-zone-bar,
#workbench-grid.has-right #workbench-center-col.is-bottom-max #bottom-panel > .wb-zone-bar { padding-right: calc(var(--center-ctrl-w, 32px) + 0.65rem + 4px); }
#workbench-grid.has-right #inspector-sidebar > .wb-zone-bar { padding-right: calc(0.65rem + 36px); }
#right-sidebar-tablist .wb-zone-tab { padding: 0 0.52rem; gap: 0.3rem; font-size: calc(0.8rem * var(--ui-scale, 1)); }
@media (min-width: 960px) { .inspector-mobile-close { display: none !important; } }
#center-split-pane, #bottom-panel, #inspector-sidebar { min-width: 0; min-height: 0; height: 100%; display: flex; flex-direction: column; overflow: hidden; container-type: inline-size; }
#center-split-pane { background: transparent; }
#bottom-panel { background: color-mix(in oklab, var(--surface-raised) 84%, transparent); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); border-top: 1px solid var(--border-subtle); }
#inspector-sidebar { background: var(--surface-raised); border-inline-start: 1px solid var(--border-subtle); }
#center-chat-tabs-group[hidden], #center-chat-actions[hidden], #center-agent-select[hidden], #center-file-view[hidden], #right-panel-files[hidden], #right-panel-copilot[hidden], #right-panel-inspector[hidden], #center-split-pane[hidden], #center-split-resizer[hidden], #bottom-panel[hidden], #bottom-panel-resizer[hidden], #inspector-sidebar[hidden], #right-sidebar-resizer[hidden] { display: none !important; }
.wb-embed-frame { display: block; width: 100%; height: 100%; flex: 1 1 auto; min-height: 0; border: 0; background: transparent; }
body.is-resizing-panes iframe { pointer-events: none !important; }
.wb-resizer { position: relative; background: transparent; display: flex; align-items: center; justify-content: center; touch-action: none; -webkit-user-select: none; user-select: none; outline: none; z-index: 15; }
.wb-resizer::before { content: ""; display: block; background: var(--border-subtle); transition: background-color 0.14s ease, transform 0.14s ease; }
.wb-resizer-v { cursor: col-resize; }
.wb-resizer-v::before { width: 1px; height: 100%; }
.wb-resizer-v:hover::before, .wb-resizer-v:focus-visible::before, .wb-resizer-v.is-dragging::before { background: var(--accent); transform: scaleX(2); }
.wb-resizer-h { cursor: row-resize; }
.wb-resizer-h::before { height: 1px; width: 100%; }
.wb-resizer-h:hover::before, .wb-resizer-h:focus-visible::before, .wb-resizer-h.is-dragging::before { background: var(--accent); transform: scaleY(2); }
.right-sidebar-scroll { flex: 1 1 auto; min-height: 0; overflow-y: auto; overscroll-behavior: contain; padding: 0.9rem 1rem 2rem; display: flex; flex-direction: column; gap: 0.85rem; }
.right-files-pane { flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
.ft-head { display: flex; align-items: center; justify-content: space-between; gap: 0.4rem; padding: 0.55rem 0.65rem 0.4rem 0.85rem; border-bottom: 1px solid var(--border-subtle); flex-shrink: 0; }
.ft-ws-title { font-family: ui-monospace, monospace; font-size: calc(0.72rem * var(--ui-scale, 1)); font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ft-head-actions { display: inline-flex; align-items: center; gap: 0.1rem; flex-shrink: 0; }
.ft-act-btn { width: 1.65rem; height: 1.65rem; border-radius: 0.42rem; }
.ft-tree { flex: 1 1 auto; min-height: 0; overflow-y: auto; overscroll-behavior: contain; padding: 0.35rem 0.35rem 2rem; display: flex; flex-direction: column; gap: 1px; }
.ft-row { width: 100%; display: flex; align-items: center; gap: 0.4rem; padding: 0.34rem 0.5rem; padding-inline-start: calc(0.5rem + var(--ft-depth, 0) * 0.95rem); border: 0; border-radius: 0.48rem; background: transparent; color: var(--text-muted); font-size: calc(0.83rem * var(--ui-scale, 1)); text-align: left; cursor: pointer; transition: background-color 0.1s ease, color 0.1s ease; }
.ft-row:hover { background: var(--hover-tint); color: var(--text); }
.ft-row.is-active { background: color-mix(in oklab, var(--accent) 14%, transparent); color: var(--accent); font-weight: 500; }
.ft-row-name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ft-chev { width: 0.85rem; height: 0.85rem; flex-shrink: 0; opacity: 0.65; transition: transform 0.12s ease; }
.ft-folder[aria-expanded="true"] .ft-chev { transform: rotate(90deg); }
.ft-icon { width: 0.95rem; height: 0.95rem; flex-shrink: 0; opacity: 0.82; }
.ft-ext { font-family: ui-monospace, monospace; font-size: calc(0.68rem * var(--ui-scale, 1)); color: var(--text-subtle); flex-shrink: 0; text-transform: uppercase; }
.center-file-view { display: flex; flex-direction: column; flex: 1 1 auto; width: 100%; height: 100%; min-height: 0; background: var(--background); }
.cf-bar { flex: none; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.55rem; padding: 0.5rem 1rem; border-bottom: 1px solid var(--border-subtle); background: color-mix(in oklab, var(--surface-raised) 76%, transparent); }
.cf-crumb { display: flex; align-items: center; gap: 0.35rem; min-width: 0; font-size: calc(0.8rem * var(--ui-scale, 1)); font-family: ui-monospace, monospace; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cf-controls { display: flex; align-items: center; gap: 0.45rem; flex-wrap: wrap; }
.cf-seg { display: inline-flex; align-items: center; padding: 0.16rem; border-radius: 0.6rem; background: var(--surface-soft); border: 1px solid var(--border-subtle); gap: 0.12rem; }
.cf-seg button { padding: 0.28rem 0.62rem; border: 0; border-radius: 0.45rem; background: transparent; color: var(--text-muted); font-size: calc(0.78rem * var(--ui-scale, 1)); font-weight: 500; cursor: pointer; white-space: nowrap; transition: background-color 0.12s ease, color 0.12s ease; }
.cf-seg button:hover { color: var(--text); }
.cf-seg button[aria-pressed="true"] { background: var(--accent); color: var(--text-on-accent); font-weight: 600; }
.cf-body { flex: 1 1 auto; min-height: 0; display: grid; grid-template-columns: minmax(0, 1fr); overflow: hidden; }
.cf-body.is-split { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }
.cf-editor-pane { display: flex; flex-direction: column; min-height: 0; height: 100%; border-inline-end: 1px solid var(--border-subtle); }
.cf-body:not(.is-split) .cf-editor-pane { border-inline-end: 0; }
.cf-editor { flex: 1 1 auto; width: 100%; height: 100%; min-height: 0; resize: none; border: 0; outline: none; padding: 1.25rem 1.4rem; background: var(--background); color: var(--text); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: calc(0.88rem * var(--ui-scale, 1)); line-height: 1.65; tab-size: 2; }
.cf-body.is-split .cf-editor { padding: 1.1rem 1.15rem; }
.cf-preview-pane { min-width: 0; min-height: 0; height: 100%; overflow-y: auto; overscroll-behavior: contain; padding: 1.5rem clamp(1.25rem, 3vw, 2.75rem) 4rem; }
.cf-body.is-split .cf-preview-pane { padding: 1.2rem 1.35rem 3.5rem; }
.cf-preview-inner { width: 100%; min-width: 0; max-width: var(--reading-width, 52rem); margin: 0 auto; display: flex; flex-direction: column; gap: 0.9rem; }
.cf-status { font-family: ui-monospace, monospace; font-size: calc(0.74rem * var(--ui-scale, 1)); color: var(--text-subtle); }
@container main-pane (max-width: 560px) {
  .cf-body.is-split { grid-template-columns: minmax(0, 1fr); grid-template-rows: minmax(0, 1fr) minmax(0, 1fr); }
  .cf-body.is-split .cf-editor-pane { border-inline-end: 0; border-bottom: 1px solid var(--border-subtle); }
}
html.is-embed:not(.is-split-chat), html.is-embed:not(.is-split-chat) body, html.is-embed:not(.is-split-chat) #main-shell { background: transparent !important; background-color: transparent !important; }
html.is-embed:not(.is-split-chat) #ambient-stage { display: none !important; }
html.is-embed #activity-rail, html.is-embed #sidebar, html.is-embed #sidebar-backdrop, html.is-embed #wb-right-toggle-wrap, html.is-embed #wb-center-controls, html.is-embed #center-tabbar, html.is-embed #center-split-resizer, html.is-embed #center-split-pane, html.is-embed #bottom-panel-resizer, html.is-embed #bottom-panel, html.is-embed #right-sidebar-resizer, html.is-embed #inspector-sidebar { display: none !important; }
html.is-embed #main-shell { padding-left: 0 !important; height: 100vh; height: 100dvh; }
html.is-embed #workbench-grid { height: 100vh !important; height: 100dvh !important; grid-template-columns: minmax(0, 1fr) !important; }
html.is-embed #workbench-center-col { grid-template-rows: minmax(0, 1fr) !important; }
html.is-embed #center-editor-row { grid-template-columns: minmax(0, 1fr) !important; }
html.is-embed .wb-view { padding: 0.85rem clamp(0.8rem, 2vw, 1.45rem) 2rem !important; }
@media (max-width: 959px) {
  #center-split-btn, #layout-bottom-btn, #wb-center-controls { display: none !important; }
  #center-tabbar { padding-right: calc(0.65rem + 36px) !important; }
  #center-editor-row.has-split { grid-template-columns: minmax(0, 1fr) !important; }
  #center-split-resizer, #center-split-pane, #bottom-panel-resizer, #bottom-panel, #right-sidebar-resizer { display: none !important; }
  #workbench-center-col.has-bottom { grid-template-rows: minmax(0, 1fr) !important; }
  #workbench-grid.has-right { grid-template-columns: minmax(0, 1fr) !important; }
  #inspector-sidebar:not([hidden]) { position: fixed; right: 0; top: 0; bottom: 0; width: min(356px, 92vw); z-index: 55; box-shadow: var(--dialog-shadow); }
  .cf-body.is-split { grid-template-columns: minmax(0, 1fr); grid-template-rows: 1fr 1fr; }
}
@media (forced-colors: active) {
  .wb-zone-tab[aria-selected="true"]::after { border-color: Highlight; }
  .wb-resizer:focus-visible::before { background: Highlight; }
}
</style>"""
