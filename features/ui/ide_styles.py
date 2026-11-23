"""IDE workbench styling: Code Editor gutter, File Tree filter, pinned tabs, Highlight-to-Copilot & #file chips."""

IDE_STYLES_CSS: str = r"""<style id="realm-ide-styles">
.cf-lang-badge { display: inline-flex; align-items: center; padding: 0.14rem 0.52rem; border-radius: 999px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: calc(0.68rem * var(--ui-scale, 1)); font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; background: color-mix(in oklab, var(--accent) 14%, transparent); color: var(--accent); border: 1px solid color-mix(in oklab, var(--accent) 28%, transparent); flex-shrink: 0; }
.cf-code-wrap { flex: 1 1 auto; min-height: 0; height: 100%; display: flex; overflow: hidden; background: var(--background); }
.cf-code-gutter { flex: none; min-width: 3.15rem; padding: 1.15rem 0.72rem 1.15rem 0.6rem; margin: 0; border-inline-end: 1px solid var(--border-subtle); background: color-mix(in oklab, var(--surface-raised) 52%, transparent); color: var(--text-subtle); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: calc(0.86rem * var(--ui-scale, 1)); line-height: 1.65; text-align: right; user-select: none; -webkit-user-select: none; overflow: hidden; white-space: pre; }
.cf-code-wrap .cf-editor { padding: 1.15rem 1.25rem; font-size: calc(0.86rem * var(--ui-scale, 1)); line-height: 1.65; white-space: pre; overflow: auto; }
.ft-filter-wrap { position: relative; display: flex; align-items: center; padding: 0.2rem 0.35rem 0.45rem; flex-shrink: 0; }
.ft-filter-ico { position: absolute; left: 0.85rem; width: 0.85rem; height: 0.85rem; color: var(--text-subtle); pointer-events: none; }
.ft-filter-input { width: 100%; height: 1.9rem; padding: 0 1.7rem 0 1.95rem; border-radius: 0.55rem; border: 1px solid var(--border-subtle); background: color-mix(in oklab, var(--surface-soft) 72%, transparent); color: var(--text); font-size: calc(0.79rem * var(--ui-scale, 1)); outline: none; transition: border-color 0.14s ease, background-color 0.14s ease; }
.ft-filter-input::placeholder { color: var(--text-subtle); }
.ft-filter-input:focus { border-color: color-mix(in oklab, var(--accent) 55%, transparent); background: var(--surface-raised); }
.ft-filter-clear { position: absolute; right: 0.6rem; width: 1.25rem; height: 1.25rem; border: 0; border-radius: 999px; background: transparent; color: var(--text-subtle); font-size: 0.72rem; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; }
.ft-filter-clear:hover { background: var(--hover-tint); color: var(--text); }
.ft-filter-clear[hidden] { display: none !important; }
.wb-zone-tab.is-pinned { padding-inline-end: 0.6rem; }
.wb-tab-pin { width: 0.8rem; height: 0.8rem; color: var(--accent); flex-shrink: 0; opacity: 0.9; }
.wb-zone-tab.is-pinned .wb-tab-x { display: none !important; }
.cf-sel-pill { position: fixed; z-index: 65; display: inline-flex; align-items: center; gap: 0.2rem; padding: 0.22rem; border-radius: 999px; background: color-mix(in oklab, var(--surface-raised) 92%, transparent); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); border: 1px solid color-mix(in oklab, var(--accent) 36%, var(--border)); box-shadow: var(--dialog-shadow); }
.cf-sel-pill[hidden] { display: none !important; }
.cf-sel-btn { display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.28rem 0.65rem; border: 0; border-radius: 999px; background: transparent; color: var(--text); font-size: calc(0.77rem * var(--ui-scale, 1)); font-weight: 500; cursor: pointer; white-space: nowrap; transition: background-color 0.12s ease, color 0.12s ease; }
.cf-sel-btn:hover { background: color-mix(in oklab, var(--accent) 16%, transparent); color: var(--accent); }
.cf-sel-btn-primary { background: color-mix(in oklab, var(--accent) 16%, transparent); color: var(--accent); }
.cf-sel-btn-primary:hover { background: var(--accent); color: var(--text-on-accent); }
.cp-compose-wrap { position: relative; }
.cp-chips { display: flex; flex-wrap: wrap; gap: 0.3rem; padding: 0 0.75rem 0.38rem; }
.cp-chips:empty { display: none; padding: 0; }
.cp-chip { display: inline-flex; align-items: center; gap: 0.3rem; max-width: 100%; padding: 0.16rem 0.42rem 0.16rem 0.55rem; border-radius: 999px; background: color-mix(in oklab, var(--accent) 13%, var(--surface-soft)); border: 1px solid color-mix(in oklab, var(--accent) 30%, var(--border-subtle)); color: var(--text); font-size: calc(0.73rem * var(--ui-scale, 1)); line-height: 1.3; }
.cp-chip-sel { background: color-mix(in oklab, var(--accent) 20%, var(--surface-soft)); border-color: color-mix(in oklab, var(--accent) 44%, transparent); color: var(--accent); }
.cp-chip-lbl { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 13.5rem; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.cp-chip-x { width: 1.05rem; height: 1.05rem; border: 0; border-radius: 999px; background: transparent; color: var(--text-muted); font-size: 0.68rem; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0; }
.cp-chip-x:hover { background: var(--hover-tint); color: var(--text); }
.cp-file-menu { position: absolute; left: 0.75rem; right: 0.75rem; bottom: calc(100% + 0.35rem); z-index: 60; max-height: 13.5rem; overflow-y: auto; padding: 0.3rem; border-radius: 0.85rem; background: color-mix(in oklab, var(--surface-raised) 96%, transparent); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid var(--border); box-shadow: var(--dialog-shadow); display: flex; flex-direction: column; gap: 0.12rem; }
.cp-file-menu[hidden] { display: none !important; }
.cp-file-opt { width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; padding: 0.4rem 0.6rem; border: 0; border-radius: 0.55rem; background: transparent; color: var(--text-muted); font-size: calc(0.79rem * var(--ui-scale, 1)); text-align: left; cursor: pointer; }
.cp-file-opt:hover, .cp-file-opt.is-active { background: color-mix(in oklab, var(--accent) 16%, transparent); color: var(--text); }
.cp-file-opt-name { font-weight: 500; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cp-file-opt-sub { font-family: ui-monospace, monospace; font-size: calc(0.7rem * var(--ui-scale, 1)); color: var(--text-subtle); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 9rem; }
.ft-pop-sep { height: 1px; margin: 0.25rem 0.4rem; background: var(--border-subtle); }
@keyframes wb-spin { to { transform: rotate(360deg); } }
.wb-tab-spin { width: 0.85rem; height: 0.85rem; color: var(--accent); flex-shrink: 0; animation: wb-spin 0.85s linear infinite; }
.wb-tab-unread { width: 0.46rem; height: 0.46rem; border-radius: 999px; background: var(--accent); box-shadow: 0 0 0 2.5px color-mix(in oklab, var(--accent) 24%, transparent); flex-shrink: 0; }
.wb-tab-dirty-dot { width: 0.48rem; height: 0.48rem; border-radius: 999px; background: var(--accent); flex-shrink: 0; margin-inline: 0.28rem; }
.wb-zone-tab.is-dirty:not(.is-pinned):not(:hover) .wb-tab-x { display: none; }
.wb-zone-tab.is-dirty:not(.is-pinned):hover .wb-tab-dirty-dot { display: none; }
.ft-dirty-dot { width: 0.44rem; height: 0.44rem; border-radius: 999px; background: var(--accent); flex-shrink: 0; }
.cf-statusbar { flex: none; display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; padding: 0.26rem 1rem; border-top: 1px solid var(--border-subtle); background: color-mix(in oklab, var(--surface-raised) 72%, transparent); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: calc(0.71rem * var(--ui-scale, 1)); color: var(--text-subtle); }
.cf-statusbar-grp { display: inline-flex; align-items: center; gap: 0.8rem; min-width: 0; }
@media (prefers-reduced-motion: reduce) { .wb-tab-spin { animation: none; opacity: 0.85; } }
</style>"""
