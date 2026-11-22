"""Semantic Light/Dark utility class bridges, PII category colors, and Forced Colors overrides."""

THEME_OVERRIDES_CSS: str = r"""
.bg-\[\#04060F\] { background-color: var(--background) !important; }
.bg-\[\#0B1020\], .bg-\[\#0B1020\]\/95 { background-color: var(--surface-raised) !important; }
.bg-\[\#4BB8E8\] { background-color: var(--accent) !important; color: var(--text-on-accent) !important; }
.bg-\[\#DC2626\] { background-color: #DC2626 !important; color: #FFFFFF !important; }
.bg-\[\#DC2626\]:hover { background-color: #B91C1C !important; }
.bg-\[\#4BB8E8\]\/20 { background-color: color-mix(in oklab, var(--accent) 22%, transparent) !important; }
.bg-\[\#4BB8E8\]\/15 { background-color: color-mix(in oklab, var(--accent) 16%, transparent) !important; }
.bg-\[\#4BB8E8\]\/12 { background-color: color-mix(in oklab, var(--accent) 13%, transparent) !important; }
.bg-\[\#4BB8E8\]\/10 { background-color: color-mix(in oklab, var(--accent) 11%, transparent) !important; }
.bg-\[\#38D399\] { background-color: var(--status-ok) !important; }
.bg-\[\#38D399\]\/15 { background-color: color-mix(in oklab, var(--status-ok) 15%, transparent) !important; }
.bg-\[\#EF4444\] { background-color: var(--status-danger) !important; }
.bg-amber-400\/10, .bg-amber-400\/15 { background-color: color-mix(in oklab, var(--status-warn) 14%, transparent) !important; }
.bg-white\/10 { background-color: color-mix(in oklab, var(--accent) 16%, transparent) !important; color: var(--text) !important; }
.bg-white\/5, .bg-white\/\[0\.04\], .bg-white\/\[0\.05\], .bg-white\/\[0\.06\] { background-color: var(--surface-pill) !important; }
.bg-\[rgba\(238\,242\,248\,0\.22\)\] { background-color: var(--border) !important; }
.bg-\[rgba\(238\,242\,248\,0\.08\)\] { background-color: var(--border-subtle) !important; }
.text-\[\#EEF2F8\] { color: var(--text) !important; }
.text-\[\#EEF2F8\]\/90 { color: color-mix(in oklab, var(--text) 92%, transparent) !important; }
.text-\[\#C8D4E6\] { color: var(--prose) !important; }
.text-\[\#A0B0C8\] { color: var(--text-muted) !important; }
.text-\[\#738196\] { color: var(--text-subtle) !important; }
.text-\[\#4BB8E8\], .text-\[\#4BB8E8\]\/80 { color: var(--accent) !important; }
.text-\[\#04060F\] { color: var(--text-on-accent) !important; }
.text-\[\#38D399\] { color: var(--status-ok) !important; }
.text-amber-300 { color: var(--status-warn) !important; }
.text-\[\#FCA5A5\], .text-red-300, .text-\[\#EF4444\] { color: var(--status-danger) !important; }
.placeholder\:text-\[\#738196\]::placeholder { color: var(--text-subtle) !important; }
.border-\[rgba\(238\,242\,248\,0\.16\)\], .border-\[rgba\(238\,242\,248\,0\.14\)\], .border-\[rgba\(238\,242\,248\,0\.12\)\], .border-white\/15 { border-color: var(--border) !important; }
.border-\[rgba\(238\,242\,248\,0\.08\)\], .border-\[rgba\(238\,242\,248\,0\.10\)\], .border-\[rgba\(238\,242\,248\,0\.06\)\], .border-white\/10, .border-white\/\[0\.06\] { border-color: var(--border-subtle) !important; }
.border-\[\#4BB8E8\] { border-color: var(--accent) !important; }
.border-\[\#4BB8E8\]\/50, .border-\[\#4BB8E8\]\/45, .border-\[\#4BB8E8\]\/40, .border-\[\#4BB8E8\]\/35, .border-\[\#4BB8E8\]\/30, .border-\[\#4BB8E8\]\/25 { border-color: color-mix(in oklab, var(--accent) 45%, transparent) !important; }
.border-\[\#38D399\]\/40 { border-color: color-mix(in oklab, var(--status-ok) 45%, transparent) !important; }
.border-amber-400\/25, .border-amber-400\/35 { border-color: color-mix(in oklab, var(--status-warn) 42%, transparent) !important; }
.border-\[\#EF4444\]\/40 { border-color: color-mix(in oklab, var(--status-danger) 45%, transparent) !important; }
.shadow-\[inset_0_0_0_1px_rgba\(238\,242\,248\,0\.08\)\] { box-shadow: inset 0 0 0 1px var(--border-subtle) !important; }
.shadow-\[inset_0_0_0_1px_rgba\(238\,242\,248\,0\.16\)\], .hover\:shadow-\[inset_0_0_0_1px_rgba\(238\,242\,248\,0\.16\)\]:hover { box-shadow: inset 0 0 0 1px var(--border) !important; }
.hover\:bg-white\/10:hover, .hover\:bg-white\/5:hover, .hover\:bg-white\/\[0\.04\]:hover, .hover\:bg-white\/\[0\.06\]:hover, .hover\:bg-\[\#EEF2F8\]\/\[0\.05\]:hover, .hover\:bg-\[\#EEF2F8\]\/10:hover { background-color: var(--hover-tint) !important; }
.hover\:bg-\[\#4BB8E8\]\/10:hover, .hover\:bg-\[\#4BB8E8\]\/15:hover, .hover\:bg-\[\#4BB8E8\]\/20:hover, .hover\:bg-\[\#4BB8E8\]\/25:hover { background-color: color-mix(in oklab, var(--accent) 22%, transparent) !important; }
.hover\:text-\[\#EEF2F8\]:hover, .hover\:text-white:hover { color: var(--text) !important; }
.hover\:text-\[\#4BB8E8\]:hover, .group:hover .group-hover\:text-\[\#4BB8E8\] { color: var(--accent) !important; }
.hover\:text-\[\#EF4444\]:hover, .hover\:text-red-300:hover { color: var(--status-danger) !important; }
.hover\:border-\[\#EF4444\]:hover { border-color: var(--status-danger) !important; }
.hover\:border-\[\#4BB8E8\]:hover, .hover\:border-\[\#4BB8E8\]\/50:hover, .focus\:border-\[\#4BB8E8\]:focus { border-color: var(--accent) !important; }
.folder-tree-row:hover, .folder-row-action:hover:not(:disabled) { background: var(--hover-tint) !important; }
.folder-tree-row.is-selected { background: color-mix(in oklab, var(--accent) 14%, transparent) !important; }
.folder-row-action[data-delete-folder]:hover:not(:disabled) { color: var(--status-danger) !important; }
.realm-skeleton { background: linear-gradient(90deg, var(--surface-raised), var(--surface-soft), var(--surface-raised)); }
.pii-cat-email { color: light-dark(#0369A1, #4BB8E8); border-color: color-mix(in oklab, currentColor 42%, transparent); }
.pii-cat-iban, .pii-cat-dob { color: var(--status-warn); border-color: color-mix(in oklab, currentColor 42%, transparent); }
.pii-cat-phone, .pii-cat-address { color: light-dark(#7E22CE, #C084FC); border-color: color-mix(in oklab, currentColor 42%, transparent); }
.pii-cat-name, .pii-cat-health_id { color: light-dark(#BE185D, #F472B6); border-color: color-mix(in oklab, currentColor 42%, transparent); }
.pii-cat-ip { color: var(--status-ok); border-color: color-mix(in oklab, currentColor 42%, transparent); }
select option { background-color: var(--surface-raised) !important; color: var(--text) !important; }
.md-code-inline, .md-pre-wrap, .md-table-wrap { background: var(--background) !important; border-color: var(--border) !important; }
.md-pre-lang { color: var(--text-subtle) !important; border-bottom-color: var(--border-subtle) !important; }
.md-hr { border-top-color: var(--border-subtle) !important; }
.md-code-inline, .md-list-marker, .md-link { color: var(--accent) !important; }
.md-link:hover { color: color-mix(in oklab, var(--accent) 82%, var(--text)) !important; }
.md-pre, .md-table td, .md-quote { color: var(--prose) !important; }
.md-table th { color: var(--text) !important; background: var(--hover-tint) !important; border-color: var(--border) !important; }
.md-table td { border-color: var(--border-subtle) !important; }
.md-math { background: color-mix(in oklab, var(--accent) 10%, transparent) !important; border-color: color-mix(in oklab, var(--accent) 28%, transparent) !important; color: var(--text) !important; }
.md-quote { border-inline-start-color: var(--accent) !important; background: color-mix(in oklab, var(--accent) 8%, transparent) !important; }
.rag-slider { --slider-fill-color: var(--accent) !important; --slider-track-color: var(--border-control) !important; }
.theme-swatch { forced-color-adjust: none; }
@media (prefers-contrast: more) {
  #prompt-container, #seed-chips .seed-chip, #more-ideas-btn, #home-browse-btn { background: var(--surface-raised) !important; border-color: var(--border-control) !important; color: var(--text) !important; }
}
@media (forced-colors: active) {
  :root { --background: Canvas; --surface-raised: Canvas; --text: CanvasText; --text-muted: CanvasText; --text-subtle: GrayText; --prose: CanvasText; --accent: Highlight; --text-on-accent: HighlightText; --status-ok: CanvasText; --status-warn: CanvasText; --status-danger: CanvasText; --border: ButtonBorder; --border-subtle: ButtonBorder; --border-control: ButtonBorder; }
  .ambient-stage { display: none !important; }
  #prompt-container { border: 1px solid ButtonBorder !important; box-shadow: none !important; }
  #prompt-container:focus-within { outline: 2px solid Highlight !important; }
  #seed-chips .seed-chip, #more-ideas-btn, #home-browse-btn { background: Canvas !important; border: 1px solid ButtonBorder !important; color: ButtonText !important; }
  .turn-author-heading { color: Highlight !important; }
}
"""
