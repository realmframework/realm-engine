"""Unified Gemini-Stitch Luminous Glass aesthetic across chrome, Library, Work OS, Focus, Impact, Workflows, Markdown & Graph."""

SURFACE_STYLES_CSS: str = r"""<style id="realm-surface-polish-styles">
/* Spatial Chrome: Frosted Glass Activity Rail, Drawers, Top Bars & Panels */
#activity-rail, #sidebar, #inspector-sidebar { background-color: var(--surface-glass-strong) !important; background-image: var(--chrome-sheen); backdrop-filter: blur(22px) saturate(135%); -webkit-backdrop-filter: blur(22px) saturate(135%); }
#inspector-sidebar { box-shadow: inset 1px 0 0 var(--specular-edge); }
.wb-zone-bar { background: var(--surface-glass-strong); backdrop-filter: blur(20px) saturate(135%); -webkit-backdrop-filter: blur(20px) saturate(135%); box-shadow: inset 0 1px 0 var(--specular-edge); }
#bottom-panel { background-color: var(--surface-glass-strong); background-image: var(--chrome-sheen); backdrop-filter: blur(22px) saturate(135%); -webkit-backdrop-filter: blur(22px) saturate(135%); }
.wb-zone-tab[aria-selected="true"]::after, .wb-tabs button[aria-selected="true"]::after { box-shadow: 0 0 10px color-mix(in oklab, var(--accent) 68%, transparent); }
.rail-btn[aria-current="page"], .rail-btn.is-active, .drawer-item.is-active, .drawer-item[aria-current="page"], .ft-row.is-active { box-shadow: inset 0 0 0 1px color-mix(in oklab, var(--accent) 26%, transparent), 0 0 14px color-mix(in oklab, var(--accent) 14%, transparent); }
.rail-popover, .workspace-menu, .turn-popover-panel, .header-popover-panel { background-color: var(--surface-glass-strong) !important; backdrop-filter: blur(24px) saturate(135%); -webkit-backdrop-filter: blur(24px) saturate(135%); box-shadow: inset 0 1px 0 var(--specular-edge), var(--dialog-shadow); }
#inspector-sidebar-body > div.rounded-xl, #inspector-sidebar-body details.rounded-xl { background-color: var(--surface-glass) !important; background-image: var(--accent-sheen); box-shadow: var(--card-shadow); }

/* Library, Folder Explorer, Topic Pills & Document Reader */
.library-folders { padding: 0.85rem 0.95rem 0.9rem; border-radius: 1rem; border: 1px solid var(--border-subtle); background: var(--surface-glass); background-image: var(--accent-sheen); backdrop-filter: blur(16px) saturate(125%); -webkit-backdrop-filter: blur(16px) saturate(125%); box-shadow: var(--card-shadow); }
.library-topics button { background: var(--surface-glass); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); transition: border-color 0.16s ease, background-color 0.16s ease, color 0.16s ease, box-shadow 0.16s ease; }
.library-topics button:hover { border-color: color-mix(in oklab, var(--accent) 48%, var(--border)); color: var(--text); }
.library-topics button[aria-pressed="true"] { background: color-mix(in oklab, var(--accent) 16%, var(--surface-glass)); box-shadow: 0 0 14px color-mix(in oklab, var(--accent) 22%, transparent); }
#library-guides article, #results > section.rounded-xl, #results article.rounded-xl { background-color: var(--surface-glass) !important; background-image: var(--accent-sheen); backdrop-filter: blur(16px) saturate(125%); -webkit-backdrop-filter: blur(16px) saturate(125%); box-shadow: var(--card-shadow); transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease; }
#library-guides article:hover { transform: translateY(-2px); border-color: color-mix(in oklab, var(--accent) 50%, var(--border)) !important; box-shadow: var(--card-shadow-hover); }
#library-tools-menu > summary, #library-study-btn, #library-new-note-btn { background-color: var(--surface-glass) !important; backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); box-shadow: inset 0 1px 0 var(--specular-edge); }
#library-upload-btn { backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); box-shadow: 0 0 14px color-mix(in oklab, var(--accent) 16%, transparent); }

/* In-Tab Markdown File View & 2D Graph View */
#center-file-view { background: color-mix(in oklab, var(--background) 64%, transparent); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); }
.cf-bar { background: var(--surface-glass-strong); backdrop-filter: blur(18px) saturate(130%); -webkit-backdrop-filter: blur(18px) saturate(130%); box-shadow: inset 0 1px 0 var(--specular-edge); }
.cf-editor { background: transparent; }
.cf-seg { background: var(--surface-glass-soft); box-shadow: inset 0 1px 0 var(--specular-edge); }
.cf-seg button[aria-pressed="true"] { box-shadow: 0 2px 10px color-mix(in oklab, var(--accent) 34%, transparent); }
.md-pre-wrap, .md-table-wrap { background: color-mix(in oklab, var(--background) 78%, var(--surface-raised)) !important; box-shadow: inset 0 1px 0 var(--specular-edge), 0 6px 18px -10px rgba(2, 4, 12, 0.35); }
#graph-view { background-color: color-mix(in oklab, var(--background) 62%, transparent) !important; }

/* Work OS, Focus & Goals, Time & Impact, and Workflows Studio */
.wb-col, .wb-card, .wb-task-quickbar, .wb-task-row, .wb-project-card, .wb-cal-week-col, .kpi-card, .timer-bar, .impact-card, .roi-table, .goal-card, .plan-card, .wb-empty, .wf-toolbar, .wf-meta-bar, .wf-side-panel, .wf-step-card, .wf-tpl-card, #imp-rate-form { background-color: var(--surface-glass) !important; backdrop-filter: blur(16px) saturate(125%); -webkit-backdrop-filter: blur(16px) saturate(125%); box-shadow: var(--card-shadow); }
.kpi-card, .plan-card, .wb-project-card, .goal-card, .timer-bar, .wb-empty, .wf-side-panel { background-image: var(--accent-sheen); }
.wb-card, .wb-task-row, .wb-project-card, .impact-card, .goal-card, .wf-step-card { transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease; }
.wb-card:hover, .wb-task-row:hover, .wb-project-card:hover, .impact-card:hover, .goal-card:hover, .wf-step-card:hover { transform: translateY(-1px); border-color: color-mix(in oklab, var(--accent) 44%, var(--border)); box-shadow: var(--card-shadow-hover); }
.wb-cal-month { backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); box-shadow: var(--card-shadow); }
.wb-cal-dow { background: var(--surface-glass-strong); }
.wb-cal-cell { background: var(--surface-glass); }
.wb-cal-cell.is-today { background: color-mix(in oklab, var(--accent) 12%, var(--surface-glass)); box-shadow: inset 0 0 0 1px color-mix(in oklab, var(--accent) 32%, transparent); }
.wb-stat-pill, .wb-btn, .wb-select, .wb-input, .wb-textarea, .wf-tb-btn { background-color: var(--surface-glass); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); box-shadow: inset 0 1px 0 var(--specular-edge); }
.wb-btn-primary, .wf-tb-btn[aria-pressed="true"] { background-color: var(--accent); box-shadow: 0 4px 16px color-mix(in oklab, var(--accent) 32%, transparent); }
progress.focus-ring { filter: drop-shadow(0 0 18px color-mix(in oklab, var(--accent) 30%, transparent)); }
.timer-clock { text-shadow: 0 0 18px color-mix(in oklab, var(--accent) 35%, transparent); }
.wf-canvas-viewport { background-color: var(--surface-glass-soft); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); box-shadow: inset 0 1px 0 var(--specular-edge), var(--card-shadow); }
.wf-node-card { background-color: var(--surface-glass-strong); background-image: var(--accent-sheen); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); box-shadow: var(--card-shadow); }
.wf-node-card:hover { box-shadow: var(--card-shadow-hover); }
.wf-port { box-shadow: 0 0 8px color-mix(in oklab, var(--accent) 45%, transparent); }
.wf-zoom-hud { background: var(--surface-glass-strong); box-shadow: inset 0 1px 0 var(--specular-edge), var(--dialog-shadow); }
.theme-custom-locked { opacity: 0.44; filter: grayscale(0.25); }
.theme-custom-locked button, .theme-custom-locked input, .theme-custom-locked label { cursor: not-allowed !important; }

/* Right Sidebar Context-Aware Copilot Pane, Diff Previews & Action Cards */
.right-copilot-pane { flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
.cp-head { flex: none; display: flex; align-items: center; justify-content: space-between; gap: 0.4rem; padding: 0.48rem 0.65rem; border-bottom: 1px solid var(--border-subtle); }
.cp-head-actions { display: inline-flex; align-items: center; gap: 0.32rem; flex-shrink: 0; }
.cp-agent-select { max-width: 7.4rem; height: 1.75rem; font-size: calc(0.76rem * var(--ui-scale, 1)); }
.cp-ctx-badge { display: inline-flex; align-items: center; gap: 0.35rem; min-width: 0; flex: 0 1 auto; padding: 0.2rem 0.55rem; border-radius: 999px; background: color-mix(in oklab, var(--accent) 13%, var(--surface-glass)); border: 1px solid color-mix(in oklab, var(--accent) 34%, transparent); color: var(--accent); font-family: ui-monospace, monospace; font-size: calc(0.72rem * var(--ui-scale, 1)); font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cp-msg-meta { font-family: ui-monospace, monospace; font-size: calc(0.68rem * var(--ui-scale, 1)); color: var(--text-muted); letter-spacing: 0.02em; display: flex; align-items: center; gap: 0.35rem; flex-wrap: wrap; }
.cp-messages { flex: 1 1 auto; min-height: 0; overflow-y: auto; overscroll-behavior: contain; padding: 0.75rem 0.7rem 1rem; display: flex; flex-direction: column; gap: 0.65rem; }
.cp-empty { margin: auto 0; padding: 1.15rem 0.9rem; border-radius: 0.95rem; background: var(--surface-glass); background-image: var(--accent-sheen); border: 1px solid var(--border-subtle); box-shadow: var(--card-shadow); display: flex; flex-direction: column; gap: 0.65rem; }
.cp-empty-title { margin: 0; font-size: calc(0.92rem * var(--ui-scale, 1)); font-weight: 600; color: var(--text); }
.cp-empty-desc { margin: 0; font-size: calc(0.79rem * var(--ui-scale, 1)); color: var(--text-muted); line-height: 1.5; }
.cp-starters { display: flex; flex-direction: column; gap: 0.35rem; margin-top: 0.2rem; }
.cp-starter-btn { width: 100%; text-align: left; padding: 0.48rem 0.68rem; border-radius: 0.65rem; border: 1px solid var(--border-subtle); background: var(--surface-glass-soft); color: var(--text); font-size: calc(0.8rem * var(--ui-scale, 1)); cursor: pointer; transition: border-color 0.14s ease, background-color 0.14s ease; }
.cp-starter-btn:hover { border-color: color-mix(in oklab, var(--accent) 52%, var(--border)); background: color-mix(in oklab, var(--accent) 10%, var(--surface-glass)); }
.cp-msg-user { align-self: flex-end; max-width: 90%; padding: 0.5rem 0.78rem; border-radius: 0.9rem 0.9rem 0.28rem 0.9rem; background: color-mix(in oklab, var(--accent) 16%, var(--surface-glass-strong)); border: 1px solid color-mix(in oklab, var(--accent) 32%, transparent); color: var(--text); font-size: calc(0.84rem * var(--ui-scale, 1)); line-height: 1.5; white-space: pre-wrap; word-break: break-word; }
.cp-msg-ai { display: flex; flex-direction: column; gap: 0.55rem; font-size: calc(0.84rem * var(--ui-scale, 1)); color: var(--prose); line-height: 1.55; }
.cp-action-card { border-radius: 0.85rem; background: var(--surface-glass); background-image: var(--accent-sheen); border: 1px solid color-mix(in oklab, var(--accent) 34%, var(--border-subtle)); box-shadow: var(--card-shadow); padding: 0.7rem 0.78rem; display: flex; flex-direction: column; gap: 0.45rem; }
.cp-action-card.is-applied { border-color: color-mix(in oklab, var(--status-ok) 48%, transparent); }
.cp-action-card.is-dismissed { opacity: 0.5; }
.cp-act-head { display: flex; align-items: center; justify-content: space-between; gap: 0.4rem; }
.cp-act-badge { font-family: ui-monospace, monospace; font-size: calc(0.66rem * var(--ui-scale, 1)); text-transform: uppercase; letter-spacing: 0.05em; padding: 0.12rem 0.45rem; border-radius: 999px; background: color-mix(in oklab, var(--accent) 14%, transparent); color: var(--accent); border: 1px solid color-mix(in oklab, var(--accent) 34%, transparent); }
.cp-act-title { font-size: calc(0.84rem * var(--ui-scale, 1)); font-weight: 600; color: var(--text); line-height: 1.35; }
.cp-act-sum { font-size: calc(0.77rem * var(--ui-scale, 1)); color: var(--text-muted); line-height: 1.4; }
.cp-diff { border-radius: 0.55rem; border: 1px solid var(--border-subtle); background: color-mix(in oklab, var(--background) 80%, transparent); overflow: hidden; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: calc(0.74rem * var(--ui-scale, 1)); line-height: 1.48; max-height: 10.5rem; overflow-y: auto; }
.cp-diff-del { padding: 0.32rem 0.55rem; background: color-mix(in oklab, var(--status-danger) 14%, transparent); color: var(--status-danger); white-space: pre-wrap; word-break: break-word; }
.cp-diff-add { padding: 0.32rem 0.55rem; background: color-mix(in oklab, var(--status-ok) 14%, transparent); color: var(--status-ok); white-space: pre-wrap; word-break: break-word; }
.cp-act-btns { display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap; padding-top: 0.15rem; }
.cp-act-done { font-family: ui-monospace, monospace; font-size: calc(0.74rem * var(--ui-scale, 1)); font-weight: 600; color: var(--status-ok); }
.cp-dock { flex: none; display: flex; flex-direction: column; gap: 0.4rem; padding: 0.52rem 0.65rem 0.62rem; border-top: 1px solid var(--border-subtle); background: var(--surface-glass-strong); }
.cp-dock-row { display: flex; align-items: flex-end; gap: 0.4rem; }
.cp-meta-bar { display: flex; align-items: center; gap: 0.35rem; min-width: 0; }
.cp-meta-select { flex: 1 1 0; min-width: 0; height: 1.72rem; border-radius: 0.5rem; border: 1px solid var(--border-subtle); background-color: var(--surface-glass); color: var(--text-muted); font-size: calc(0.72rem * var(--ui-scale, 1)); padding: 0 0.5rem; outline: none; cursor: pointer; text-overflow: ellipsis; }
.cp-meta-select:hover:not(:disabled) { border-color: color-mix(in oklab, var(--accent) 44%, var(--border)); color: var(--text); }
.cp-meta-select:focus-visible { border-color: var(--accent); color: var(--text); }
.cp-meta-select:disabled { opacity: 0.85; cursor: default; color: var(--accent); border-color: color-mix(in oklab, var(--accent) 32%, transparent); }
.cp-input { flex: 1; min-width: 0; max-height: 7.5rem; resize: none; border-radius: 0.75rem; border: 1px solid var(--border-control); background: color-mix(in oklab, var(--background) 74%, var(--surface-raised)); color: var(--text); padding: 0.48rem 0.7rem; font-size: calc(0.84rem * var(--ui-scale, 1)); line-height: 1.45; outline: none; }
.cp-input:focus { border-color: var(--accent); box-shadow: 0 0 0 2px color-mix(in oklab, var(--accent) 22%, transparent); }
.cp-send { width: 2.05rem; height: 2.05rem; border-radius: 999px; border: 0; background: var(--accent); color: var(--text-on-accent); font-weight: 700; font-size: 0.95rem; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; cursor: pointer; box-shadow: 0 3px 12px color-mix(in oklab, var(--accent) 34%, transparent); transition: filter 0.14s ease; }
.cp-send:hover { filter: brightness(1.08); }
.cp-send.is-stop { background: var(--surface-raised); color: var(--accent); border: 1px solid var(--accent); }

/* Accessibility Guardrails: High Contrast, Forced Colors & Reduced Motion */
@media (prefers-reduced-motion: reduce) {
  #library-guides article:hover, .wb-card:hover, .wb-task-row:hover, .wb-project-card:hover, .impact-card:hover, .goal-card:hover, .wf-step-card:hover { transform: none; }
}
@media (prefers-contrast: more) {
  #activity-rail, #sidebar, #inspector-sidebar, .wb-zone-bar, #bottom-panel, #center-file-view, .library-folders, #library-guides article, .wb-col, .wb-card, .kpi-card, .timer-bar, .impact-card, .roi-table, .goal-card, .plan-card, #imp-rate-form, .wf-toolbar, .wf-meta-bar, .wf-side-panel, .wf-node-card, .cp-empty, .cp-action-card, .cp-dock, .cp-meta-select, dialog { background-color: var(--surface-raised) !important; background-image: none !important; backdrop-filter: none !important; border-color: var(--border-control) !important; }
}
@media (forced-colors: active) {
  #activity-rail, #sidebar, #inspector-sidebar, .wb-zone-bar, #bottom-panel, #center-file-view, .library-folders, #library-guides article, .wb-col, .wb-card, .kpi-card, .timer-bar, .impact-card, .roi-table, .goal-card, .plan-card, #imp-rate-form, .wf-toolbar, .wf-meta-bar, .wf-canvas-viewport, .wf-side-panel, .wf-node-card, .cp-empty, .cp-action-card, .cp-dock, .cp-meta-select, dialog { background-color: Canvas !important; background-image: none !important; backdrop-filter: none !important; box-shadow: none !important; border-color: ButtonBorder !important; }
  progress.focus-ring { filter: none !important; }
  .timer-clock { text-shadow: none !important; }
}
</style>"""
