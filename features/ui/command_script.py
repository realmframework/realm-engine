"""Global Command Palette (Cmd/Ctrl+K) and inline / prompt commands with keyboard navigation."""

COMMAND_SCRIPT: str = r"""
let cmdFiltered = [], cmdActiveIdx = 0;
let slashFiltered = [], slashActiveIdx = 0, slashMenuOpen = false;

function cmdScore(query, text) {
  if (!query) { return 1; }
  const q = query.toLowerCase(), hay = String(text || "").toLowerCase();
  if (hay === q) { return 100; }
  if (hay.startsWith(q)) { return 80; }
  if (hay.includes(" " + q) || hay.includes("/" + q) || hay.includes("_" + q) || hay.includes("-" + q)) { return 60; }
  if (hay.includes(q)) { return 40; }
  let qi = 0;
  for (let i = 0; i < hay.length && qi < q.length; i++) { if (hay[i] === q[qi]) { qi++; } }
  return qi === q.length ? 20 : 0;
}

function buildCommandPaletteItems() {
  const items = [];
  const inChat = Boolean(typeof currentChatId !== "undefined" && currentChatId && Array.isArray(currentTurns) && currentTurns.length);
  items.push(
    { group: "cmd_grp_actions", id: "act-new-chat", label: t("new_chat"), sub: "", kbd: "", run: () => resetHome() },
    { group: "cmd_grp_actions", id: "act-free-chat", label: t("free_chat"), sub: (typeof freeChatMode !== "undefined" && freeChatMode) ? "ON" : "OFF", kbd: "", run: () => { if (typeof setFreeChatMode === "function") { setFreeChatMode(!freeChatMode); } } },
    { group: "cmd_grp_actions", id: "act-library", label: t("library"), sub: String(workspaceDocCount || 0), kbd: "", run: () => { setActiveTag(null); openLibraryCatalog(null); } },
    { group: "cmd_grp_actions", id: "act-work-board", label: t("work_board_nav"), sub: "Work OS", kbd: "", run: () => { if (typeof openWorkBoardView === "function") { openWorkBoardView("kanban"); } } },
    { group: "cmd_grp_actions", id: "act-focus", label: t("focus_nav"), sub: "Work OS", kbd: "", run: () => { if (typeof openFocusView === "function") { openFocusView(); } } },
    { group: "cmd_grp_actions", id: "act-impact", label: t("impact_nav"), sub: "Work OS", kbd: "", run: () => { if (typeof openImpactView === "function") { openImpactView("roi"); } } },
    { group: "cmd_grp_actions", id: "act-workflows", label: t("workflows_nav"), sub: "", kbd: "", run: () => { if (typeof openWorkflowsView === "function") { openWorkflowsView(); } } },
    { group: "cmd_grp_actions", id: "act-split-chat", label: t("sh_toggle_right"), sub: "", kbd: "", run: () => { if (typeof openSplitChat === "function") { if (typeof wbLayout !== "undefined" && wbLayout.splitOpen) { closeSplitChat(); } else { openSplitChat({}); } } } },
    { group: "cmd_grp_actions", id: "act-bottom-panel", label: t("sh_toggle_bottom"), sub: "", kbd: "", run: () => { if (typeof toggleBottomPanel === "function") { toggleBottomPanel(); } } },
    { group: "cmd_grp_actions", id: "act-right-sidebar", label: t("sh_toggle_right_sb"), sub: "", kbd: "", run: () => { if (typeof setRightSidebarOpen === "function" && typeof wbLayout !== "undefined") { setRightSidebarOpen(!wbLayout.rightOpen); } } },
    { group: "cmd_grp_actions", id: "act-graph", label: t("graph_view"), sub: "2D", kbd: "", run: () => { setActiveTag(null); openGraphView(); } },
    { group: "cmd_grp_actions", id: "act-agents", label: t("agents_nav"), sub: typeof activeAgentName === "function" ? activeAgentName() : "", kbd: "", run: () => { if (typeof openAgentStudio === "function") { openAgentStudio("roster"); } } },
    { group: "cmd_grp_actions", id: "act-formats", label: t("formats_nav"), sub: "", kbd: "", run: () => { if (typeof openFormatStudio === "function") { openFormatStudio("browse"); } } },
    { group: "cmd_grp_actions", id: "act-upload", label: t("up_title"), sub: "", kbd: "", run: () => openUploadDialog() },
    { group: "cmd_grp_actions", id: "act-new-note", label: t("lib_new_note"), sub: ".md", kbd: "", run: () => { if (typeof openNewNoteModal === "function") { openNewNoteModal(); } } },
    { group: "cmd_grp_actions", id: "act-gap-scan", label: t("gap_title"), sub: "", kbd: "", run: () => { if (typeof openGapAnalysisModal === "function") { openGapAnalysisModal(); } } },
    { group: "cmd_grp_actions", id: "act-study", label: t("study_title"), sub: "", kbd: "", run: () => { if (typeof openStudyDeck === "function") { openStudyDeck({}); } } },
    { group: "cmd_grp_actions", id: "act-briefing", label: t("br_title"), sub: "", kbd: "", run: () => { if (typeof openBriefingModal === "function") { openBriefingModal({}); } } },
    { group: "cmd_grp_actions", id: "act-voice-loop", label: t("vl_title"), sub: (typeof voiceLoopEnabled !== "undefined" && voiceLoopEnabled) ? "ON" : "OFF", kbd: "", run: () => { if (typeof setVoiceLoopEnabled === "function") { setVoiceLoopEnabled(!voiceLoopEnabled); } } },
    { group: "cmd_grp_actions", id: "act-new-area", label: t("new_area_btn"), sub: "", kbd: "", run: () => openNewAreaDialog() },
    { group: "cmd_grp_actions", id: "act-link-folder", label: t("open_vault"), sub: "", kbd: "", run: () => linkExistingFolder() },
    { group: "cmd_grp_actions", id: "act-settings", label: t("settings"), sub: "", kbd: "", run: () => openSettings("workspace") },
    { group: "cmd_grp_actions", id: "act-guide", label: t("guide_title"), sub: "/help", kbd: "", run: () => { if (typeof openGuideModal === "function") { openGuideModal(); } } },
    { group: "cmd_grp_actions", id: "act-appearance", label: t("tab_appearance"), sub: t("a11y_section_title"), kbd: "", run: () => openSettings("appearance") },
    { group: "cmd_grp_actions", id: "act-theme", label: t("cmd_act_theme_toggle"), sub: "", kbd: "", run: () => { const cur = (workspaceConfig && workspaceConfig.theme_mode) || "system", darkNow = cur === "dark" || (cur === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches), next = darkNow ? "light" : "dark", acc = (workspaceConfig && workspaceConfig.theme_accent) || "#4BB8E8", gl = (workspaceConfig && workspaceConfig.theme_glow) || "#6366F1"; applyThemeTokens(next, acc, gl, true); persistThemeWorkspace(next, acc, gl); } },
    { group: "cmd_grp_actions", id: "act-motion", label: t("cmd_act_reduce_motion"), sub: (typeof readingComfort !== "undefined" && readingComfort.reduce_motion) ? "ON" : "OFF", kbd: "", run: () => { if (typeof updateReadingComfort === "function") { updateReadingComfort({ reduce_motion: !readingComfort.reduce_motion }); } } },
    { group: "cmd_grp_actions", id: "act-eco", label: t("eco_title"), sub: (workspaceConfig && workspaceConfig.eco_mode) ? "ON" : "OFF", kbd: "", run: () => { if (typeof setEcoModeUI === "function") { setEcoModeUI(!(workspaceConfig && workspaceConfig.eco_mode)); } } }
  );
  if (inChat) {
    items.push(
      { group: "cmd_grp_actions", id: "act-inspector", label: t("cmd_act_inspector"), sub: "", kbd: "", run: () => { if (typeof setInspectorOpen === "function") { setInspectorOpen(true); } } },
      { group: "cmd_grp_actions", id: "act-exp-pdf", label: t("cmd_act_export_pdf"), sub: ".pdf", kbd: "", run: () => { if (typeof exportFullChatPdf === "function") { exportFullChatPdf(); } } },
      { group: "cmd_grp_actions", id: "act-exp-md", label: t("cmd_act_export_md"), sub: ".md", kbd: "", run: () => { if (typeof runChatAction === "function") { runChatAction(false, "md"); } } }
    );
  }
  if (typeof agentTeam !== "undefined" && Array.isArray(agentTeam)) {
    for (const ag of agentTeam) {
      items.push({ group: "cmd_grp_agents", id: "ag-" + ag.id, label: ag.name, sub: ag.role || ag.tagline || "", color: (typeof paletteColorsFor === "function" ? paletteColorsFor(ag.palette).accent : "#4BB8E8"), run: () => { if (typeof selectAgentUI === "function") { selectAgentUI(ag.id); } } });
    }
  }
  if (Array.isArray(knowledgeAreas)) {
    for (const area of knowledgeAreas) {
      items.push({ group: "cmd_grp_workspaces", id: "ws-" + area.name, label: areaTitle(area), sub: String(area.doc_count || 0), color: area.color || "#4BB8E8", run: () => switchKnowledgeArea(area.name) });
    }
  }
  if (typeof availableFormats !== "undefined" && Array.isArray(availableFormats)) {
    for (const fmt of availableFormats) {
      items.push({ group: "cmd_grp_formats", id: "fmt-" + fmt.id, label: fmt.name, sub: fmt.description || "", run: () => { if (typeof pinFormat === "function") { pinFormat(fmt.id); if (typeof showToast === "function") { showToast(t("slash_pinned_fmt", { name: fmt.name }), 3000); } } } });
    }
  }
  if (Array.isArray(allGuides)) {
    for (const g of allGuides.slice(0, 60)) {
      const sub = [g.subfolder, Array.isArray(g.tags) ? g.tags.slice(0, 3).join(", ") : ""].filter(Boolean).join(" · ");
      items.push({ group: "cmd_grp_guides", id: "doc-" + g.doc_id, label: g.title || g.doc_id, sub: sub, run: () => renderGuideReader(g, null, -1) });
    }
  }
  if (Array.isArray(savedChats)) {
    for (const c of savedChats.slice(0, 30)) {
      items.push({ group: "cmd_grp_chats", id: "chat-" + c.chat_id, label: c.title || c.chat_id, sub: "", run: () => openSavedChat(c.chat_id) });
    }
  }
  return items;
}

function renderCommandResults(queryText) {
  const listEl = document.getElementById("cmd-palette-list"), countEl = document.getElementById("cmd-palette-count"), inputEl = document.getElementById("cmd-palette-input");
  if (!listEl) { return; }
  const q = String(queryText || "").trim();
  const scored = [];
  for (const item of buildCommandPaletteItems()) {
    const score = Math.max(cmdScore(q, item.label), Math.floor(cmdScore(q, item.sub) * 0.7), Math.floor(cmdScore(q, t(item.group)) * 0.5));
    if (!q || score > 0) { scored.push({ item, score }); }
  }
  if (q) { scored.sort((a, b) => b.score - a.score); }
  cmdFiltered = scored.slice(0, 48).map(s => s.item);
  cmdActiveIdx = cmdFiltered.length ? Math.min(cmdActiveIdx, cmdFiltered.length - 1) : 0;
  if (countEl) { countEl.textContent = cmdFiltered.length ? t("cmd_matches_n", { n: cmdFiltered.length }) : ""; }
  if (!cmdFiltered.length) {
    listEl.innerHTML = "<div class='px-4 py-6 text-center text-sm text-[#738196]'>" + escapeHtml(t("cmd_no_matches")) + "</div>";
    if (inputEl) { inputEl.removeAttribute("aria-activedescendant"); }
    return;
  }
  let html = "", lastGroup = "";
  cmdFiltered.forEach(function (item, idx) {
    if (!q && item.group !== lastGroup) {
      lastGroup = item.group;
      html += "<div role='presentation' class='px-2.5 pt-2.5 pb-1 text-2xs font-mono uppercase tracking-wider text-[#738196]'>" + escapeHtml(t(item.group)) + "</div>";
    }
    const dot = item.color ? "<span aria-hidden='true' class='w-2 h-2 rounded-full shrink-0' style='background:" + item.color + "'></span>" : "";
    const sub = item.sub ? "<span class='ml-auto text-xs text-[#738196] truncate' style='max-width:14rem'>" + escapeHtml(item.sub) + "</span>" : "";
    const optId = "cmd-opt-" + idx;
    html += "<button type='button' id='" + optId + "' role='option' aria-selected='" + (idx === cmdActiveIdx ? "true" : "false") + "' data-cmd-idx='" + idx + "' class='cmd-item'>"
      + dot + "<span class='truncate font-medium'>" + escapeHtml(item.label) + "</span>" + sub + "</button>";
  });
  listEl.innerHTML = html;
  syncCommandSelection(false);
  listEl.querySelectorAll("[data-cmd-idx]").forEach(function (btn) {
    btn.addEventListener("mouseenter", function () { cmdActiveIdx = Number(btn.getAttribute("data-cmd-idx") || 0); syncCommandSelection(false); });
    btn.addEventListener("click", function () { executeCommandItem(Number(btn.getAttribute("data-cmd-idx") || 0)); });
  });
}

function syncCommandSelection(scrollInto) {
  const listEl = document.getElementById("cmd-palette-list"), inputEl = document.getElementById("cmd-palette-input");
  if (!listEl) { return; }
  listEl.querySelectorAll("[data-cmd-idx]").forEach(function (btn) {
    const active = Number(btn.getAttribute("data-cmd-idx")) === cmdActiveIdx;
    btn.setAttribute("aria-selected", String(active));
    if (active && scrollInto) { btn.scrollIntoView({ block: "nearest" }); }
  });
  if (inputEl && cmdFiltered[cmdActiveIdx]) { inputEl.setAttribute("aria-activedescendant", "cmd-opt-" + cmdActiveIdx); }
}

function executeCommandItem(idx) {
  const item = cmdFiltered[idx];
  const modal = document.getElementById("cmd-palette-modal");
  if (modal && modal.open) { modal.close(); }
  if (item && typeof item.run === "function") { item.run(); }
}

function openCommandPalette() {
  const modal = document.getElementById("cmd-palette-modal"), inp = document.getElementById("cmd-palette-input");
  if (!modal) { return; }
  if (modal.open) { modal.close(); return; }
  closeSlashMenu();
  if (inp) { inp.value = ""; inp.setAttribute("aria-expanded", "true"); }
  cmdActiveIdx = 0;
  renderCommandResults("");
  modal.showModal();
  if (inp) { inp.focus(); }
}

function buildSlashCommands() {
  const cmds = [
    { group: "slash_grp_recipes", slug: "explain", label: "/explain", chip: t("slash_chip_explain"), desc: t("slash_explain_d"), kind: "recipe", prefix: t("slash_explain_p") },
    { group: "slash_grp_recipes", slug: "summarize", label: "/summarize", chip: t("slash_chip_summarize"), desc: t("slash_summarize_d"), kind: "recipe", prefix: t("slash_summarize_p") },
    { group: "slash_grp_recipes", slug: "quiz", label: "/quiz", chip: t("slash_chip_quiz"), desc: t("slash_quiz_d"), kind: "recipe", prefix: t("slash_quiz_p") },
    { group: "slash_grp_recipes", slug: "compare", label: "/compare", chip: t("slash_chip_compare"), desc: t("slash_compare_d"), kind: "recipe", prefix: t("slash_compare_p") },
    { group: "slash_grp_recipes", slug: "eli5", label: "/eli5", chip: t("slash_chip_eli5"), desc: t("slash_eli5_d"), kind: "recipe", prefix: t("slash_eli5_p") },
    { group: "slash_grp_recipes", slug: "translate", label: "/translate", chip: t("slash_chip_translate"), desc: t("slash_translate_d"), kind: "recipe", prefix: t("slash_translate_p") },
    { group: "slash_grp_recipes", slug: "factcheck", label: "/factcheck", chip: t("slash_chip_factcheck"), desc: t("slash_factcheck_d"), kind: "recipe", prefix: t("slash_factcheck_p") },
  ];
  if (typeof agentTeam !== "undefined" && Array.isArray(agentTeam)) {
    for (const ag of agentTeam) {
      const slug = String(ag.id || ag.name || "").toLowerCase().replace(/[^a-z0-9_-]+/g, "");
      if (slug) {
        cmds.push({ group: "slash_grp_agents", slug: slug, label: "/" + slug, desc: ag.name + (ag.role ? " — " + ag.role : ""), kind: "agent", agentId: ag.id, agentName: ag.name, color: (typeof paletteColorsFor === "function" ? paletteColorsFor(ag.palette).accent : "#4BB8E8") });
      }
    }
  }
  if (typeof availableFormats !== "undefined" && Array.isArray(availableFormats)) {
    for (const fmt of availableFormats) {
      const slug = String(fmt.id || "").toLowerCase().replace(/[^a-z0-9_-]+/g, "");
      if (slug) {
        cmds.push({ group: "slash_grp_formats", slug: slug, label: "/" + slug, desc: fmt.name + (fmt.description ? " — " + fmt.description : ""), kind: "format", formatId: fmt.id, formatName: fmt.name });
      }
    }
  }
  cmds.push(
    { group: "slash_grp_modes", slug: "free", label: "/free", desc: t("slash_free_d"), kind: "mode", action: () => { if (typeof setFreeChatMode === "function") { setFreeChatMode(!freeChatMode); } } },
    { group: "slash_grp_modes", slug: "new", label: "/new", desc: t("slash_new_d"), kind: "mode", action: () => resetHome() },
    { group: "slash_grp_modes", slug: "cards", label: "/cards", desc: t("slash_cards_d"), kind: "mode", action: () => { if (typeof openStudyDeck === "function") { openStudyDeck({}); } } },
    { group: "slash_grp_modes", slug: "gaps", label: "/gaps", desc: t("slash_gaps_d"), kind: "mode", action: () => { if (typeof openGapAnalysisModal === "function") { openGapAnalysisModal(); } } },
    { group: "slash_grp_modes", slug: "help", label: "/help", desc: t("slash_help_d"), kind: "mode", action: () => { if (typeof openGuideModal === "function") { openGuideModal(); } } }
  );
  return cmds;
}

function closeSlashMenu() {
  const menu = document.getElementById("slash-cmd-menu");
  slashMenuOpen = false;
  slashFiltered = [];
  if (menu) { menu.hidden = true; menu.replaceChildren(); }
  if (queryEl) { queryEl.removeAttribute("role"); queryEl.removeAttribute("aria-autocomplete"); queryEl.removeAttribute("aria-expanded"); queryEl.removeAttribute("aria-controls"); queryEl.removeAttribute("aria-activedescendant"); }
}

function syncSlashSelection() {
  const menu = document.getElementById("slash-cmd-menu");
  if (!menu) { return; }
  menu.querySelectorAll("[data-slash-idx]").forEach(function (btn) {
    const on = Number(btn.getAttribute("data-slash-idx")) === slashActiveIdx;
    btn.setAttribute("aria-selected", String(on));
    if (on) { btn.scrollIntoView({ block: "nearest" }); }
  });
  if (queryEl && slashFiltered[slashActiveIdx]) { queryEl.setAttribute("aria-activedescendant", "slash-opt-" + slashActiveIdx); }
}

async function applySlashCommand(cmd, trailingText, autoSend) {
  closeSlashMenu();
  const rest = String(trailingText || "").trim();
  if (cmd.kind === "recipe") {
    const autoQ = autoSend ? (rest || (typeof standaloneRecipeQuery === "function" ? standaloneRecipeQuery(cmd) : "")) : "";
    if (autoQ) {
      queryEl.value = ""; if (typeof clearActiveSlashRecipe === "function") { clearActiveSlashRecipe(); }
      if (typeof autoResizeQuery === "function") { autoResizeQuery(); }
      runSearch(true, { displayQuery: autoQ, instructionPrefix: cmd.prefix }); return;
    }
    if (typeof setActiveSlashRecipe === "function") { setActiveSlashRecipe(cmd); }
    queryEl.value = rest; if (typeof autoResizeQuery === "function") { autoResizeQuery(); } queryEl.focus(); return;
  }
  if (cmd.kind === "agent") {
    queryEl.value = rest; if (typeof autoResizeQuery === "function") { autoResizeQuery(); } queryEl.focus();
    if (typeof selectAgentUI === "function") { await selectAgentUI(cmd.agentId); }
    if (typeof showToast === "function") { showToast(t("slash_switched_agent", { name: cmd.agentName }), 2800); }
    if (autoSend && rest) { submitQuery(); }
    return;
  }
  if (cmd.kind === "format") {
    if (typeof pinFormat === "function") { pinFormat(cmd.formatId); }
    if (typeof showToast === "function") { showToast(t("slash_pinned_fmt", { name: cmd.formatName }), 2800); }
    queryEl.value = rest; if (typeof autoResizeQuery === "function") { autoResizeQuery(); } queryEl.focus();
    if (autoSend && rest) { submitQuery(); }
    return;
  }
  if (cmd.kind === "mode" && typeof cmd.action === "function") {
    queryEl.value = rest; if (typeof autoResizeQuery === "function") { autoResizeQuery(); } cmd.action(); queryEl.focus();
  }
}

function updateSlashMenu() {
  const menu = document.getElementById("slash-cmd-menu");
  if (!menu || !queryEl) { return; }
  const val = queryEl.value;
  if (!val.startsWith("/") || /\s/.test(val.slice(1))) { closeSlashMenu(); return; }
  const needle = val.slice(1).toLowerCase();
  const all = buildSlashCommands();
  const scored = [];
  for (const cmd of all) {
    const s = Math.max(cmdScore(needle, cmd.slug), Math.floor(cmdScore(needle, cmd.desc) * 0.5));
    if (!needle || s > 0) { scored.push({ cmd, s }); }
  }
  if (needle) { scored.sort((a, b) => b.s - a.s); }
  slashFiltered = scored.slice(0, 12).map(x => x.cmd);
  if (!slashFiltered.length) { closeSlashMenu(); return; }
  slashActiveIdx = Math.min(slashActiveIdx, slashFiltered.length - 1);
  let html = "", lastGroup = "";
  slashFiltered.forEach(function (cmd, idx) {
    if (!needle && cmd.group !== lastGroup) {
      lastGroup = cmd.group;
      html += "<div role='presentation' class='px-2.5 pt-2 pb-1 text-2xs font-mono uppercase tracking-wider text-[#738196]'>" + escapeHtml(t(cmd.group)) + "</div>";
    }
    const dot = cmd.color ? "<span aria-hidden='true' class='w-2 h-2 rounded-full shrink-0' style='background:" + cmd.color + "'></span>" : "";
    html += "<button type='button' id='slash-opt-" + idx + "' role='option' aria-selected='" + (idx === slashActiveIdx ? "true" : "false") + "' data-slash-idx='" + idx + "' class='slash-item'>"
      + dot + "<span class='font-mono text-xs text-[#4BB8E8] shrink-0'>" + escapeHtml(cmd.label) + "</span><span class='text-xs text-[#A0B0C8] truncate'>" + escapeHtml(cmd.desc) + "</span></button>";
  });
  menu.innerHTML = html;
  menu.hidden = false; slashMenuOpen = true;
  queryEl.setAttribute("role", "combobox"); queryEl.setAttribute("aria-autocomplete", "list");
  queryEl.setAttribute("aria-expanded", "true"); queryEl.setAttribute("aria-controls", "slash-cmd-menu");
  syncSlashSelection();
  menu.querySelectorAll("[data-slash-idx]").forEach(function (btn) {
    btn.addEventListener("mouseenter", function () { slashActiveIdx = Number(btn.getAttribute("data-slash-idx") || 0); syncSlashSelection(); });
    btn.addEventListener("mousedown", function (e) { e.preventDefault(); applySlashCommand(slashFiltered[Number(btn.getAttribute("data-slash-idx") || 0)], "", false); });
  });
}

function tryExpandInlineSlashSubmit() {
  if (!queryEl) { return false; }
  const raw = queryEl.value.trim();
  if (!raw.startsWith("/")) { return false; }
  const space = raw.indexOf(" ");
  const token = (space === -1 ? raw.slice(1) : raw.slice(1, space)).toLowerCase();
  const rest = space === -1 ? "" : raw.slice(space + 1).trim();
  const exact = buildSlashCommands().find(c => c.slug === token);
  if (!exact) { return false; }
  applySlashCommand(exact, rest, true);
  return true;
}

function bindCommandUX() {
  const modal = document.getElementById("cmd-palette-modal"), inp = document.getElementById("cmd-palette-input"), sideBtn = document.getElementById("sidebar-cmd-btn");
  const closeBtn = document.getElementById("close-cmd-palette");
  const kbdEl = document.getElementById("sidebar-cmd-kbd"), recReset = document.getElementById("recipe-reset-btn");
  if (kbdEl && !/mac|iphone|ipad/i.test(navigator.platform || navigator.userAgent || "")) { kbdEl.textContent = "Ctrl K"; }
  if (modal && inp) { modal.addEventListener("close", function () { inp.setAttribute("aria-expanded", "false"); }); }
  if (closeBtn && modal) { closeBtn.addEventListener("click", function () { if (modal.open) { modal.close(); } }); }
  if (sideBtn) { sideBtn.addEventListener("click", openCommandPalette); }
  if (recReset) { recReset.addEventListener("click", () => { if (typeof clearActiveSlashRecipe === "function") { clearActiveSlashRecipe(); } if (queryEl) { queryEl.focus(); } }); }
  if (inp) {
    inp.addEventListener("input", function () { cmdActiveIdx = 0; renderCommandResults(inp.value); });
    inp.addEventListener("keydown", function (e) {
      if (!cmdFiltered.length) { return; }
      if (e.key === "ArrowDown") { e.preventDefault(); cmdActiveIdx = (cmdActiveIdx + 1) % cmdFiltered.length; syncCommandSelection(true); }
      else if (e.key === "ArrowUp") { e.preventDefault(); cmdActiveIdx = (cmdActiveIdx - 1 + cmdFiltered.length) % cmdFiltered.length; syncCommandSelection(true); }
      else if (e.key === "Home") { e.preventDefault(); cmdActiveIdx = 0; syncCommandSelection(true); }
      else if (e.key === "End") { e.preventDefault(); cmdActiveIdx = cmdFiltered.length - 1; syncCommandSelection(true); }
      else if (e.key === "Enter") { e.preventDefault(); if (e.isComposing || e.keyCode === 229) { return; } executeCommandItem(cmdActiveIdx); }
    });
  }
  document.addEventListener("keydown", function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      if (modal && modal.open) { modal.close(); return; }
      const otherOpen = document.querySelector("dialog[open]");
      if (otherOpen) { otherOpen.close(); }
      openCommandPalette();
    }
  });
  if (queryEl) {
    queryEl.addEventListener("input", function () { if (typeof autoResizeQuery === "function") { autoResizeQuery(); } updateSlashMenu(); if (typeof updateMentionMenu === "function") { updateMentionMenu(); } });
    queryEl.addEventListener("keydown", function (e) {
      if (typeof handleMentionKeydown === "function" && handleMentionKeydown(e)) { return; }
      if (slashMenuOpen && slashFiltered.length) {
        if (e.key === "ArrowDown") { e.preventDefault(); slashActiveIdx = (slashActiveIdx + 1) % slashFiltered.length; syncSlashSelection(); return; }
        if (e.key === "ArrowUp") { e.preventDefault(); slashActiveIdx = (slashActiveIdx - 1 + slashFiltered.length) % slashFiltered.length; syncSlashSelection(); return; }
        if (e.key === "Tab" || e.key === "Enter") { e.preventDefault(); if (e.key === "Enter" && (e.isComposing || e.keyCode === 229)) { return; } applySlashCommand(slashFiltered[slashActiveIdx], "", false); return; }
        if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); closeSlashMenu(); return; }
      }
      if (e.key === "Backspace" && !queryEl.value && typeof activeSlashRecipe !== "undefined" && activeSlashRecipe) { clearActiveSlashRecipe(); return; }
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (e.isComposing || e.keyCode === 229) { return; }
        const form = document.getElementById("search-form");
        if (form && form.requestSubmit) { form.requestSubmit(); } else { submitQuery(); }
      }
    });
    document.addEventListener("click", function (e) {
      const menu = document.getElementById("slash-cmd-menu");
      if (slashMenuOpen && menu && !menu.contains(e.target) && e.target !== queryEl) { closeSlashMenu(); }
    });
  }
}
"""
