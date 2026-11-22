"""HTML template for the AI Engineering Knowledge Engine search UI (Google Stitch design)."""

from features.ui.command_template import (
    COMMAND_PALETTE_HTML,
    COMMAND_STYLES_CSS,
    SLASH_MENU_HTML,
)
from features.ui.editor_template import EDITOR_MODALS_HTML, EDITOR_STYLES_CSS
from features.ui.experience_template import AREA_TEMPLATE_SELECT
from features.ui.focus_template import FOCUS_MODALS_HTML, FOCUS_VIEW_HTML
from features.ui.form_styles import FORM_STYLES_CSS
from features.ui.guide_template import GUIDE_MODAL_HTML, GUIDE_STYLES_CSS
from features.ui.icons import ICON_GLOBE, ICON_MIC
from features.ui.impact_focus_styles import IMPACT_FOCUS_STYLES_CSS
from features.ui.impact_template import IMPACT_MODALS_HTML, IMPACT_VIEW_HTML
from features.ui.modals import MODALS_HTML
from features.ui.power_template import POWER_MODAL_HTML, POWER_STYLES_CSS
from features.ui.script import CLIENT_SCRIPT
from features.ui.shell_styles import SHELL_STYLES_CSS
from features.ui.sidebar_template import (
    ACTIVITY_RAIL_HTML,
    APP_TOPBAR_HTML,
    SIDEBAR_HTML,
)
from features.ui.split_styles import SPLIT_STYLES_CSS
from features.ui.split_template import (
    BOTTOM_PANEL_HTML,
    CENTER_SPLIT_PANE_HTML,
    CENTER_TABBAR_HTML,
    RIGHT_SIDEBAR_HTML,
)
from features.ui.study_template import STUDY_MODAL_HTML, STUDY_STYLES_CSS
from features.ui.theme_styles import THEME_BRIDGE_CSS
from features.ui.work_board_modals import WORK_BOARD_MODALS_HTML
from features.ui.work_board_styles import WORK_BOARD_STYLES_CSS
from features.ui.work_board_template import WORK_BOARD_HTML
from features.ui.workflow_studio_styles import WORKFLOW_STUDIO_STYLES_CSS
from features.ui.workflow_studio_template import (
    WORKFLOWS_MODALS_HTML,
    WORKFLOWS_VIEW_HTML,
)
from features.ui.workflow_template import WORKFLOW_MODALS_HTML, WORKFLOW_STYLES_CSS

