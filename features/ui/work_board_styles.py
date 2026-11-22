"""Theme-adaptive CSS for Projects, Kanban Board, Task Manager, and Local Calendar."""

WORK_BOARD_STYLES_CSS: str = r"""<style id="realm-work-board-styles">
#work-board-view [hidden] { display: none !important; }
.wb-view { width: 100%; min-height: 100vh; padding: 1.75rem clamp(1rem, 2.5vw, 2.25rem) 4.5rem; display: flex; flex-direction: column; gap: 1.25rem; color: var(--text); }
.wb-view.hidden { display: none !important; }
.wb-header { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.85rem; padding-inline-end: 3.25rem; }
.wb-title-row { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.wb-title { margin: 0; font-size: calc(1.5rem * var(--ui-scale, 1)); font-weight: 600; letter-spacing: -0.02em; color: var(--text); }
.wb-stat-strip { display: flex; flex-wrap: wrap; gap: 0.45rem; align-items: center; }
.wb-stat-pill { font-size: calc(0.8125rem * var(--ui-scale, 1)); font-family: ui-monospace, monospace; padding: 0.25rem 0.65rem; border-radius: 999px; background: var(--surface-raised); border: 1px solid var(--border-subtle); color: var(--text-muted); }
.wb-stat-pill.is-warn { color: var(--status-danger); border-color: color-mix(in oklab, var(--status-danger) 42%, transparent); background: color-mix(in oklab, var(--status-danger) 10%, var(--surface-raised)); }
.wb-stat-pill.is-accent { color: var(--accent); border-color: color-mix(in oklab, var(--accent) 42%, transparent); }
.wb-controls { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; }
.wb-select, .wb-input, .wb-textarea { background-color: var(--surface-raised); color: var(--text); border: 1px solid var(--border-control); border-radius: 0.65rem; padding: 0.48rem 0.75rem; font-size: calc(0.875rem * var(--ui-scale, 1)); outline: none; transition: border-color 0.15s ease; }
.wb-select:focus, .wb-input:focus, .wb-textarea:focus { border-color: var(--accent); }
.wb-btn { display: inline-flex; align-items: center; justify-content: center; gap: 0.4rem; padding: 0.5rem 0.85rem; border-radius: 0.7rem; font-size: calc(0.875rem * var(--ui-scale, 1)); font-weight: 500; border: 1px solid var(--border); background: var(--surface-raised); color: var(--text); cursor: pointer; transition: border-color 0.15s ease, background-color 0.15s ease; white-space: nowrap; }
.wb-btn:hover { border-color: var(--accent); background: var(--hover-tint); }
.wb-btn-primary { background: var(--accent); color: var(--text-on-accent); border-color: transparent; font-weight: 600; }
.wb-btn-primary:hover { filter: brightness(1.08); background: var(--accent); border-color: transparent; }
.wb-btn-danger { color: var(--status-danger); border-color: color-mix(in oklab, var(--status-danger) 40%, transparent); }
.wb-btn-sm { padding: 0.32rem 0.62rem; font-size: calc(0.8125rem * var(--ui-scale, 1)); border-radius: 0.55rem; }
.wb-icon-btn { display: inline-flex; align-items: center; justify-content: center; width: 1.85rem; height: 1.85rem; border-radius: 0.5rem; border: 1px solid transparent; background: transparent; color: var(--text-muted); cursor: pointer; transition: background-color 0.15s ease, color 0.15s ease; }
.wb-icon-btn:hover { background: var(--hover-tint); color: var(--text); }
.wb-tabs { display: flex; flex: none; gap: 1.25rem; overflow-x: auto; border-block-end: 1px solid var(--border-subtle); scrollbar-width: thin; }
.wb-tabs button { position: relative; flex: none; white-space: nowrap; padding: 0.65rem 0.15rem; font-size: calc(0.9375rem * var(--ui-scale, 1)); font-weight: 500; color: var(--text-muted); background: transparent; border: 0; cursor: pointer; }
.wb-tabs button:hover { color: var(--text); }
.wb-tabs button[aria-selected="true"] { color: var(--accent); }
.wb-tabs button[aria-selected="true"]::after { content: ""; position: absolute; inset: auto 0 0; border-block-end: 2px solid currentColor; }
.wb-kanban-wrap { display: flex; gap: 0.75rem; overflow-x: auto; align-items: flex-start; padding: 0.25rem 0.75rem 1.25rem 0.25rem; scrollbar-width: thin; }
.wb-col { flex: 1 0 12.25rem; max-width: 21rem; min-width: 12rem; background: color-mix(in oklab, var(--surface-raised) 88%, transparent); border: 1px solid var(--border-subtle); border-radius: 1rem; padding: 0.8rem; display: flex; flex-direction: column; gap: 0.65rem; transition: border-color 0.15s ease, box-shadow 0.15s ease; }
.wb-col.is-drop-over { border-color: var(--accent); box-shadow: 0 0 0 2px color-mix(in oklab, var(--accent) 30%, transparent); }
.wb-col-head { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; }
.wb-col-title-wrap { display: flex; align-items: center; gap: 0.5rem; min-width: 0; }
.wb-dot { width: 0.625rem; height: 0.625rem; border-radius: 999px; flex-shrink: 0; }
.wb-col-title { font-size: calc(0.9375rem * var(--ui-scale, 1)); font-weight: 600; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.wb-col-count { font-size: calc(0.75rem * var(--ui-scale, 1)); font-family: ui-monospace, monospace; color: var(--text-subtle); padding: 0.1rem 0.45rem; border-radius: 999px; background: var(--surface-pill); }
.wb-col-list { display: flex; flex-direction: column; gap: 0.55rem; min-height: 3.5rem; }
.wb-card { background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: 0.85rem; padding: 0.78rem 0.85rem; display: flex; flex-direction: column; gap: 0.5rem; transition: border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease; }
.wb-card:hover { border-color: var(--border); box-shadow: var(--dialog-shadow); }
.wb-card.is-dragging { opacity: 0.5; transform: scale(1.01); }
.wb-card-top { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: flex-start; gap: 0.45rem; }
.wb-drag-handle { display: inline-flex; align-items: center; justify-content: center; width: 1.4rem; height: 1.5rem; border-radius: 0.4rem; color: var(--text-subtle); cursor: grab; touch-action: none; -webkit-user-select: none; user-select: none; }
.wb-drag-handle:hover { color: var(--text); background: var(--hover-tint); }
.wb-drag-handle:active { cursor: grabbing; }
.wb-card-title { background: transparent; border: 0; padding: 0; text-align: left; font: inherit; font-size: calc(0.9375rem * var(--ui-scale, 1)); font-weight: 500; color: var(--text); cursor: pointer; line-height: 1.4; word-break: break-word; }
.wb-card-title:hover { color: var(--accent); }
.wb-card-title.is-done { text-decoration: line-through; color: var(--text-muted); }
.wb-card-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 0.35rem; font-size: calc(0.75rem * var(--ui-scale, 1)); }
.wb-chip { display: inline-flex; align-items: center; gap: 0.25rem; padding: 0.14rem 0.5rem; border-radius: 999px; border: 1px solid var(--border-subtle); background: var(--surface-pill); color: var(--text-muted); font-size: calc(0.75rem * var(--ui-scale, 1)); }
.wb-chip.prio-urgent { color: var(--status-danger); border-color: color-mix(in oklab, var(--status-danger) 45%, transparent); background: color-mix(in oklab, var(--status-danger) 12%, transparent); font-weight: 600; }
.wb-chip.prio-high { color: var(--status-warn); border-color: color-mix(in oklab, var(--status-warn) 45%, transparent); background: color-mix(in oklab, var(--status-warn) 12%, transparent); }
.wb-chip.prio-low { color: var(--text-subtle); }
.wb-chip.is-overdue { color: var(--status-danger); border-color: color-mix(in oklab, var(--status-danger) 45%, transparent); font-weight: 600; }
.wb-chip.is-today { color: var(--accent); border-color: color-mix(in oklab, var(--accent) 45%, transparent); font-weight: 600; }
.wb-card-move { display: inline-flex; gap: 0.1rem; flex-shrink: 0; }
.wb-quick-add { display: flex; gap: 0.35rem; align-items: center; margin-top: 0.25rem; }
.wb-quick-add input { flex: 1; min-width: 0; padding: 0.42rem 0.65rem; font-size: calc(0.8125rem * var(--ui-scale, 1)); }
.wb-add-col-card { flex: 0 0 11.75rem; border: 1px dashed var(--border); border-radius: 1rem; padding: 0.8rem; display: flex; flex-direction: column; gap: 0.55rem; background: transparent; }
.wb-list-toolbar { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.65rem; margin-bottom: 0.85rem; }
.wb-filter-pills { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.wb-pill-btn { padding: 0.38rem 0.78rem; border-radius: 999px; border: 1px solid var(--border); background: transparent; color: var(--text-muted); font-size: calc(0.8125rem * var(--ui-scale, 1)); cursor: pointer; }
.wb-pill-btn[aria-pressed="true"] { background: color-mix(in oklab, var(--accent) 16%, transparent); border-color: var(--accent); color: var(--accent); font-weight: 600; }
.wb-task-quickbar { display: grid; grid-template-columns: minmax(12rem, 1fr) auto auto auto auto; gap: 0.5rem; margin-bottom: 1rem; padding: 0.75rem; border-radius: 0.9rem; background: var(--surface-raised); border: 1px solid var(--border-subtle); }
@media (max-width: 820px) { .wb-task-quickbar { grid-template-columns: 1fr 1fr; } .wb-task-quickbar > :first-child { grid-column: 1 / -1; } }
.wb-task-row { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 0.75rem; padding: 0.7rem 0.9rem; border-radius: 0.85rem; background: var(--surface-raised); border: 1px solid var(--border-subtle); margin-bottom: 0.5rem; }
.wb-task-row:hover { border-color: var(--border); }
.wb-check-btn { width: 1.35rem; height: 1.35rem; border-radius: 999px; border: 1.5px solid var(--border-control); background: transparent; color: var(--text-on-accent); display: inline-flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0; }
.wb-check-btn[aria-pressed="true"] { background: var(--status-ok); border-color: var(--status-ok); }
.wb-cal-toolbar { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.7rem; margin-bottom: 0.85rem; }
.wb-cal-month { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 1px; background: var(--border-subtle); border: 1px solid var(--border-subtle); border-radius: 0.95rem; overflow: hidden; }
.wb-cal-dow { background: var(--surface-soft); color: var(--text-muted); font-size: calc(0.75rem * var(--ui-scale, 1)); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; padding: 0.55rem 0.65rem; text-align: center; }
.wb-cal-cell { min-width: 0; min-height: 7.2rem; background: var(--surface-raised); padding: 0.45rem; display: flex; flex-direction: column; gap: 0.28rem; transition: background-color 0.15s ease; }
.wb-cal-cell.is-other-month { opacity: 0.48; }
.wb-cal-cell.is-today { background: color-mix(in oklab, var(--accent) 8%, var(--surface-raised)); }
.wb-cal-cell.is-drop-over { outline: 2px solid var(--accent); outline-offset: -2px; background: color-mix(in oklab, var(--accent) 14%, var(--surface-raised)); }
.wb-cal-day-num { display: flex; align-items: center; justify-content: space-between; font-size: calc(0.8125rem * var(--ui-scale, 1)); font-weight: 600; color: var(--text-muted); }
.wb-cal-day-num.is-today span:first-child { background: var(--accent); color: var(--text-on-accent); padding: 0.08rem 0.45rem; border-radius: 999px; }
.wb-cal-item { display: flex; align-items: center; gap: 0.3rem; width: 100%; min-width: 0; text-align: left; padding: 0.2rem 0.42rem; border-radius: 0.42rem; border: 0; font-size: calc(0.75rem * var(--ui-scale, 1)); line-height: 1.3; cursor: pointer; overflow: hidden; white-space: nowrap; background: color-mix(in oklab, var(--accent) 14%, var(--surface-soft)); color: var(--text); }
.wb-cal-item > span:last-child { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.wb-cal-item.kind-focus { background: color-mix(in oklab, #A78BFA 20%, var(--surface-soft)); }
.wb-cal-item.kind-milestone { background: color-mix(in oklab, #F59E0B 20%, var(--surface-soft)); }
.wb-cal-item.kind-deadline { background: color-mix(in oklab, var(--status-danger) 16%, var(--surface-soft)); }
.wb-cal-week { display: grid; grid-template-columns: repeat(7, minmax(7.5rem, 1fr)); gap: 0.6rem; overflow-x: auto; }
.wb-cal-week-col { background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: 0.85rem; padding: 0.65rem; min-height: 18rem; display: flex; flex-direction: column; gap: 0.4rem; }
.wb-cal-week-col.is-today { border-color: var(--accent); }
.wb-projects-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(18rem, 1fr)); gap: 0.9rem; }
.wb-project-card { background: var(--surface-raised); border: 1px solid var(--border-subtle); border-radius: 1rem; padding: 1rem 1.1rem; display: flex; flex-direction: column; gap: 0.65rem; }
.wb-progress-track { width: 100%; height: 0.45rem; border-radius: 999px; background: var(--surface-pill); overflow: hidden; }
.wb-progress-fill { height: 100%; border-radius: 999px; transition: width 0.2s ease; }
.wb-dialog { margin: auto; width: calc(100% - 2rem); max-width: 34rem; max-height: 88vh; overflow-y: auto; border-radius: 1.15rem; background: var(--surface-raised); color: var(--text); border: 1px solid var(--border); padding: 1.4rem; box-shadow: var(--dialog-shadow); }
.wb-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
@media (max-width: 560px) { .wb-form-grid { grid-template-columns: 1fr; } }
.wb-field { display: flex; flex-direction: column; gap: 0.3rem; }
.wb-field label { font-size: calc(0.8125rem * var(--ui-scale, 1)); color: var(--text-muted); font-weight: 500; }
.wb-subtask-row { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 0.5rem; padding: 0.35rem 0.5rem; border-radius: 0.55rem; background: var(--surface-soft); }
.wb-empty { padding: 2.25rem 1rem; text-align: center; color: var(--text-muted); font-size: calc(0.9375rem * var(--ui-scale, 1)); border: 1px dashed var(--border-subtle); border-radius: 1rem; }
</style>"""
