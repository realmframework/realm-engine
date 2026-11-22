"""Theme-adaptive CSS for Vertical Dual Chat & Horizontal/Vertical Board/Guide Split Screen."""

SPLIT_STYLES_CSS: str = r"""<style id="realm-split-styles">
#split-resizer[hidden], #split-pane-b[hidden], #split-chat-body[hidden], #split-guide-body[hidden] { display: none !important; }
#top-right-tools { position: fixed; right: 1rem; top: 1rem; z-index: 40; display: flex; align-items: center; gap: 0.45rem; }
#split-toggle-btn { height: 2.25rem; width: 2.25rem; border-radius: 999px; background: var(--surface-raised); color: var(--text-muted); box-shadow: inset 0 0 0 1px var(--border); display: inline-flex; align-items: center; justify-content: center; border: 0; cursor: pointer; transition: color 0.15s ease, box-shadow 0.15s ease, background-color 0.15s ease; }
#split-toggle-btn:hover, #split-toggle-btn[aria-expanded="true"], #split-toggle-btn.is-active { color: var(--accent); box-shadow: inset 0 0 0 1px var(--accent); }
#split-mode-menu { position: fixed; inset: auto; top: 3.75rem; right: 1rem; margin: 0; width: min(17.5rem, calc(100vw - 2rem)); border-radius: 0.95rem; background: var(--surface-raised); color: var(--text); border: 1px solid var(--border); padding: 0.4rem; box-shadow: var(--dialog-shadow); }
.split-menu-item { width: 100%; display: flex; align-items: center; gap: 0.6rem; padding: 0.55rem 0.7rem; border-radius: 0.65rem; border: 0; background: transparent; color: var(--text); font-size: calc(0.875rem * var(--ui-scale, 1)); text-align: left; cursor: pointer; transition: background-color 0.15s ease, color 0.15s ease; }
.split-menu-item:hover { background: var(--hover-tint); color: var(--accent); }
.split-menu-item.is-danger { color: var(--status-danger); border-top: 1px solid var(--border-subtle); margin-top: 0.25rem; padding-top: 0.65rem; border-radius: 0 0 0.65rem 0.65rem; }
#main-content.is-split-vertical { display: grid !important; grid-template-columns: minmax(18rem, var(--split-a, 50%)) 8px minmax(18rem, 1fr); grid-template-rows: minmax(0, 1fr); height: 100vh; height: 100dvh; overflow: hidden; }
#main-content.is-split-horizontal { display: grid !important; grid-template-rows: minmax(13rem, var(--split-a, 52%)) 8px minmax(13rem, 1fr); grid-template-columns: minmax(0, 1fr); height: 100vh; height: 100dvh; overflow: hidden; }
#main-content.is-split-active > #workspace-shell, #main-content.is-split-active > #work-board-view, #main-content.is-split-active > #focus-view, #main-content.is-split-active > #impact-view { min-width: 0; min-height: 0; height: 100% !important; overflow-y: auto; }
#main-content.is-split-active > #workspace-shell { padding-top: 0.25rem; }
#main-content.is-split-active > #work-board-view, #main-content.is-split-active > #focus-view, #main-content.is-split-active > #impact-view { min-height: 0 !important; padding-top: 1.25rem; padding-bottom: 2rem; }
#split-resizer { position: relative; background: transparent; display: flex; align-items: center; justify-content: center; touch-action: none; -webkit-user-select: none; user-select: none; outline: none; }
#split-resizer::before { content: ""; display: block; border-radius: 999px; background: var(--border); transition: background-color 0.15s ease, transform 0.15s ease; }
#main-content.is-split-vertical > #split-resizer { cursor: col-resize; }
#main-content.is-split-vertical > #split-resizer::before { width: 2px; height: 100%; }
#main-content.is-split-horizontal > #split-resizer { cursor: row-resize; }
#main-content.is-split-horizontal > #split-resizer::before { height: 2px; width: 100%; }
#split-resizer:hover::before, #split-resizer:focus-visible::before, #split-resizer.is-dragging::before { background: var(--accent); }
#split-pane-b { min-width: 0; min-height: 0; height: 100%; display: flex; flex-direction: column; background: color-mix(in oklab, var(--surface-raised) 68%, var(--background)); border-inline-start: 1px solid var(--border-subtle); overflow: hidden; }
#main-content.is-split-horizontal > #split-pane-b { border-inline-start: 0; border-top: 1px solid var(--border-subtle); }
.split-pane-header { flex: none; display: flex; flex-wrap: nowrap; align-items: center; justify-content: space-between; gap: 0.35rem; padding: 0.55rem 0.75rem; padding-inline-end: 3.75rem; border-bottom: 1px solid var(--border-subtle); background: var(--surface-raised); overflow-x: auto; }
#main-content.is-split-horizontal .split-pane-header { padding-inline-end: 0.9rem; }
.split-pane-group { display: flex; align-items: center; gap: 0.3rem; min-width: 0; flex-wrap: nowrap; }
.split-seg { display: inline-flex; padding: 0.15rem; border-radius: 0.6rem; background: var(--surface-soft); border: 1px solid var(--border-subtle); flex-shrink: 0; }
.split-seg button { padding: 0.25rem 0.55rem; border-radius: 0.45rem; border: 0; background: transparent; color: var(--text-muted); font-size: calc(0.8125rem * var(--ui-scale, 1)); font-weight: 500; cursor: pointer; white-space: nowrap; }
.split-seg button[aria-pressed="true"] { background: var(--accent); color: var(--text-on-accent); font-weight: 600; }
.split-mini-select { max-width: 8.25rem; min-width: 4.5rem; background: var(--surface-soft); color: var(--text); border: 1px solid var(--border); border-radius: 0.55rem; padding: 0.28rem 1.75rem 0.28rem 0.5rem; font-size: calc(0.8125rem * var(--ui-scale, 1)); outline: none; overflow: hidden; text-overflow: ellipsis; }
.split-mini-select:focus { border-color: var(--accent); }
#split-chat-body, #split-guide-body { flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
#split-chat-stream { flex: 1 1 auto; min-height: 0; overflow-y: auto; padding: 1rem 1.15rem; display: flex; flex-direction: column; gap: 1.1rem; }
.split-empty-chat { margin: auto; text-align: center; max-width: 22rem; color: var(--text-muted); font-size: calc(0.9rem * var(--ui-scale, 1)); line-height: 1.55; }
.split-turn { display: flex; flex-direction: column; gap: 0.55rem; padding-bottom: 0.9rem; border-bottom: 1px solid var(--border-subtle); }
.split-turn:last-child { border-bottom: 0; }
.split-user-bubble { align-self: flex-end; max-width: 88%; padding: 0.55rem 0.9rem; border-radius: 1rem; background: var(--surface-raised); border: 1px solid var(--border); color: var(--text); font-size: calc(0.9375rem * var(--ui-scale, 1)); line-height: 1.5; white-space: pre-wrap; word-break: break-word; }
.split-turn-actions { display: flex; align-items: center; gap: 0.35rem; flex-wrap: wrap; margin-top: 0.2rem; }
.split-chat-dock { flex: none; padding: 0.65rem 0.9rem 0.85rem; border-top: 1px solid var(--border-subtle); background: var(--surface-raised); }
.split-pill { display: flex; align-items: flex-end; gap: 0.45rem; padding: 0.45rem 0.55rem 0.45rem 0.85rem; border-radius: 1.15rem; background: var(--background); border: 1px solid var(--border-control); }
.split-pill:focus-within { border-color: var(--accent); }
#split-query { flex: 1; min-width: 0; resize: none; max-height: 7rem; border: 0; outline: none; background: transparent; color: var(--text); font-size: calc(0.9375rem * var(--ui-scale, 1)); line-height: 1.45; padding: 0.2rem 0; }
#split-guide-scroll { flex: 1 1 auto; min-height: 0; overflow-y: auto; padding: 1rem 1.25rem 2rem; display: flex; flex-direction: column; gap: 0.9rem; }
@media (max-width: 959px) {
  #split-toggle-btn { display: none !important; }
  #main-content.is-split-vertical, #main-content.is-split-horizontal { display: flex !important; flex-direction: column; height: auto; overflow: visible; }
  #split-resizer, #split-pane-b { display: none !important; }
}
</style>"""
