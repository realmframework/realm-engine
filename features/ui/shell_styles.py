"""Two-Tier Spatial Shell CSS: 52px Activity Rail, Context Drawer, Mobile Switcher & Global Controls."""

SHELL_STYLES_CSS: str = r"""<style id="realm-spatial-shell-styles">
:root { --rail-w: 52px; --drawer-w: 248px; --topbar-h: 44px; --shell-left: calc(var(--rail-w) + var(--drawer-w)); }
body.drawer-collapsed { --shell-left: var(--rail-w); }
#activity-rail { position: fixed; inset-block: 0; inset-inline-start: 0; width: var(--rail-w); z-index: 60; background: var(--surface-raised); border-inline-end: 1px solid var(--border-subtle); display: flex; flex-direction: column; align-items: center; padding: 0.25rem 0 0.7rem; gap: 0.25rem; }
.rail-btn { position: relative; width: 38px; height: 38px; border-radius: 0.65rem; border: 0; background: transparent; color: var(--text-muted); display: inline-flex; align-items: center; justify-content: center; cursor: pointer; transition: background-color 0.14s ease, color 0.14s ease; }
.rail-btn:hover { background: var(--hover-tint); color: var(--text); }
.rail-btn[aria-current="page"], .rail-btn.is-active { background: color-mix(in oklab, var(--accent) 14%, transparent); color: var(--accent); }
.rail-btn[aria-current="page"]::before { content: ""; position: absolute; inset-inline-start: -7px; inset-block: 7px; width: 3px; border-radius: 0 3px 3px 0; background: var(--accent); }
.rail-badge-dot { position: absolute; top: 6px; right: 6px; width: 7px; height: 7px; border-radius: 999px; background: var(--accent); border: 1.5px solid var(--surface-raised); }
.rail-badge-dot[hidden] { display: none !important; }
.rail-divider { width: 22px; height: 1px; background: var(--border-subtle); margin: 0.15rem 0; }
.rail-spacer { flex: 1; }
.rail-popover { position: fixed; inset: auto; margin: 0; min-width: 14.5rem; max-width: min(19rem, calc(100vw - 2rem)); border-radius: 0.9rem; background: var(--surface-raised); color: var(--text); border: 1px solid var(--border); padding: 0.4rem; box-shadow: var(--dialog-shadow); }
#rail-status-popover { padding: 0.85rem 0.95rem; min-width: 16.5rem; }
.shell-pop-item { width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 0.6rem; padding: 0.48rem 0.65rem; border-radius: 0.55rem; border: 0; background: transparent; color: var(--text); font-size: calc(0.85rem * var(--ui-scale, 1)); text-align: left; cursor: pointer; transition: background-color 0.12s ease, color 0.12s ease; }
.shell-pop-item:hover { background: var(--hover-tint); color: var(--accent); }
.shell-pop-sep { margin-top: 0.28rem; border-top: 1px solid var(--border-subtle); padding-top: 0.5rem; }
.shell-pop-row { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; font-size: calc(0.83rem * var(--ui-scale, 1)); padding: 0.28rem 0; color: var(--text-muted); }
.shell-pop-row strong { color: var(--text); font-weight: 600; font-family: ui-monospace, monospace; font-size: calc(0.79rem * var(--ui-scale, 1)); }
.bp-menu-group { display: flex; flex-direction: column; gap: 0.12rem; }
.bp-check-item { justify-content: flex-start; gap: 0.5rem; }
.bp-check-item::before { content: ""; flex: none; inline-size: 1.05rem; text-align: center; font-weight: 700; color: var(--accent); }
.bp-check-item[aria-checked="true"]::before { content: "✓"; }
#sidebar { left: var(--rail-w) !important; width: var(--drawer-w) !important; padding: 0 !important; border-inline-end: 1px solid var(--border-subtle); box-shadow: none !important; transition: transform 0.18s ease, opacity 0.15s ease; }
#sidebar-header { height: var(--topbar-h); min-height: var(--topbar-h); flex-shrink: 0; display: flex; align-items: center; gap: 0.25rem; padding: 0 0.6rem; border-bottom: 1px solid var(--border-subtle); }
#sidebar-body { flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column; padding: 0.75rem 0.65rem 0.7rem; overflow: hidden; }
body.drawer-collapsed #sidebar { transform: translateX(calc(-100% - var(--rail-w))) !important; pointer-events: none; }
#main-shell { padding-left: var(--shell-left) !important; height: 100vh; height: 100dvh; overflow: hidden; transition: padding-left 0.18s ease !important; }
.drawer-panel { display: flex; flex-direction: column; gap: 0.25rem; flex: 1; min-height: 0; overflow-y: auto; overscroll-behavior: contain; }
.drawer-panel[hidden] { display: none !important; }
.drawer-heading { font-size: calc(0.72rem * var(--ui-scale, 1)); font-family: ui-monospace, monospace; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-subtle); padding: 0.25rem 0.6rem 0.35rem; }
.drawer-item { width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; padding: 0.5rem 0.62rem; border-radius: 0.6rem; border: 0; background: transparent; color: var(--text-muted); font-size: calc(0.88rem * var(--ui-scale, 1)); text-align: left; cursor: pointer; transition: background-color 0.13s ease, color 0.13s ease; }
.drawer-item:hover { background: var(--hover-tint); color: var(--text); }
.drawer-item.is-active, .drawer-item[aria-current="page"] { background: color-mix(in oklab, var(--accent) 13%, transparent); color: var(--accent); font-weight: 500; }
.drawer-item-lead { display: flex; align-items: center; gap: 0.55rem; min-width: 0; }
.drawer-item-lead span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.drawer-sublist { display: flex; flex-direction: column; gap: 0.15rem; padding-inline-start: 1rem; }
.drawer-subitem { padding-block: 0.35rem; font-size: calc(0.82rem * var(--ui-scale, 1)); }
.drawer-badge { font-size: calc(0.72rem * var(--ui-scale, 1)); font-family: ui-monospace, monospace; color: var(--text-subtle); flex-shrink: 0; }
.mobile-only-ctrl { display: none !important; }
.mobile-rail-strip, .mobile-drawer-footer { display: none; }
#wb-global-controls { position: absolute; top: 0; right: 0; height: var(--topbar-h); z-index: 40; display: flex; align-items: center; gap: 0.25rem; padding: 0 0.65rem 0 0; }
#topbar-timer-pill { display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.18rem 0.58rem; border-radius: 999px; border: 1px solid color-mix(in oklab, var(--accent) 45%, transparent); background: color-mix(in oklab, var(--accent) 12%, transparent); color: var(--accent); font-family: ui-monospace, monospace; font-size: calc(0.76rem * var(--ui-scale, 1)); font-weight: 600; cursor: pointer; }
#topbar-timer-pill[hidden] { display: none !important; }
.topbar-icon-btn { height: 2rem; width: 2rem; border-radius: 0.52rem; border: 1px solid transparent; background: transparent; color: var(--text-muted); display: inline-flex; align-items: center; justify-content: center; cursor: pointer; transition: background-color 0.14s ease, color 0.14s ease, border-color 0.14s ease; }
.topbar-icon-btn:hover { background: var(--hover-tint); color: var(--text); }
.topbar-icon-btn.is-active, .topbar-icon-btn[aria-expanded="true"], .topbar-icon-btn[aria-pressed="true"] { color: var(--accent); background: color-mix(in oklab, var(--accent) 12%, transparent); border-color: color-mix(in oklab, var(--accent) 36%, transparent); }
.topbar-pill-btn { height: 2rem; padding: 0 0.62rem; gap: 0.35rem; border-radius: 999px; border: 1px solid var(--border-subtle); background: color-mix(in oklab, var(--surface-raised) 70%, transparent); color: var(--text-muted); font-size: calc(0.78rem * var(--ui-scale, 1)); font-family: ui-monospace, monospace; font-weight: 500; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; transition: background-color 0.14s ease, color 0.14s ease, border-color 0.14s ease; }
.topbar-pill-btn:hover { background: var(--hover-tint); color: var(--text); border-color: var(--border); }
.topbar-pill-btn[aria-expanded="true"] { color: var(--accent); background: color-mix(in oklab, var(--accent) 13%, transparent); border-color: color-mix(in oklab, var(--accent) 42%, transparent); }
.topbar-icon-btn[hidden], .topbar-pill-btn[hidden], #sidebar-open-btn.hidden { display: none !important; }
@media (min-width: 901px) { #sidebar-open-btn { display: none !important; } }
.graph-viewport { height: 100% !important; min-height: calc(100dvh - var(--topbar-h) - 0.5rem); }
.wb-view { min-height: 100% !important; padding: 1.15rem clamp(0.95rem, 2vw, 1.85rem) 2.75rem !important; gap: 0.95rem !important; }
.wb-header { padding-inline-end: 0 !important; }
@media (max-width: 900px) {
  #activity-rail { display: none !important; }
  #sidebar { left: 0 !important; width: 274px !important; }
  body.drawer-collapsed #sidebar { transform: translateX(-100%) !important; }
  #sidebar.-translate-x-full { transform: translateX(-100%) !important; pointer-events: none; }
  #sidebar:not(.-translate-x-full) { transform: translateX(0) !important; pointer-events: auto; }
  #main-shell { padding-left: 0 !important; }
  #sidebar-open-btn { position: static !important; margin-inline-end: 0.2rem; }
  .mobile-only-ctrl { display: inline-flex !important; }
  .mobile-rail-strip { display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.2rem; padding: 0.25rem; margin-bottom: 0.55rem; border-radius: 0.7rem; background: var(--background); border: 1px solid var(--border-subtle); }
  .mobile-rail-strip .rail-btn { width: 100%; height: 34px; }
  .mobile-rail-strip .rail-btn[aria-current="page"]::before { display: none; }
  .mobile-drawer-footer { display: flex; flex-direction: column; gap: 0.15rem; padding-top: 0.45rem; margin-top: 0.45rem; border-top: 1px solid var(--border-subtle); }
}
@media (forced-colors: active) { .rail-btn[aria-current="page"]::before { background: Highlight; } }
</style>"""
