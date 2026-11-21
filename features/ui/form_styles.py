"""Comfortable modal typography, native switch + fallback toggles, and branded selects."""

FORM_STYLES_CSS: str = r"""<style id="realm-form-polish">
#settings-modal[open] { inline-size: min(49rem, calc(100vw - 2rem)); max-inline-size: 49rem; block-size: min(49rem, 88vh); block-size: min(49rem, 88dvh); padding: 1.75rem; }
#onboarding-modal[open] { inline-size: min(46rem, calc(100vw - 2rem)); max-inline-size: 46rem; padding: 1.75rem; }
#upload-modal[open] { inline-size: min(44rem, calc(100vw - 2rem)); max-inline-size: 44rem; padding: 1.75rem; }
#format-studio-modal[open] { display: flex; inline-size: min(50rem, calc(100vw - 2rem)); max-inline-size: 50rem; block-size: min(46rem, 88vh); block-size: min(46rem, 88dvh); padding: 1.75rem; }
dialog textarea { font-size: 0.9375rem !important; border-radius: 0.75rem !important; background: color-mix(in oklab, var(--background) 82%, var(--surface-raised)) !important; }
dialog h2 { font-size: 1.25rem !important; font-weight: 600; letter-spacing: -0.015em; }
.settings-tabs { gap: 1.5rem; margin-block-end: 0.25rem; }
.settings-tabs button { font-size: 0.9375rem !important; font-weight: 500; padding: 0.85rem 0.2rem !important; }
dialog { font-size: 0.9375rem; line-height: 1.5; }
dialog .text-xs { font-size: 0.875rem !important; line-height: 1.48 !important; }
dialog .text-\[11px\] { font-size: 0.8125rem !important; line-height: 1.45 !important; }
dialog .text-sm { font-size: 0.9375rem !important; line-height: 1.5 !important; }
dialog .text-base { font-size: 1.0625rem !important; }
dialog input[type="text"], dialog input[type="password"], dialog input[type="url"], dialog input[type="number"] {
  min-block-size: 2.65rem; padding: 0.55rem 0.875rem !important; font-size: 0.9375rem !important; border-radius: 0.75rem !important;
  background: color-mix(in oklab, var(--background) 82%, var(--surface-raised)) !important;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
}
dialog input:focus-visible, dialog select:focus-visible {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px color-mix(in oklab, var(--accent) 24%, transparent) !important;
  outline: none;
}
dialog select {
  min-block-size: 2.65rem; padding: 0.55rem 2.5rem 0.55rem 0.9rem !important;
  font-size: 0.9375rem !important; font-weight: 500; border-radius: 0.75rem !important;
  background-color: color-mix(in oklab, var(--background) 82%, var(--surface-raised)) !important;
  border: 1px solid var(--border) !important; color: var(--text) !important;
  box-shadow: inset 0 1px 0 color-mix(in oklab, white 6%, transparent);
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
}
dialog select:hover:not(:disabled) {
  border-color: color-mix(in oklab, var(--accent) 60%, var(--border)) !important;
  background-color: color-mix(in oklab, var(--surface-raised) 76%, var(--background)) !important;
}
dialog select:disabled { opacity: 0.52; cursor: not-allowed; }
@supports (appearance: base-select) {
  dialog select, dialog select::picker(select) { appearance: base-select; }
  dialog select { background-image: none; padding-inline-end: 0.9rem !important; align-items: center; }
  dialog select::picker-icon { color: var(--accent); margin-inline-start: auto; transition: transform 0.2s ease; }
  dialog select:open::picker-icon { transform: rotate(180deg); }
  dialog select::picker(select) {
    background: var(--surface-raised); color: var(--text); border: 1px solid var(--border);
    border-radius: 0.875rem; padding: 0.35rem; margin-block-start: 0.35rem; box-shadow: var(--dialog-shadow);
  }
  dialog select option {
    padding: 0.5rem 0.75rem; border-radius: 0.55rem; font-size: 0.9375rem; color: var(--text); cursor: pointer;
  }
  dialog select option:hover { background: color-mix(in oklab, var(--accent) 16%, transparent); }
  dialog select option::checkmark { color: var(--accent); }
}
input[type="checkbox"][switch] {
  accent-color: var(--accent); margin: 0; cursor: pointer; flex-shrink: 0;
}
input[type="checkbox"][switch]:focus-visible { outline: 2.5px solid var(--accent); outline-offset: 3px; border-radius: 999px; }
html.has-native-switch input[type="checkbox"][switch] { transform: scale(1.18); transform-origin: right center; }
html.no-native-switch input[type="checkbox"][switch] {
  -webkit-appearance: none; appearance: none; position: relative;
  inline-size: 2.75rem; block-size: 1.55rem; border-radius: 9999px;
  background: color-mix(in oklab, var(--text-subtle) 38%, var(--background));
  border: 1px solid var(--border); transition: background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}
html.no-native-switch input[type="checkbox"][switch]::before {
  content: ""; position: absolute; inset-block-start: 2px; inset-inline-start: 2px;
  inline-size: 1.18rem; block-size: 1.18rem; border-radius: 9999px; background: #FFFFFF;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.35); transition: transform 0.2s cubic-bezier(0.22, 1, 0.36, 1);
}
html.no-native-switch input[type="checkbox"][switch]:checked {
  background: var(--accent); border-color: var(--accent);
  box-shadow: 0 0 14px color-mix(in oklab, var(--accent) 42%, transparent);
}
html.no-native-switch input[type="checkbox"][switch]:checked::before { transform: translateX(1.18rem); }
html.no-native-switch input[type="checkbox"][switch]:disabled { opacity: 0.45; cursor: not-allowed; }
#web-search-chat-btn[hidden], #upload-progress-panel[hidden], #graph-focus-banner[hidden], #graph-controls-panel[hidden], #custom-format-form[hidden], #format-browse-pane[hidden], #inspector-toggle-btn[hidden], #inspector-sidebar[hidden] { display: none !important; }
#web-search-chat-btn[aria-pressed="true"] {
  background: color-mix(in oklab, var(--accent) 20%, transparent) !important;
  color: var(--accent) !important;
  box-shadow: inset 0 0 0 1px color-mix(in oklab, var(--accent) 55%, transparent), 0 0 14px color-mix(in oklab, var(--accent) 26%, transparent);
}
.graph-hud {
  background: color-mix(in oklab, var(--surface-raised) 76%, transparent) !important;
  backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
  border: 1px solid var(--border) !important; box-shadow: var(--dialog-shadow);
}
@media (forced-colors: active) {
  html.no-native-switch input[type="checkbox"][switch] { border: 1px solid ButtonBorder; background: Canvas; }
  html.no-native-switch input[type="checkbox"][switch]:checked { background: Highlight; }
  html.no-native-switch input[type="checkbox"][switch]::before { background: CanvasText; }
}
</style>"""
