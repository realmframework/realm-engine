"""Shared True-DRY Chat Tab Strip, Center Open Chat Tabs & Docked Right Sidebar controller."""

WORKBENCH_TABS_SCRIPT: str = r"""
let wbTabSeq = 0;
let wbCenterIsChat = true;
let centerChatTabs = [{ id: "ct_0", kind: "chat", chatId: "", title: "", agentId: "", draft: "" }];
let activeCenterTabId = "ct_0";
const wbWorkingChats = new Set();
const wbUnreadChats = new Set();
const WB_PIN_SVG = "<svg class='wb-tab-pin' aria-hidden='true' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'><path d='M12 17v5'/><path d='M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16h14v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z'/></svg>";
const WB_SPIN_SVG = "<svg class='wb-tab-spin' aria-hidden='true' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.2' stroke-linecap='round'><circle cx='12' cy='12' r='9' stroke-opacity='0.22'/><path d='M21 12a9 9 0 0 0-9-9'/></svg>";

function isChatVisibleNow(chatId) {
  if (!chatId) { return false; }
  const fv = document.getElementById("center-file-view"), sh = document.getElementById("workspace-shell");
  if ((fv && !fv.hidden) || (sh && sh.classList.contains("hidden"))) { return false; }
  const cur = centerChatTabs.find(function (tb) { return tb.id === activeCenterTabId; });
  return Boolean(cur && cur.kind !== "file" && cur.chatId === chatId);
}

function setChatTabActivity(chatId, state) {
  if (!chatId) { return; }
  if (state === "working") { wbUnreadChats.delete(chatId); wbWorkingChats.add(chatId); }
  else if (state === "done") { wbWorkingChats.delete(chatId); if (!isChatVisibleNow(chatId)) { wbUnreadChats.add(chatId); } }
  else { wbWorkingChats.delete(chatId); }
  renderCenterChatTabs();
  if (typeof renderRecentChats === "function") { renderRecentChats(); }
}

function clearWorkingChats() {
  if (!wbWorkingChats.size) { return; }
  wbWorkingChats.clear();
  renderCenterChatTabs();
  if (typeof renderRecentChats === "function") { renderRecentChats(); }
}

function defaultChatTabLabel() {
  return t("new_chat").replace(/^\+\s*/, "");
}

function populateAgentSelect(sel, selectedId) {
  if (!sel) { return ""; }
  const list = typeof agentTeam !== "undefined" && Array.isArray(agentTeam) && agentTeam.length
    ? agentTeam
    : [{ id: "saga", name: "Saga" }, { id: "lisbeth", name: "Lisbeth" }, { id: "plague", name: "Plague" }];
  const chosen = list.some(function (a) { return a.id === selectedId; }) ? selectedId : list[0].id;
  sel.innerHTML = list.map(function (a) {
    return "<option value='" + escapeHtml(a.id) + "'" + (a.id === chosen ? " selected" : "") + ">" + escapeHtml(a.name) + "</option>";
  }).join("");
  sel.value = chosen;
  return chosen;
}

function renderChatTabStrip(listId, tabs, activeId, attrPrefix, onActivate, onClose) {
  const list = document.getElementById(listId); if (!list) { return activeId; }
  const selId = tabs.some(function (tb) { return tb.id === activeId; }) ? activeId : (tabs[0] ? tabs[0].id : "");
  const fallbackLabel = defaultChatTabLabel();
  list.innerHTML = tabs.map(function (tb) {
    const sel = tb.id === selId;
    const isFile = tb.kind === "file";
    const label = tb.title || fallbackLabel;
    const working = !isFile && tb.chatId && wbWorkingChats.has(tb.chatId);
    const unread = !isFile && tb.chatId && !working && wbUnreadChats.has(tb.chatId);
    const pinHtml = tb.pinned ? WB_PIN_SVG : "";
    const statusLead = working ? ("<span title='" + escapeHtml(t("st_chat_working")) + "' aria-label='" + escapeHtml(t("st_chat_working")) + "' class='inline-flex items-center'>" + WB_SPIN_SVG + "</span>")
      : (unread ? ("<span class='wb-tab-unread' title='" + escapeHtml(t("st_chat_unread")) + "' aria-label='" + escapeHtml(t("st_chat_unread")) + "'></span>") : "");
    const iconHtml = !statusLead && !tb.pinned && isFile && typeof FT_FILE_SVG !== "undefined" ? FT_FILE_SVG : "";
    const dirtyHtml = isFile && tb.dirty ? "<span class='wb-tab-dirty-dot' title='" + escapeHtml(t("st_file_modified")) + "' aria-label='" + escapeHtml(t("st_file_modified")) + "'></span>" : "";
    const closeAria = isFile ? "Close file tab" : "Close chat tab";
    const closeX = tabs.length > 1 && !tb.pinned
      ? "<span class='wb-tab-x' data-" + attrPrefix + "-close='" + escapeHtml(tb.id) + "' role='button' aria-label='" + closeAria + "'>✕</span>"
      : "";
    const pvCls = (isFile && tb.preview ? " is-preview" : "") + (tb.pinned ? " is-pinned" : "") + (isFile && tb.dirty ? " is-dirty" : "");
    return "<button type='button' role='tab' aria-selected='" + String(sel) + "' tabindex='" + (sel ? "0" : "-1") + "' data-" + attrPrefix + "-tab='" + escapeHtml(tb.id) + "' class='wb-zone-tab" + pvCls + "'>" + pinHtml + statusLead + iconHtml + "<span>" + escapeHtml(label) + "</span>" + dirtyHtml + closeX + "</button>";
  }).join("");
  list.querySelectorAll("[data-" + attrPrefix + "-tab]").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      const x = e.target.closest("[data-" + attrPrefix + "-close]");
      if (x) { e.stopPropagation(); onClose(x.getAttribute("data-" + attrPrefix + "-close")); return; }
      onActivate(btn.getAttribute("data-" + attrPrefix + "-tab"));
    });
    btn.addEventListener("dblclick", function () {
      const tid = btn.getAttribute("data-" + attrPrefix + "-tab");
      const tb = tabs.find(function (item) { return item.id === tid; });
      if (tb && tb.preview) { tb.preview = false; renderChatTabStrip(listId, tabs, selId, attrPrefix, onActivate, onClose); }
    });
    if (listId === "center-tablist") {
      btn.addEventListener("contextmenu", function (e) {
        e.preventDefault();
        if (typeof openTabContextMenu === "function") { openTabContextMenu(btn.getAttribute("data-" + attrPrefix + "-tab") || "", { x: e.clientX, y: e.clientY }); }
      });
    }
  });
  if (typeof bindRovingTablist === "function") {
    bindRovingTablist("#" + listId + " [role='tab']", function (btn) { onActivate(btn.getAttribute("data-" + attrPrefix + "-tab")); });
  }
  const activeEl = list.querySelector("[aria-selected='true']");
  if (activeEl && activeEl.scrollIntoView) { activeEl.scrollIntoView({ block: "nearest", inline: "nearest" }); }
  return selId;
}

function syncGlobalControlsWidth() {
  const ctrls = document.getElementById("wb-center-controls"), shell = document.getElementById("main-shell");
  if (!ctrls || !shell) { return; }
  const w = ctrls.offsetWidth;
  if (w > 0) { shell.style.setProperty("--center-ctrl-w", w + "px"); }
}

function syncCenterTabbarVisibility(isChatView) {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) { return; }
  wbCenterIsChat = Boolean(isChatView);
  const grp = document.getElementById("center-chat-tabs-group"), acts = document.getElementById("center-chat-actions");
  const curTab = centerChatTabs.find(function (tb) { return tb.id === activeCenterTabId; });
  const isFileTab = Boolean(curTab && curTab.kind === "file");
  const agSel = document.getElementById("center-agent-select");
  if (grp) { grp.hidden = !wbCenterIsChat; }
  if (acts) { acts.hidden = !wbCenterIsChat; }
  if (agSel) { agSel.hidden = !wbCenterIsChat || isFileTab; }
  if (typeof applyWorkbenchGrid === "function") { applyWorkbenchGrid(); }
  syncGlobalControlsWidth();
}

function setRightSidebarTab(tab) {
  const safe = tab === "inspector" ? "inspector" : "copilot";
  if (typeof wbLayout !== "undefined") { wbLayout.rightTab = safe; }
  document.querySelectorAll("[data-right-tab]").forEach(function (btn) {
    const sel = btn.getAttribute("data-right-tab") === safe;
    btn.setAttribute("aria-selected", String(sel));
    btn.tabIndex = sel ? 0 : -1;
  });
  const pc = document.getElementById("right-panel-copilot"), pi = document.getElementById("right-panel-inspector");
  if (pc) { pc.hidden = safe !== "copilot"; }
  if (pi) { pi.hidden = safe !== "inspector"; }
  if (typeof inspectorOpen !== "undefined" && typeof wbLayout !== "undefined") {
    inspectorOpen = Boolean(wbLayout.rightOpen && safe === "inspector");
  }
  if (safe === "copilot") {
    if (typeof syncCopilotContextUI === "function") { syncCopilotContextUI(); }
  } else {
    if (typeof syncInspectorSidebar === "function") { syncInspectorSidebar(); }
    if (typeof refreshContextUsage === "function") { refreshContextUsage(); }
  }
}

function setRightSidebarOpen(open, tab) {
  wbLayout.rightOpen = Boolean(open);
  if (tab === "copilot" || tab === "inspector") { wbLayout.rightTab = tab; }
  if (typeof inspectorOpen !== "undefined") { inspectorOpen = wbLayout.rightOpen && (wbLayout.rightTab || "copilot") === "inspector"; }
  applyWorkbenchGrid();
  if (wbLayout.rightOpen) { setRightSidebarTab(wbLayout.rightTab || "copilot"); }
  else if (typeof syncInspectorSidebar === "function") { syncInspectorSidebar(); }
}

function snapshotActiveCenterTab() {
  const cur = centerChatTabs.find(function (tb) { return tb.id === activeCenterTabId; });
  if (!cur || cur.kind === "file") { return; }
  if (typeof queryEl !== "undefined" && queryEl) { cur.draft = queryEl.value || ""; }
  if (typeof activeAgentId !== "undefined" && activeAgentId) { cur.agentId = activeAgentId; }
}

function renderCenterChatTabs() {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) { return; }
  if (!centerChatTabs.length) { centerChatTabs = [{ id: "ct_" + (++wbTabSeq), kind: "chat", chatId: "", title: "", agentId: "", draft: "" }]; }
  activeCenterTabId = renderChatTabStrip("center-tablist", centerChatTabs, activeCenterTabId, "ct", activateCenterChatTab, closeCenterChatTab);
}

function syncCenterChatTab(chatId, title) {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) {
    notifyParentFrame({ type: "realm:chat-state", chatId: chatId || "", title: title || "", agentId: typeof activeAgentId !== "undefined" ? activeAgentId : "", refreshChats: Boolean(chatId) });
    return;
  }
  const cid = chatId || "";
  if (cid) {
    const existing = centerChatTabs.find(function (tb) { return tb.kind !== "file" && tb.chatId === cid; });
    if (existing) {
      activeCenterTabId = existing.id;
      if (title) { existing.title = title; }
      renderCenterChatTabs();
      if (typeof renderWorkspaceFilesTree === "function") { renderWorkspaceFilesTree(); }
      return;
    }
    const cur = centerChatTabs.find(function (tb) { return tb.id === activeCenterTabId; });
    if (cur && cur.kind !== "file" && !cur.chatId) {
      cur.chatId = cid; cur.title = title || ""; cur.draft = "";
    } else {
      const id = "ct_" + (++wbTabSeq);
      centerChatTabs.push({ id: id, kind: "chat", chatId: cid, title: title || "", agentId: typeof activeAgentId !== "undefined" ? activeAgentId : "", draft: "" });
      activeCenterTabId = id;
    }
  } else {
    const cur = centerChatTabs.find(function (tb) { return tb.id === activeCenterTabId; });
    if (cur && cur.kind !== "file" && !cur.chatId) {
      renderCenterChatTabs();
      return;
    }
    const blank = centerChatTabs.find(function (tb) { return tb.kind !== "file" && !tb.chatId; });
    if (blank) { activeCenterTabId = blank.id; }
    else {
      const id = "ct_" + (++wbTabSeq);
      centerChatTabs.push({ id: id, kind: "chat", chatId: "", title: "", agentId: typeof defaultAgentId !== "undefined" ? defaultAgentId : "", draft: "" });
      activeCenterTabId = id;
    }
  }
  syncCenterTabbarVisibility(true);
  renderCenterChatTabs();
  if (typeof renderWorkspaceFilesTree === "function") { renderWorkspaceFilesTree(); }
  if (typeof syncCopilotContextUI === "function") { syncCopilotContextUI(); }
}

function activateCenterChatTab(tabId) {
  const tb = centerChatTabs.find(function (item) { return item.id === tabId; });
  if (!tb) { return; }
  if (tabId !== activeCenterTabId) { snapshotActiveCenterTab(); }
  activeCenterTabId = tb.id;
  const fv = document.getElementById("center-file-view");
  if (tb.kind === "file") {
    if (typeof stopActiveAudio === "function") { stopActiveAudio(); }
    if (typeof stopGraphSimulation === "function") { stopGraphSimulation(); }
    if (typeof closeWorkBoardView === "function") { closeWorkBoardView(); }
    if (typeof closeFocusView === "function") { closeFocusView(); }
    if (typeof closeImpactView === "function") { closeImpactView(); }
    if (typeof closeWorkflowsView === "function") { closeWorkflowsView(); }
    const shell = document.getElementById("workspace-shell"), gv = document.getElementById("graph-view");
    if (shell) { shell.classList.add("hidden"); }
    if (gv) { gv.classList.add("hidden"); }
    if (fv) { fv.hidden = false; }
    if (typeof setAmbientDimmed === "function") { setAmbientDimmed(true); }
    if (typeof setActiveRailSection === "function") { setActiveRailSection("files", false); }
    syncCenterTabbarVisibility(true);
    if (typeof renderCenterFileTab === "function") { renderCenterFileTab(tb); }
    renderCenterChatTabs();
    if (typeof ftPrefs !== "undefined" && ftPrefs.autoReveal && typeof ftRevealDocInTree === "function") { ftRevealDocInTree(tb.docId, true); }
    if (typeof syncInspectorSidebar === "function") { syncInspectorSidebar(); }
    return;
  }
  if (fv) { fv.hidden = true; }
  if (tb.chatId) { wbUnreadChats.delete(tb.chatId); }
  if (typeof setActiveRailSection === "function") { setActiveRailSection("chat", false); }
  if (tb.chatId) {
    if (tb.chatId !== currentChatId && typeof openSavedChat === "function") { openSavedChat(tb.chatId); }
    else if (typeof setViewMode === "function") { setViewMode(Boolean(currentTurns && currentTurns.length)); if (typeof renderRecentChats === "function") { renderRecentChats(); } }
  } else if (typeof resetHome === "function") {
    resetHome();
    if (typeof queryEl !== "undefined" && queryEl && tb.draft) {
      queryEl.value = tb.draft;
      if (typeof autoResizeQuery === "function") { autoResizeQuery(); }
    }
    if (tb.agentId && typeof activeAgentId !== "undefined" && tb.agentId !== activeAgentId && typeof selectAgentUI === "function") {
      selectAgentUI(tb.agentId);
    }
  }
  syncCenterTabbarVisibility(true);
  renderCenterChatTabs();
  if (typeof renderWorkspaceFilesTree === "function") { renderWorkspaceFilesTree(); }
  if (typeof syncCopilotContextUI === "function") { syncCopilotContextUI(); }
}

async function closeCenterChatTab(tabId, force) {
  const tb = centerChatTabs.find(function (item) { return item.id === tabId; });
  if (!tb) { return true; }
  if (!force && tb.kind === "file" && tb.dirty && typeof confirmUnsavedChanges === "function") {
    const ch = await confirmUnsavedChanges({ name: tb.filename || tb.title, canSave: !tb.readOnly });
    if (ch === "cancel") { return false; }
    if (ch === "save" && typeof saveCenterFileTab === "function") {
      await saveCenterFileTab(tb);
      if (tb.dirty) { return false; }
    }
  }
  const wasActive = activeCenterTabId === tabId;
  centerChatTabs = centerChatTabs.filter(function (item) { return item.id !== tabId; });
  if (!centerChatTabs.length) {
    centerChatTabs = [{ id: "ct_" + (++wbTabSeq), kind: "chat", chatId: "", title: "", agentId: "", draft: "" }];
  }
  if (wasActive) { activateCenterChatTab(centerChatTabs[centerChatTabs.length - 1].id); }
  else { renderCenterChatTabs(); if (typeof renderWorkspaceFilesTree === "function") { renderWorkspaceFilesTree(); } }
  return true;
}

function resetCenterChatTabsOnAreaChange() {
  centerChatTabs = [{ id: "ct_" + (++wbTabSeq), kind: "chat", chatId: "", title: "", agentId: "", draft: "" }];
  activeCenterTabId = centerChatTabs[0].id;
  const fv = document.getElementById("center-file-view");
  if (fv) { fv.hidden = true; }
  renderCenterChatTabs();
  if (typeof renderWorkspaceFilesTree === "function") { renderWorkspaceFilesTree(); }
}

function bindWorkbenchTabsUX() {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) { return; }
  const addBtn = document.getElementById("center-add-tab-btn");
  if (addBtn) {
    addBtn.addEventListener("click", function () {
      snapshotActiveCenterTab();
      const id = "ct_" + (++wbTabSeq);
      centerChatTabs.push({ id: id, kind: "chat", chatId: "", title: "", agentId: typeof defaultAgentId !== "undefined" ? defaultAgentId : "", draft: "" });
      activeCenterTabId = id;
      const fv = document.getElementById("center-file-view");
      if (fv) { fv.hidden = true; }
      if (typeof setActiveRailSection === "function") { setActiveRailSection("chat", false); }
      if (typeof resetHome === "function") { resetHome(); }
      syncCenterTabbarVisibility(true);
      renderCenterChatTabs();
      if (typeof renderWorkspaceFilesTree === "function") { renderWorkspaceFilesTree(); }
    });
  }
  const cAgSel = document.getElementById("center-agent-select");
  if (cAgSel) {
    cAgSel.addEventListener("change", function () {
      if (typeof selectAgentUI === "function" && cAgSel.value) { selectAgentUI(cAgSel.value); }
    });
  }
  renderCenterChatTabs();
  syncGlobalControlsWidth();
}
"""
