"""True-DRY VS Code 4-Zone CSS Grid Workbench, Combinable Resizable Panes & Zero-Chrome Embed Mode."""

SPLIT_STYLES_CSS: str = r"""<style id="realm-split-styles">
#workbench-grid { position: relative; z-index: 10; flex: 1 1 auto; min-height: 0; height: calc(100vh - var(--topbar-h, 44px)); height: calc(100dvh - var(--topbar-h, 44px)); display: grid; grid-template-columns: minmax(0, 1fr); grid-template-rows: minmax(0, 1fr); overflow: hidden; }
#workbench-grid.has-right { grid-template-columns: minmax(0, 1fr) 6px minmax(17rem, var(--right-w, 348px)); }
#workbench-center-col { min-width: 0; min-height: 0; height: 100%; display: grid; grid-template-columns: minmax(0, 1fr); grid-template-rows: minmax(0, 1fr); overflow: hidden; }
#workbench-center-col.has-bottom { grid-template-rows: minmax(11rem, var(--editor-h, 58%)) 6px minmax(11rem, 1fr); }
#workbench-center-col.has-bottom.is-bottom-max { grid-template-rows: 0px 0px minmax(0, 1fr); }
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
.wb-zone-bar { flex: none; display: flex; align-items: center; justify-content: space-between; gap: 0.35rem; padding: 0 0.55rem; min-height: 2.25rem; border-bottom: 1px solid var(--border-subtle); background: color-mix(in oklab, var(--background) 70%, transparent); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); }
.wb-tab-strip { display: flex; align-items: stretch; gap: 0.1rem; overflow-x: auto; flex: 1 1 auto; min-inline-size: 0; scrollbar-width: none; scroll-snap-type: inline proximity; }
.wb-tab-strip::-webkit-scrollbar { display: none; }
.wb-zone-tab { position: relative; flex: none; scroll-snap-align: start; display: inline-flex; align-items: center; gap: 0.42rem; padding: 0.46rem 0.72rem; border: 0; border-radius: 0; background: transparent; color: var(--text-muted); font-size: calc(0.81rem * var(--ui-scale, 1)); font-weight: 500; cursor: pointer; max-width: 14rem; white-space: nowrap; transition: color 0.13s ease, background-color 0.13s ease; }
.wb-zone-tab > span:first-child { overflow: hidden; text-overflow: ellipsis; }
.wb-zone-tab:hover { background: var(--hover-tint); color: var(--text); }
.wb-zone-tab[aria-selected="true"] { color: var(--text); }
.wb-zone-tab[aria-selected="true"]::after { content: ""; position: absolute; inset: auto 0 0; border-block-end: 2px solid var(--accent); }
.wb-zone-tab[hidden] { display: none !important; }
.wb-tab-x { width: 1.15rem; height: 1.15rem; border-radius: 999px; display: inline-flex; align-items: center; justify-content: center; font-size: calc(0.7rem * var(--ui-scale, 1)); color: var(--text-subtle); }
.wb-tab-x:hover { background: var(--hover-tint); color: var(--text); }
.wb-bar-actions { display: flex; align-items: center; gap: 0.2rem; flex-shrink: 0; }
.wb-compact-select { max-width: 8.5rem; height: 1.75rem; padding: 0 1.65rem 0 0.55rem; border-radius: 0.5rem; border: 1px solid var(--border-subtle); background-color: var(--surface-raised); color: var(--text); font-size: calc(0.78rem * var(--ui-scale, 1)); font-weight: 500; cursor: pointer; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
#center-split-pane, #bottom-panel, #inspector-sidebar { min-width: 0; min-height: 0; height: 100%; display: flex; flex-direction: column; overflow: hidden; container-type: inline-size; }
#center-split-pane { background: transparent; }
#bottom-panel { background: color-mix(in oklab, var(--surface-raised) 84%, transparent); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); border-top: 1px solid var(--border-subtle); }
#inspector-sidebar { background: var(--surface-raised); border-inline-start: 1px solid var(--border-subtle); }
#center-split-pane[hidden], #center-split-resizer[hidden], #bottom-panel[hidden], #bottom-panel-resizer[hidden], #inspector-sidebar[hidden], #right-sidebar-resizer[hidden], #right-panel-inspector[hidden], #right-panel-doc[hidden] { display: none !important; }
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
.right-doc-toolbar { display: flex; align-items: center; gap: 0.45rem; flex-shrink: 0; }
.right-doc-body { display: flex; flex-direction: column; gap: 0.8rem; }
html.is-embed, html.is-embed body, html.is-embed #main-shell { background: transparent !important; background-color: transparent !important; }
html.is-embed #activity-rail, html.is-embed #sidebar, html.is-embed #sidebar-backdrop, html.is-embed #app-topbar, html.is-embed #ambient-stage, html.is-embed #center-tabbar, html.is-embed #center-split-resizer, html.is-embed #center-split-pane, html.is-embed #bottom-panel-resizer, html.is-embed #bottom-panel, html.is-embed #right-sidebar-resizer, html.is-embed #inspector-sidebar { display: none !important; }
html.is-embed #main-shell { padding-left: 0 !important; height: 100vh; height: 100dvh; }
html.is-embed #workbench-grid { height: 100vh !important; height: 100dvh !important; grid-template-columns: minmax(0, 1fr) !important; }
html.is-embed #workbench-center-col { grid-template-rows: minmax(0, 1fr) !important; }
html.is-embed #center-editor-row { grid-template-columns: minmax(0, 1fr) !important; }
html.is-embed .wb-view { padding: 0.85rem clamp(0.8rem, 2vw, 1.45rem) 2rem !important; }
@media (max-width: 959px) {
  #center-split-btn, #layout-bottom-btn { display: none !important; }
  #center-editor-row.has-split { grid-template-columns: minmax(0, 1fr) !important; }
  #center-split-resizer, #center-split-pane, #bottom-panel-resizer, #bottom-panel, #right-sidebar-resizer { display: none !important; }
  #workbench-center-col.has-bottom { grid-template-rows: minmax(0, 1fr) !important; }
  #workbench-grid.has-right { grid-template-columns: minmax(0, 1fr) !important; }
  #inspector-sidebar:not([hidden]) { position: fixed; right: 0; top: var(--topbar-h, 44px); bottom: 0; width: min(356px, 92vw); z-index: 55; box-shadow: var(--dialog-shadow); }
}
@media (forced-colors: active) {
  .wb-zone-tab[aria-selected="true"]::after { border-color: Highlight; }
  .wb-resizer:focus-visible::before { background: Highlight; }
}
</style>"""
