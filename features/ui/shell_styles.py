"""Codex-inspired Two-Tier Spatial Shell CSS: 52px Activity Rail, Context Drawer, Calm Top Bar & Multi-Tab Workbench."""

SHELL_STYLES_CSS: str = r"""<style id="realm-spatial-shell-styles">
:root { --rail-w: 52px; --drawer-w: 248px; --topbar-h: 44px; --shell-left: calc(var(--rail-w) + var(--drawer-w)); }
body.drawer-collapsed { --shell-left: var(--rail-w); }
#activity-rail { position: fixed; inset-block: 0; inset-inline-start: 0; width: var(--rail-w); z-index: 60; background: var(--surface-raised); border-inline-end: 1px solid var(--border-subtle); display: flex; flex-direction: column; align-items: center; padding: 0.55rem 0 0.7rem; gap: 0.25rem; }
.rail-btn { position: relative; width: 38px; height: 38px; border-radius: 0.65rem; border: 0; background: transparent; color: var(--text-muted); display: inline-flex; align-items: center; justify-content: center; cursor: pointer; transition: background-color 0.14s ease, color 0.14s ease; }
.rail-btn:hover { background: var(--hover-tint); color: var(--text); }
.rail-btn[aria-current="page"], .rail-btn.is-active { background: color-mix(in oklab, var(--accent) 14%, transparent); color: var(--accent); }
.rail-btn[aria-current="page"]::before { content: ""; position: absolute; inset-inline-start: -7px; inset-block: 7px; width: 3px; border-radius: 0 3px 3px 0; background: var(--accent); }
.rail-badge-dot { position: absolute; top: 6px; right: 6px; width: 7px; height: 7px; border-radius: 999px; background: var(--accent); border: 1.5px solid var(--surface-raised); }
.rail-badge-dot[hidden] { display: none !important; }
.rail-divider { width: 22px; height: 1px; background: var(--border-subtle); margin: 0.2rem 0; }
.rail-spacer { flex: 1; }
.rail-popover { position: fixed; inset: auto; margin: 0; min-width: 14.5rem; max-width: min(19rem, calc(100vw - 4.5rem)); border-radius: 0.95rem; background: var(--surface-raised); color: var(--text); border: 1px solid var(--border); padding: 0.45rem; box-shadow: var(--dialog-shadow); }
#rail-more-menu { left: calc(var(--rail-w) + 8px); top: 14.5rem; }
#rail-status-popover { left: calc(var(--rail-w) + 8px); bottom: 1rem; padding: 0.85rem 0.95rem; min-width: 16.5rem; }
#topbar-more-menu { right: 1rem; top: calc(var(--topbar-h) + 6px); }
.shell-pop-item { width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 0.6rem; padding: 0.5rem 0.65rem; border-radius: 0.6rem; border: 0; background: transparent; color: var(--text); font-size: calc(0.86rem * var(--ui-scale, 1)); text-align: left; cursor: pointer; transition: background-color 0.12s ease, color 0.12s ease; }
.shell-pop-item:hover { background: var(--hover-tint); color: var(--accent); }
.shell-pop-row { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; font-size: calc(0.84rem * var(--ui-scale, 1)); padding: 0.28rem 0; color: var(--text-muted); }
.shell-pop-row strong { color: var(--text); font-weight: 600; font-family: ui-monospace, monospace; font-size: calc(0.8rem * var(--ui-scale, 1)); }
#sidebar { left: var(--rail-w) !important; width: var(--drawer-w) !important; padding: 0.7rem 0.75rem !important; border-inline-end: 1px solid var(--border-subtle); box-shadow: none !important; transition: transform 0.18s ease, opacity 0.15s ease; }
body.drawer-collapsed #sidebar { transform: translateX(calc(-100% - var(--rail-w))) !important; pointer-events: none; }
#main-shell { padding-left: var(--shell-left) !important; transition: padding-left 0.18s ease !important; }
.drawer-panel { display: flex; flex-direction: column; gap: 0.25rem; flex: 1; min-height: 0; overflow-y: auto; }
.drawer-panel[hidden] { display: none !important; }
.drawer-heading { font-size: calc(0.72rem * var(--ui-scale, 1)); font-family: ui-monospace, monospace; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-subtle); padding: 0.45rem 0.6rem 0.2rem; }
.drawer-item { width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; padding: 0.5rem 0.62rem; border-radius: 0.6rem; border: 0; background: transparent; color: var(--text-muted); font-size: calc(0.88rem * var(--ui-scale, 1)); text-align: left; cursor: pointer; transition: background-color 0.13s ease, color 0.13s ease; }
.drawer-item:hover { background: var(--hover-tint); color: var(--text); }
.drawer-item.is-active, .drawer-item[aria-current="page"] { background: color-mix(in oklab, var(--accent) 13%, transparent); color: var(--accent); font-weight: 500; }
.drawer-item-lead { display: flex; align-items: center; gap: 0.55rem; min-width: 0; }
.drawer-item-lead span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.drawer-badge { font-size: calc(0.72rem * var(--ui-scale, 1)); font-family: ui-monospace, monospace; color: var(--text-subtle); flex-shrink: 0; }
.drawer-primary-btn { width: 100%; display: flex; align-items: center; justify-content: center; gap: 0.45rem; padding: 0.55rem 0.75rem; margin-bottom: 0.35rem; border-radius: 0.65rem; background: var(--surface-soft); border: 1px solid var(--border); color: var(--text); font-size: calc(0.88rem * var(--ui-scale, 1)); font-weight: 500; cursor: pointer; transition: border-color 0.14s ease, background-color 0.14s ease; }
.drawer-primary-btn:hover { border-color: var(--accent); background: var(--hover-tint); }
#app-topbar { position: sticky; top: 0; z-index: 35; height: var(--topbar-h); flex: none; display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; padding: 0 1rem 0 1.25rem; background: color-mix(in oklab, var(--background) 84%, transparent); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-bottom: 1px solid var(--border-subtle); }
.topbar-left { display: flex; align-items: center; gap: 0.6rem; min-width: 0; }
#topbar-title { font-size: calc(0.9rem * var(--ui-scale, 1)); font-weight: 500; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
#topbar-timer-pill { display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.18rem 0.58rem; border-radius: 999px; border: 1px solid color-mix(in oklab, var(--accent) 45%, transparent); background: color-mix(in oklab, var(--accent) 12%, transparent); color: var(--accent); font-family: ui-monospace, monospace; font-size: calc(0.76rem * var(--ui-scale, 1)); font-weight: 600; cursor: pointer; }
#topbar-timer-pill[hidden] { display: none !important; }
.topbar-right { display: flex; align-items: center; gap: 0.3rem; flex-shrink: 0; }
.topbar-icon-btn { height: 2rem; width: 2rem; border-radius: 0.55rem; border: 1px solid transparent; background: transparent; color: var(--text-muted); display: inline-flex; align-items: center; justify-content: center; cursor: pointer; transition: background-color 0.14s ease, color 0.14s ease, border-color 0.14s ease; }
.topbar-icon-btn:hover { background: var(--hover-tint); color: var(--text); }
.topbar-icon-btn.is-active, .topbar-icon-btn[aria-expanded="true"] { color: var(--accent); background: color-mix(in oklab, var(--accent) 12%, transparent); border-color: color-mix(in oklab, var(--accent) 36%, transparent); }
.topbar-icon-btn[hidden], #sidebar-open-btn.hidden { display: none !important; }
@media (min-width: 901px) { #sidebar-open-btn { display: none !important; } }
#main-content { min-height: calc(100vh - var(--topbar-h)); min-height: calc(100dvh - var(--topbar-h)); }
#main-content.is-split-vertical, #main-content.is-split-horizontal { height: calc(100vh - var(--topbar-h)) !important; height: calc(100dvh - var(--topbar-h)) !important; }
#workspace-shell.h-screen { height: calc(100vh - var(--topbar-h)) !important; height: calc(100dvh - var(--topbar-h)) !important; }
.wb-view { min-height: calc(100vh - var(--topbar-h)) !important; padding: 1.25rem clamp(1rem, 2.2vw, 2rem) 3.5rem !important; gap: 1rem !important; }
.wb-header { padding-inline-end: 0 !important; }
.wb-side-tabbar { flex: none; display: flex; align-items: center; justify-content: space-between; gap: 0.35rem; padding: 0.38rem 0.55rem; border-bottom: 1px solid var(--border-subtle); background: var(--surface-raised); min-height: 2.55rem; }
.wb-side-tablist { display: flex; align-items: center; gap: 0.25rem; overflow-x: auto; flex: 1; min-width: 0; scrollbar-width: none; }
.wb-side-tab { position: relative; flex: none; display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.32rem 0.62rem; border-radius: 0.52rem; border: 1px solid transparent; background: transparent; color: var(--text-muted); font-size: calc(0.81rem * var(--ui-scale, 1)); font-weight: 500; cursor: pointer; max-width: 11.5rem; white-space: nowrap; }
.wb-side-tab span:first-child { overflow: hidden; text-overflow: ellipsis; }
.wb-side-tab:hover { background: var(--hover-tint); color: var(--text); }
.wb-side-tab[aria-selected="true"] { background: var(--surface-soft); color: var(--text); border-color: var(--border); }
.wb-side-tab[aria-selected="true"]::after { content: ""; position: absolute; inset: auto 0.35rem 0; border-block-end: 2px solid var(--accent); }
.wb-tab-x { width: 1.15rem; height: 1.15rem; border-radius: 999px; display: inline-flex; align-items: center; justify-content: center; font-size: 0.7rem; color: var(--text-subtle); }
.wb-tab-x:hover { background: var(--hover-tint); color: var(--text); }
.wb-launcher-wrap { flex: 1; overflow-y: auto; padding: 2rem 1.35rem; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1.25rem; }
.wb-launcher-search { width: 100%; max-width: 27rem; }
.wb-launcher-grid { width: 100%; max-width: 27rem; display: grid; grid-template-columns: repeat(auto-fill, minmax(7.6rem, 1fr)); gap: 0.65rem; }
.wb-launcher-tile { display: flex; flex-direction: column; align-items: flex-start; gap: 0.55rem; padding: 0.85rem; border-radius: 0.85rem; border: 1px solid var(--border-subtle); background: var(--surface-raised); color: var(--text); text-align: left; cursor: pointer; transition: border-color 0.14s ease, background-color 0.14s ease; }
.wb-launcher-tile:hover { border-color: var(--accent); background: var(--hover-tint); }
.wb-launcher-tile svg { width: 1.15rem; height: 1.15rem; color: var(--accent); }
.wb-launcher-tile span { font-size: calc(0.84rem * var(--ui-scale, 1)); font-weight: 500; }
.wb-side-subpane { flex: 1; min-height: 0; overflow-y: auto; padding: 0.95rem 1.05rem; display: flex; flex-direction: column; gap: 0.75rem; }
.wb-side-subpane[hidden], #split-launcher-body[hidden] { display: none !important; }
@media (max-width: 900px) {
  #activity-rail { display: none !important; }
  #sidebar { left: 0 !important; width: 268px !important; }
  body.drawer-collapsed #sidebar { transform: none; pointer-events: auto; }
  #main-shell { padding-left: 0 !important; }
  #sidebar-open-btn { position: static !important; margin-inline-end: 0.25rem; }
}
@media (forced-colors: active) { .rail-btn[aria-current="page"]::before { background: Highlight; } .wb-side-tab[aria-selected="true"]::after { border-color: Highlight; } }
</style>"""