HTML_PAGE: str = (
    """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="text-scale" content="scale" />
<meta name="color-scheme" content="light dark" />
<script>try{var r=document.documentElement;if(new URLSearchParams(location.search).get("embed")==="1"){r.classList.add("is-embed");}var m=localStorage.getItem("color-scheme");if(m==="dark"||m==="light"){document.querySelector('meta[name="color-scheme"]').content=m;}var a=localStorage.getItem("realm_theme_accent"),g=localStorage.getItem("realm_theme_glow");if(a&&/^#[0-9a-f]{6}$/i.test(a)){r.style.setProperty("--accent-seed",a);}if(g&&/^#[0-9a-f]{6}$/i.test(g)){r.style.setProperty("--accent-glow",g);}var rf=localStorage.getItem("realm_reading_font"),rs=localStorage.getItem("realm_reading_size"),rw=localStorage.getItem("realm_reading_width");if(rf==="legible")r.classList.add("realm-legible");if(rf==="dyslexic")r.classList.add("realm-dyslexic");var sc=rs==="sm"?"0.9375":rs==="lg"?"1.125":rs==="xl"?"1.25":"1";r.style.setProperty("--ui-scale",sc);r.style.setProperty("--reading-size","calc(1rem * "+sc+")");if(rw==="narrow")r.style.setProperty("--reading-width","40rem");else if(rw==="wide")r.style.setProperty("--reading-width","62rem");if(localStorage.getItem("realm_hc_focus")==="1")r.classList.add("realm-hc-focus");if(localStorage.getItem("realm_reduce_motion")==="1")r.classList.add("realm-reduce-motion");}catch(e){}</script>
<meta name="shell-type" content="web_dashboard" />
<title>REALM Engine</title>
<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="/static/favicon-32.png"><link rel="icon" type="image/png" sizes="16x16" href="/static/favicon-16.png"><link rel="apple-touch-icon" sizes="192x192" href="/static/logo-192.png">
<style>
:root {
  color-scheme: dark;
  --background: #04060F;
  --surface-raised: #0B1020;
  --text: #EEF2F8;
  --text-muted: #A0B0C8;
  --text-subtle: #738196;
  --accent: #4BB8E8;
  --text-on-accent: #04060F;
  --border: rgba(238, 242, 248, 0.16);
  --border-subtle: rgba(238, 242, 248, 0.08);
}
@layer base { html, body { margin: 0; padding: 0; background: var(--background); color: var(--text); accent-color: var(--accent); } body { overscroll-behavior: none; } }
::-webkit-scrollbar { display: none; }
#prompt-container { view-transition-name: search-pill; }
.prompt-entry { display: flex; flex: 1; flex-wrap: wrap; align-items: center; gap: .375rem; min-inline-size: 0; }
.prompt-entry input { flex: 1 1 12ch; inline-size: 0; min-inline-size: min(100%, 12ch); }
#scope-chip { flex: 0 1 auto; max-inline-size: 14rem; min-inline-size: 0; }
#scope-chip[hidden] { display: none !important; }
#scope-chip-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
#scope-reset-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
#model { max-inline-size: 10.5rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
dialog:modal { overscroll-behavior: contain; }
dialog::backdrop { overflow: hidden; overscroll-behavior: contain; background: rgba(4, 6, 15, 0.8); backdrop-filter: blur(4px); }
select { appearance: none; -webkit-appearance: none; padding-right: 2.25rem !important; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 0.75rem center; background-size: 0.75rem; }
.chat-dock { padding-bottom: max(1.5rem, env(safe-area-inset-bottom)); background: transparent; }
.library-folders { --folder-indent: 1.25rem; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-subtle); }
.folder-nav { overflow-x: auto; padding: 2px; }
.folder-tree { min-inline-size: 24rem; }
.folder-branches { margin: 0; padding: 0; border: 0; }
.folder-branches[hidden] { display: none; }
.folder-tree-row { display: flex; align-items: center; gap: .25rem; min-block-size: 2.5rem; min-inline-size: calc(22rem + var(--folder-depth, 0) * var(--folder-indent)); padding-inline: calc(var(--folder-depth, 0) * var(--folder-indent)) .25rem; border-radius: .5rem; }
.folder-tree-row:hover { background: rgba(238,242,248,.04); }
.folder-tree-row.is-selected { background: rgba(75,184,232,.12); }
.folder-filter { display: flex; flex: 1; align-items: center; gap: .5rem; min-inline-size: 0; min-block-size: 2.4rem; padding: .3rem .55rem; text-align: start; font-size: calc(.9375rem * var(--ui-scale, 1)); color: var(--text-muted); border-radius: .5rem; }
.folder-filter.folder-root { font-weight: 600; color: var(--text); }
.folder-filter[aria-pressed="true"] { color: var(--accent); font-weight: 500; }
.folder-file-count { margin-inline-start: auto; padding-inline-start: 1rem; flex-shrink: 0; color: var(--text-subtle); font-family: ui-monospace, monospace; font-size: calc(.8125rem * var(--ui-scale, 1)); }
.folder-branch-toggle[aria-expanded="true"] svg { transform: rotate(90deg); }
.folder-branch-toggle svg { display: block; }
.folder-row-action { display: inline-flex; align-items: center; justify-content: center; min-width: 1.75rem; height: 1.75rem; border-radius: .5rem; color: var(--text-muted); }
.folder-row-action:hover:not(:disabled) { background: rgba(238,242,248,.06); color: var(--text); }
.folder-row-action[data-delete-folder]:hover:not(:disabled) { color: #EF4444; }
.folder-tree-row button:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.folder-child-creator { padding-inline-start: calc(var(--folder-depth, 0) * var(--folder-indent)); max-inline-size: 36rem; }
.library-empty-state { padding: 2.5rem 1rem; text-align: center; }
@media (hover: hover) and (pointer: fine) {
  .folder-row-actions { opacity: 0; pointer-events: none; }
  .folder-tree-row:hover > .folder-row-actions, .folder-tree-row:focus-within > .folder-row-actions { opacity: 1; pointer-events: auto; }
}
[data-specialist-only] { display: none !important; }
#settings-modal [data-everyday-only] { display: none !important; }
#settings-modal [data-specialist-only] { display: revert !important; }
#settings-modal[open] { display: flex; flex-direction: column; block-size: min(44rem, 85vh); block-size: min(44rem, 85dvh); }
.settings-body { --scrollbar-thumb: #738196; --scrollbar-track: #0B1020; overflow-y: auto; flex: 1 1 auto; min-block-size: 0; padding-inline-end: 0.875rem; overscroll-behavior: contain; scrollbar-gutter: stable; scrollbar-width: thin; scrollbar-color: var(--scrollbar-thumb) var(--scrollbar-track); }
.settings-body::-webkit-scrollbar { display: block; width: 6px; }
.settings-body::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb); border-radius: 999px; }
.settings-body::-webkit-scrollbar-track { background: transparent; }
.settings-panel[hidden], [role="tabpanel"][hidden] { display: none !important; }
.settings-tabs { display: flex; flex: none; gap: 1.25rem; overflow-x: auto; border-block-end: 1px solid var(--border-subtle); scrollbar-width: thin; }
.settings-tabs button { position: relative; flex: none; white-space: nowrap; padding: .75rem .125rem; color: var(--text-muted); font-size: calc(.9375rem * var(--ui-scale, 1)); }
.settings-tabs button[aria-selected="true"] { color: var(--accent); }
.settings-tabs button[aria-selected="true"]::after { content: ""; position: absolute; inset: auto 0 0; border-block-end: 2px solid currentColor; }
.settings-tabs button:focus-visible, .workspace-menu button:focus-visible, #workspace-switcher-btn:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.workspace-menu nav { max-block-size: min(55vh, 24rem); overflow-y: auto; }
.workspace-menu { position: fixed; inset: auto; margin: 0; inline-size: min(22rem, calc(100vw - 2rem)); max-block-size: var(--workspace-menu-height, 70vh); overflow-y: auto; }
.library-topics { display: flex; gap: .5rem; overflow-x: auto; padding-block: .25rem .75rem; margin-block-end: 1rem; scrollbar-width: thin; }
.library-topics button { flex: none; border-radius: 999px; padding: .4rem .85rem; border: 1px solid var(--border); color: var(--text-muted); font-size: calc(.875rem * var(--ui-scale, 1)); white-space: nowrap; }
.library-topics button[aria-pressed="true"] { color: var(--accent); border-color: var(--accent); background: rgba(75,184,232,.12); }
.library-topics button:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.run-mode-card { display: flex; align-items: flex-start; gap: .75rem; padding: .875rem; border: 1px solid var(--border-subtle); border-radius: .75rem; cursor: pointer; }
.run-mode-card input { margin-block-start: .2rem; accent-color: var(--accent); }
.run-mode-card:has(input:checked) { border-color: var(--accent); background: rgba(75,184,232,.06); }
.run-mode-card:focus-within { outline: 2px solid var(--accent); outline-offset: 2px; }
.graph-viewport { height: 100vh; height: 100dvh; width: 100%; }
#upload-modal[open] { display: flex; }
@media (max-height: 700px) { #upload-modal { padding: 1rem; gap: 0.75rem; } #upload-modal > div:first-child { gap: 0.5rem; } }
#upload-redaction-inspector { flex: 1 1 auto; scrollbar-width: thin; scrollbar-color: #738196 #04060F; }
#upload-redaction-inspector::-webkit-scrollbar { display: block; width: 6px; }
#upload-redaction-inspector::-webkit-scrollbar-thumb { background: #738196; border-radius: 6px; }
.visually-hidden:where(:not(:focus-within, :active)) { position: absolute; clip-path: inset(50%); overflow: hidden; width: 1px; height: 1px; margin: -1px; padding: 0; border: 0; white-space: nowrap; }
.visually-hidden:focus-visible + label { outline: 2px solid var(--accent); outline-offset: 4px; border-radius: 0.5rem; }
.skip-link:focus-visible { position: fixed; top: 0.75rem; left: 0.75rem; z-index: 90; padding: 0.55rem 1rem; border-radius: 0.75rem; background: var(--accent); color: var(--text-on-accent); font-size: 0.875rem; font-weight: 600; text-decoration: none; box-shadow: var(--dialog-shadow); }
:where(a:any-link, button, input, select, textarea, summary, [tabindex]:not([tabindex="-1"])):focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
input[type="range"].rag-slider { --slider-track-size: 0.375rem; --slider-thumb-size: 1rem; --slider-track-radius: 999px; --slider-thumb-radius: 50%; --slider-track-color: rgba(238,242,248,0.22); --slider-fill-color: #4BB8E8; --slider-thumb-color: var(--slider-fill-color); --attr-min: attr(min type(<number>), 0); --attr-max: attr(max type(<number>), 100); --control-value: attr(value type(<number>), 50); --slider-progress: calc(progress(var(--control-value), var(--attr-min), var(--attr-max)) * 100%); appearance: none; inline-size: 100%; block-size: 2rem; margin: 0; padding: 0; border: 0; background: transparent; cursor: pointer; }
@supports not (opacity: progress(1, 0, 100)) { input[type="range"].rag-slider { --slider-progress: calc((var(--control-value) - var(--attr-min)) / (var(--attr-max) - var(--attr-min)) * 100%); } }
input[type="range"].rag-slider::-webkit-slider-runnable-track { block-size: var(--slider-track-size); border: 0; border-radius: var(--slider-track-radius); background: linear-gradient(to right, var(--slider-fill-color) var(--slider-progress), var(--slider-track-color) var(--slider-progress)); }
input[type="range"].rag-slider::-webkit-slider-thumb { -webkit-appearance: none; appearance: none; inline-size: var(--slider-thumb-size); block-size: var(--slider-thumb-size); margin-block-start: calc((var(--slider-track-size) - var(--slider-thumb-size)) / 2); border: 0; border-radius: var(--slider-thumb-radius); background: var(--slider-thumb-color); }
input[type="range"].rag-slider::-moz-range-track { block-size: var(--slider-track-size); border: 0; border-radius: var(--slider-track-radius); background: var(--slider-track-color); }
input[type="range"].rag-slider::-moz-range-progress { block-size: var(--slider-track-size); border-radius: var(--slider-track-radius); background: var(--slider-fill-color); }
input[type="range"].rag-slider::-moz-range-thumb { inline-size: var(--slider-thumb-size); block-size: var(--slider-thumb-size); border: 0; border-radius: var(--slider-thumb-radius); background: var(--slider-thumb-color); }
input[type="range"].rag-slider:focus-visible { outline: 2px solid var(--slider-fill-color); outline-offset: 4px; }
.md-p { line-height: 1.72; }
.md-code-inline { padding: .125rem .375rem; border-radius: .375rem; background: #04060F; border: 1px solid rgba(238,242,248,.12); color: #4BB8E8; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .875em; }
.md-pre-wrap { border-radius: .75rem; background: #04060F; border: 1px solid rgba(238,242,248,.12); overflow: hidden; margin-block: .25rem; }
.md-pre-lang { padding: .375rem .875rem; font-family: ui-monospace, monospace; font-weight: 500; font-size: calc(.8125rem * var(--ui-scale, 1)); text-transform: uppercase; letter-spacing: .06em; color: #738196; border-bottom: 1px solid rgba(238,242,248,.08); }
.md-pre { margin: 0; padding: .875rem 1rem; overflow-x: auto; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: calc(.875rem * var(--ui-scale, 1)); line-height: 1.6; color: #DCE6F5; scrollbar-width: thin; }
.md-math { padding: .75rem 1rem; border-radius: .75rem; background: rgba(75,184,232,.06); border: 1px solid rgba(75,184,232,.18); text-align: center; overflow-x: auto; font-family: ui-monospace, monospace; font-size: calc(.9375rem * var(--ui-scale, 1)); line-height: 1.5; color: #EEF2F8; }
.md-table-wrap { overflow-x: auto; border-radius: .75rem; border: 1px solid rgba(238,242,248,.12); background: #04060F; margin-block: .25rem; }
.md-table { width: 100%; border-collapse: collapse; font-size: calc(.9375rem * var(--ui-scale, 1)); line-height: 1.55; text-align: left; }
.md-table th { padding: .625rem .875rem; color: #EEF2F8; font-weight: 600; background: rgba(238,242,248,.04); border-bottom: 1px solid rgba(238,242,248,.12); }
.md-table td { padding: .625rem .875rem; color: #C8D4E6; border-top: 1px solid rgba(238,242,248,.07); vertical-align: top; }
.md-quote { margin: .25rem 0; padding: .5rem 1rem; border-inline-start: 3px solid #4BB8E8; background: rgba(75,184,232,.06); border-radius: 0 .5rem .5rem 0; color: #C8D4E6; }
.md-hr { border: 0; border-top: 1px solid rgba(238,242,248,.10); margin-block: .5rem; }
.md-list { list-style: none; padding: 0; display: flex; flex-direction: column; gap: .4rem; margin-block: .125rem; }
.md-list-item { display: flex; align-items: flex-start; gap: .625rem; }
.md-list-marker { color: #4BB8E8; font-family: ui-monospace, monospace; font-size: calc(.875rem * var(--ui-scale, 1)); margin-top: .28rem; flex-shrink: 0; }
.md-link { color: #4BB8E8; text-decoration: underline; text-underline-offset: 3px; cursor: pointer; background: transparent; border: 0; padding: 0; font: inherit; text-align: left; }
.md-link:hover { color: #74D1FF; }
@media (prefers-reduced-motion: reduce) { ::view-transition-group(*), ::view-transition-old(*), ::view-transition-new(*) { animation: none !important; } }
</style>
<link rel="stylesheet" href="/static/ui.css" />
"""
    + THEME_BRIDGE_CSS
    + FORM_STYLES_CSS
    + COMMAND_STYLES_CSS
    + GUIDE_STYLES_CSS
    + EDITOR_STYLES_CSS
    + WORKFLOW_STYLES_CSS
    + STUDY_STYLES_CSS
    + POWER_STYLES_CSS
    + WORK_BOARD_STYLES_CSS
    + SPLIT_STYLES_CSS
    + IMPACT_FOCUS_STYLES_CSS
    + WORKFLOW_STUDIO_STYLES_CSS
    + SHELL_STYLES_CSS
    + """
</head>
<body class="bg-[#04060F] font-sans text-base text-[#EEF2F8] antialiased">
<a href="#main-content" data-i18n="skip_main" class="skip-link visually-hidden">Skip to main content</a>
<div id="sidebar-backdrop" hidden class="fixed inset-0 z-40"></div>
"""
    + ACTIVITY_RAIL_HTML
    + "\n"
    + SIDEBAR_HTML
    + """
<div id="main-shell" class="relative pl-[300px] min-h-screen bg-[#04060F] flex flex-col transition-all duration-200">
  <div id="ambient-stage" aria-hidden="true" class="ambient-stage"><canvas id="ambient-aurora-canvas" class="supernova-beam"></canvas><canvas id="ambient-dots-canvas"></canvas></div>
"""
    + APP_TOPBAR_HTML
    + '\n<div id="workbench-grid"><div id="workbench-center-col">\n'
    + '<div id="center-editor-row"><div id="center-primary-col">\n'
    + CENTER_TABBAR_HTML
    + '\n'
    + """  <main id="main-content" tabindex="-1" class="relative z-10 w-full flex-1 flex flex-col pt-0 outline-none">
    <div id="graph-view" class="graph-viewport hidden w-full relative overflow-hidden bg-[#04060F]"></div>
"""
    + WORK_BOARD_HTML
    + "\n"
    + FOCUS_VIEW_HTML
    + "\n"
    + IMPACT_VIEW_HTML
    + "\n"
    + WORKFLOWS_VIEW_HTML
    + "\n"
    + """    <div id="workspace-shell" class="flex flex-col w-full flex-1 justify-center items-center px-4 sm:px-6">
      <div id="active-stream" tabindex="-1" class="hidden w-full max-w-3xl flex-1 pt-8 pb-16 flex-col gap-8 outline-none">
        <div id="chat-stream" class="flex flex-col gap-8 w-full max-w-3xl"></div>
        <div id="tutor" class="w-full max-w-3xl"></div>
        <div id="stream-divider" class="hidden w-full max-w-3xl h-px bg-[rgba(238,242,248,0.08)] my-1"></div>
        <div id="chunks-header" class="hidden w-full max-w-3xl items-center justify-between gap-2"><button id="chunks-toggle-btn" type="button" class="text-sm text-[#A0B0C8] hover:text-[#EEF2F8] transition-colors"><span id="chunks-title" data-i18n="chunks_zero_hint">▸ View 0 source passages</span></button><span id="chunks-rag-pill" data-specialist-only class="px-2.5 py-0.5 rounded-full bg-[#0B1020] border border-[rgba(238,242,248,0.10)] text-2xs font-mono text-[#738196]">mode: hybrid · top-k: 5 · temp: 0.2</span></div>
        <div id="results" class="flex flex-col gap-4 w-full max-w-3xl"></div>
      </div>
      <div id="search-dock" class="w-full max-w-3xl mx-auto flex flex-col items-center justify-center relative z-30">
        <div id="hero-heading" class="text-center"><img id="hero-logo" src="/static/logo-512.png" width="56" height="56" fetchpriority="high" class="w-14 h-14 mx-auto mb-5" alt=""><h1 id="hero-greeting-text" data-i18n="hero_greeting" class="text-4xl font-normal tracking-tight mb-8 text-[#EEF2F8]">Where should we start?</h1></div>
        <search class="w-full relative">
          <form id="search-form" class="w-full">
            <div id="prompt-container" class="w-full rounded-full bg-[#0B1020] shadow-[inset_0_0_0_1px_rgba(238,242,248,0.16)] focus-within:shadow-[inset_0_0_0_1px_#4BB8E8] flex items-center py-3 px-4 gap-3 transition-all duration-200">
              <button id="prompt-upload-btn" type="button" title="Add Documents" aria-label="Add Documents" data-i18n-title="aria_add_docs" data-i18n-aria-label="aria_add_docs" class="bg-[#04060F] hover:bg-[#EEF2F8]/10 text-[#A0B0C8] hover:text-[#EEF2F8] w-9 h-9 rounded-full flex items-center justify-center text-lg leading-none shrink-0 transition">+</button>
              <div class="prompt-entry">
                <span id="scope-chip" hidden class="bg-[#4BB8E8]/15 text-[#4BB8E8] text-xs px-2.5 py-1 rounded-full flex items-center gap-1.5">
                  <span id="scope-chip-icon" aria-hidden="true" class="shrink-0"></span><span id="scope-chip-label"></span>
                  <button id="scope-reset-btn" type="button" aria-label="Clear scope" title="Clear scope" data-i18n-aria-label="aria_clear_scope" data-i18n-title="aria_clear_scope" class="shrink-0 w-5 h-5 rounded-full flex items-center justify-center hover:bg-white/10"><svg aria-hidden="true" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="m6 6 12 12M18 6 6 18"/></svg></button>
                </span>
                <span id="recipe-chip" hidden><span id="recipe-chip-label"></span><button id="recipe-reset-btn" type="button" aria-label="Clear command mode" data-i18n-aria-label="aria_clear_cmd" class="shrink-0 w-4 h-4 rounded-full flex items-center justify-center hover:bg-white/10"><svg aria-hidden="true" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="m6 6 12 12M18 6 6 18"/></svg></button></span>
                <span id="attached-chips" hidden></span>
                <textarea id="query" name="q" rows="1" aria-label="Ask a question" data-i18n-aria-label="aria_ask_question" autocomplete="off" spellcheck="false" placeholder="Ask anything..." data-i18n-placeholder="ask_placeholder" class="prompt-textarea bg-transparent border-0 outline-none text-[#EEF2F8] placeholder:text-[#738196]"></textarea>
              </div>
              <div class="flex items-center gap-2 pl-1 shrink-0">
                <button id="web-search-chat-btn" type="button" hidden aria-pressed="false" aria-label="Toggle live web search for this message" title="Web search OFF for this message" class="w-9 h-9 rounded-full text-[#A0B0C8] hover:text-[#EEF2F8] hover:bg-[#EEF2F8]/10 flex items-center justify-center shrink-0 transition">"""
    + ICON_GLOBE
    + """</button>
                <div class="relative flex items-center"><select id="model" aria-label="Model" data-i18n-aria-label="aria_model" class="appearance-none bg-transparent text-[#A0B0C8] hover:text-[#EEF2F8] text-sm font-medium pl-2.5 pr-6 py-1.5 rounded-full hover:bg-white/[0.04] outline-none transition-colors cursor-pointer"></select></div>
                <button id="mic-btn" type="button" aria-pressed="false" aria-label="Voice dictation" title="Voice dictation" data-i18n-aria-label="aria_voice_dictation" data-i18n-title="aria_voice_dictation" class="w-9 h-9 rounded-full text-[#A0B0C8] hover:text-[#EEF2F8] hover:bg-[#EEF2F8]/10 flex items-center justify-center shrink-0 transition">"""
    + ICON_MIC
    + """</button>
                <button id="prompt-submit-btn" type="submit" aria-label="Submit query" title="Submit query" data-i18n-aria-label="submit_query" data-i18n-title="submit_query" class="w-9 h-9 rounded-full bg-[#4BB8E8] text-[#04060F] hover:brightness-110 active:scale-95 flex items-center justify-center text-base font-semibold shrink-0 transition">↑</button>
              </div>
            </div>
          </form>
"""
    + SLASH_MENU_HTML
    + """          <p id="scope-status" role="status" class="visually-hidden"></p>
        </search>
        <div id="seed-chips" class="w-full max-w-3xl mt-5 flex flex-col gap-1.5 pl-4">
          <div id="seed-list" class="flex flex-col gap-1.5">
            <button class="seed-chip text-left text-[#A0B0C8] hover:text-[#EEF2F8] text-sm py-1.5 transition-colors flex items-center gap-2.5 group w-fit" data-seed="Summarize the key points across my documents" type="button"><span class="text-[#738196] group-hover:text-[#4BB8E8] transition-colors">↳</span><span>Summarize the key points across my documents</span></button>
            <button class="seed-chip text-left text-[#A0B0C8] hover:text-[#EEF2F8] text-sm py-1.5 transition-colors flex items-center gap-2.5 group w-fit" data-seed="Extract key action items and important details" type="button"><span class="text-[#738196] group-hover:text-[#4BB8E8] transition-colors">↳</span><span>Extract key action items and important details</span></button>
            <button class="seed-chip text-left text-[#A0B0C8] hover:text-[#EEF2F8] text-sm py-1.5 transition-colors flex items-center gap-2.5 group w-fit" data-seed="What should I focus on next?" type="button"><span class="text-[#738196] group-hover:text-[#4BB8E8] transition-colors">↳</span><span>What should I focus on next?</span></button>
          </div>
          <div class="flex flex-wrap items-center gap-5 mt-2 pt-1">
            <button id="more-ideas-btn" type="button" data-i18n="more_ideas" class="text-xs font-medium text-[#738196] hover:text-[#4BB8E8] transition-colors flex items-center gap-1">↻ More ideas</button>
            <button id="home-browse-btn" type="button" class="text-xs font-medium text-[#738196] hover:text-[#EEF2F8] transition-colors flex items-center gap-1.5"><span><span data-i18n="browse_guides_pre">Browse all </span><span id="home-guide-count">0</span><span data-i18n="browse_guides_post"> documents →</span></span></button>
          </div>
        </div>
      </div>
    </div>
  </main>
</div>
"""
    + CENTER_SPLIT_PANE_HTML
    + "\n</div>\n"
    + BOTTOM_PANEL_HTML
    + "\n</div>\n"
    + RIGHT_SIDEBAR_HTML
    + "\n</div>\n</div>\n"
    + r"""<dialog id="confirm-modal" closedby="any" aria-labelledby="confirm-title" aria-describedby="confirm-message" class="m-auto w-[calc(100%_-_2rem)] max-w-md rounded-2xl bg-[#0B1020] text-[#EEF2F8] border border-white/15 p-6 shadow-2xl"><h2 id="confirm-title" class="text-lg font-semibold">Delete item?</h2><p id="confirm-message" class="text-sm text-[#A0B0C8] leading-relaxed mt-3 mb-6 break-words"></p><form method="dialog" class="flex justify-end gap-3"><button id="confirm-cancel-btn" value="cancel" autofocus data-i18n="cancel" class="rounded-xl border border-white/15 px-4 py-2 text-sm">Cancel</button><button id="confirm-delete-btn" value="delete" data-i18n="delete_btn" class="rounded-xl bg-[#DC2626] text-white px-4 py-2 text-sm font-medium">Delete</button></form></dialog>
<dialog id="area-modal" closedby="any" aria-labelledby="area-modal-title" class="m-auto w-[calc(100%_-_2rem)] max-w-md rounded-2xl bg-[#0B1020] text-[#EEF2F8] border border-white/15 p-6 shadow-2xl"><h2 id="area-modal-title" class="text-lg font-semibold mb-4"><span data-everyday-only data-i18n="area_new_title">New Workspace</span><span data-specialist-only data-i18n="area_new_title">New Knowledge Area</span></h2><form id="new-area-form" class="flex flex-col gap-3"><label for="area-name" data-i18n="area_name_lbl" class="text-xs text-[#A0B0C8]">Workspace name</label><input id="area-name" name="area" autofocus required maxlength="64" placeholder="e.g. Care Notes" data-i18n-placeholder="area_name_ph" aria-describedby="area-name-help" class="rounded-lg bg-[#04060F] border border-white/15 px-3 py-2 text-sm"/><p id="area-name-help" data-i18n="area_name_help" class="text-xs text-[#738196]">Give it a name, like Care Notes. Each workspace keeps its documents and chats separate.</p>"""
    + AREA_TEMPLATE_SELECT
    + """<p id="new-area-status" role="status" class="text-xs text-[#A0B0C8]"></p><div class="flex justify-end gap-3"><button type="submit" formmethod="dialog" formnovalidate value="cancel" data-i18n="cancel" class="rounded-xl border border-white/15 px-4 py-2 text-sm">Cancel</button><button id="create-area-btn" type="submit" data-i18n="area_create_btn" class="rounded-xl bg-[#4BB8E8] text-[#04060F] px-4 py-2 text-sm font-medium">Create Workspace</button></div></form></dialog>"""
    + '<div id="upload-toast" role="status" aria-live="polite" class="hidden fixed top-5 left-1/2 -translate-x-1/2 z-[70] max-w-md rounded-xl border border-white/15 bg-[#0B1020] px-4 py-2.5 text-sm text-[#EEF2F8] shadow-2xl pointer-events-none text-center"></div>'
    + '<p id="app-live-status" role="status" aria-live="polite" aria-atomic="true" class="visually-hidden"></p>'
    + '<div id="global-drop-overlay" hidden aria-hidden="true" class="fixed inset-0 z-50 pointer-events-none flex items-center justify-center p-6"><div class="rounded-2xl border-2 border-dashed border-[#4BB8E8] bg-[#0B1020] px-8 py-6 flex flex-col items-center gap-2.5 shadow-2xl"><svg aria-hidden="true" class="w-8 h-8 text-[#4BB8E8]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 16V4m0 0-4 4m4-4 4 4M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/></svg><span data-i18n="drop_overlay_title" class="text-base font-medium text-[#EEF2F8]">Drop files or whole folders to add to your Library</span><span data-i18n="drop_overlay_sub" class="text-xs text-[#A0B0C8]">PDF, Word, Excel, PowerPoint, CSV, Markdown, or nested folders · Private &amp; local</span></div></div>'
    + MODALS_HTML
    + COMMAND_PALETTE_HTML
    + GUIDE_MODAL_HTML
    + EDITOR_MODALS_HTML
    + WORKFLOW_MODALS_HTML
    + STUDY_MODAL_HTML
    + POWER_MODAL_HTML
    + WORK_BOARD_MODALS_HTML
    + FOCUS_MODALS_HTML
    + IMPACT_MODALS_HTML
    + WORKFLOWS_MODALS_HTML
    + "\n"
    + CLIENT_SCRIPT
    + "\n</body>\n</html>\n"
)
