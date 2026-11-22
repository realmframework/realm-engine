"""Comfortable modal typography, native switch + fallback toggles, and branded selects."""

FORM_STYLES_CSS: str = r"""<style id="realm-form-polish">
#settings-modal[open] { inline-size: min(52rem, calc(100vw - 2rem)); max-inline-size: 52rem; block-size: min(50rem, 88vh); block-size: min(50rem, 88dvh); max-block-size: 88dvh; padding: 1.5rem 1.75rem; }
#onboarding-modal[open] { inline-size: min(48rem, calc(100vw - 2rem)); max-inline-size: 48rem; padding: 1.75rem; }
#upload-modal[open] { inline-size: min(46rem, calc(100vw - 2rem)); max-inline-size: 46rem; padding: 1.75rem; }
#format-studio-modal[open], #agent-studio-modal[open] { display: flex; inline-size: min(52rem, calc(100vw - 2rem)); max-inline-size: 52rem; block-size: min(48rem, 88vh); block-size: min(48rem, 88dvh); padding: 1.75rem; }
dialog textarea { font-size: calc(0.95rem * var(--ui-scale, 1)); border-radius: 0.75rem; border-color: var(--border-control); background: color-mix(in oklab, var(--background) 82%, var(--surface-raised)) !important; }
dialog h2 { font-size: calc(1.25rem * var(--ui-scale, 1)); font-weight: 600; letter-spacing: -0.015em; }
.settings-tabs { gap: 1.5rem; margin-block-end: 0.25rem; }
.settings-tabs button { font-size: calc(0.95rem * var(--ui-scale, 1)); font-weight: 500; padding: 0.85rem 0.2rem !important; }
dialog { font-size: calc(0.95rem * var(--ui-scale, 1)); line-height: 1.55; max-inline-size: calc(100vw - 2rem); }
dialog .text-xs { font-size: calc(0.875rem * var(--ui-scale, 1)); line-height: 1.5; }
dialog .text-sm { font-size: calc(0.9375rem * var(--ui-scale, 1)); line-height: 1.55; }
dialog input[type="text"], dialog input[type="password"], dialog input[type="url"], dialog input[type="number"] {
  min-block-size: 2.75rem; padding: 0.55rem 0.9rem !important; font-size: calc(0.95rem * var(--ui-scale, 1)); border-radius: 0.75rem !important;
  border-color: var(--border-control) !important;
  background: color-mix(in oklab, var(--background) 82%, var(--surface-raised)) !important;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
}
dialog input.key-secret-input { padding-inline-end: 2.75rem !important; }
.key-eye-btn {
  position: absolute; inset-inline-end: 0.35rem; top: 50%; transform: translateY(-50%);
  display: inline-flex; align-items: center; justify-content: center;
  min-inline-size: 2rem; min-block-size: 2rem; border-radius: 0.5rem;
  color: var(--text-muted); background: transparent; border: 0; cursor: pointer;
  transition: color 0.14s ease, background-color 0.14s ease;
}
.key-eye-btn:hover { color: var(--text); background: var(--hover-tint); }
#settings-api-key-group [hidden], #onboarding-api-key-group [hidden], .key-eye-btn[hidden] { display: none !important; }
dialog input:focus-visible, dialog select:focus-visible, dialog textarea:focus-visible {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px color-mix(in oklab, var(--accent) 24%, transparent) !important;
  outline: 2px solid transparent;
}
dialog select {
  min-block-size: 2.75rem; padding: 0.55rem 2.5rem 0.55rem 0.9rem !important;
  font-size: calc(0.95rem * var(--ui-scale, 1)); font-weight: 500; border-radius: 0.75rem !important;
  background-color: color-mix(in oklab, var(--background) 82%, var(--surface-raised)) !important;
  border: 1px solid var(--border-control) !important; color: var(--text) !important;
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
    padding: 0.5rem 0.75rem; border-radius: 0.55rem; font-size: calc(0.95rem * var(--ui-scale, 1)); color: var(--text); cursor: pointer;
  }
  dialog select option:hover { background: color-mix(in oklab, var(--accent) 16%, transparent); }
  dialog select option::checkmark { color: var(--accent); }
}
input[type="checkbox"][switch] {
  accent-color: var(--accent); margin: 0; cursor: pointer; flex-shrink: 0;
}
input[type="checkbox"][switch]:focus-visible { outline: 2.5px solid var(--accent); outline-offset: 3px; border-radius: 999px; }
html.has-native-switch input[type="checkbox"][switch] { transform: scale(1.12); transform-origin: center; margin-inline: 0.5rem 0.2rem; }
html.no-native-switch input[type="checkbox"][switch] {
  -webkit-appearance: none; appearance: none; position: relative;
  inline-size: 2.75rem; block-size: 1.55rem; border-radius: 9999px;
  background: light-dark(#64748B, #334155);
  border: 1px solid var(--border-control); transition: background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
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
#web-search-chat-btn[hidden], #upload-progress-panel[hidden], #graph-focus-banner[hidden], #graph-controls-panel[hidden], #custom-format-form[hidden], #format-browse-pane[hidden], #inspector-sidebar[hidden], #agent-roster-pane[hidden], #agent-editor-form[hidden], #agent-guided-pane[hidden], #agent-raw-pane[hidden], #restore-agents-btn[hidden] { display: none !important; }
details.export-menu > summary::-webkit-details-marker { display: none; }
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
[data-onboarding-dot] { position: relative; }
[data-onboarding-dot]::after { content: ""; position: absolute; inset: -0.5rem -0.35rem; }
</style>"""
