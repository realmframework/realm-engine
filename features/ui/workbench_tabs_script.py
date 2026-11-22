"""Shared True-DRY Chat Tab Strip, Center Open Chat Tabs & Docked Right Sidebar controller."""

WORKBENCH_TABS_SCRIPT: str = r"""
let wbTabSeq = 0;
let wbCenterIsChat = true;
let centerChatTabs = [{ id: "ct_0", chatId: "", title: "", agentId: "", draft: "" }];
let activeCenterTabId = "ct_0";

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
    const label = tb.title || fallbackLabel;
    const closeX = tabs.length > 1
      ? "<span class='wb-tab-x' data-" + attrPrefix + "-close='" + escapeHtml(tb.id) + "' role='button' aria-label='Close chat tab'>✕</span>"
      : "";
    return "<button type='button' role='tab' aria-selected='" + String(sel) + "' tabindex='" + (sel ? "0" : "-1") + "' data-" + attrPrefix + "-tab='" + escapeHtml(tb.id) + "' class='wb-zone-tab'><span>" + escapeHtml(label) + "</span>" + closeX + "</button>";
  }).join("");
  list.querySelectorAll("[data-" + attrPrefix + "-tab]").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      const x = e.target.closest("[data-" + attrPrefix + "-close]");
      if (x) { e.stopPropagation(); onClose(x.getAttribute("data-" + attrPrefix + "-close")); return; }
      onActivate(btn.getAttribute("data-" + attrPrefix + "-tab"));
    });
  });
  if (typeof bindRovingTablist === "function") {
    bindRovingTablist("#" + listId + " [role='tab']", function (btn) { onActivate(btn.getAttribute("data-" + attrPrefix + "-tab")); });
  }
  const activeEl = list.querySelector("[aria-selected='true']");
  if (activeEl && activeEl.scrollIntoView) { activeEl.scrollIntoView({ block: "nearest", inline: "nearest" }); }
  return selId;
}

function syncGlobalControlsWidth() {
  const ctrls = document.getElementById("wb-global-controls"), shell = document.getElementById("main-shell");
  if (!ctrls || !shell) { return; }
  const w = ctrls.offsetWidth;
  if (w > 0) { shell.style.setProperty("--global-ctrl-w", (w + 4) + "px"); }
}

function syncCenterTabbarVisibility(isChatView) {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) { return; }
  wbCenterIsChat = Boolean(isChatView);
  const grp = document.getElementById("center-chat-tabs-group"), acts = document.getElementById("center-chat-actions");
  if (grp) { grp.hidden = !wbCenterIsChat; }
  if (acts) { acts.hidden = !wbCenterIsChat; }
  if (typeof applyWorkbenchGrid === "function") { applyWorkbenchGrid(); }
  syncGlobalControlsWidth();
}

function setRightSidebarOpen(open) {
  wbLayout.rightOpen = Boolean(open);
  if (typeof inspectorOpen !== "undefined") { inspectorOpen = wbLayout.rightOpen; }
  applyWorkbenchGrid();
  if (typeof syncInspectorSidebar === "function") { syncInspectorSidebar(); }
}

function snapshotActiveCenterTab() {
  const cur = centerChatTabs.find(function (tb) { return tb.id === activeCenterTabId; });
  if (!cur) { return; }
  if (typeof queryEl !== "undefined" && queryEl) { cur.draft = queryEl.value || ""; }
  if (typeof activeAgentId !== "undefined" && activeAgentId) { cur.agentId = activeAgentId; }
}

function renderCenterChatTabs() {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) { return; }
  if (!centerChatTabs.length) { centerChatTabs = [{ id: "ct_" + (++wbTabSeq), chatId: "", title: "", agentId: "", draft: "" }]; }
  activeCenterTabId = renderChatTabStrip("center-tablist", centerChatTabs, activeCenterTabId, "ct", activateCenterChatTab, closeCenterChatTab);
}

function syncCenterChatTab(chatId, title) {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) {
    notifyParentFrame({ type: "realm:chat-state", chatId: chatId || "", title: title || "", agentId: typeof activeAgentId !== "undefined" ? activeAgentId : "", refreshChats: Boolean(chatId) });
    return;
  }
  const cid = chatId || "";
  if (cid) {
    const existing = centerChatTabs.find(function (tb) { return tb.chatId === cid; });
    if (existing) {
      activeCenterTabId = existing.id;
      if (title) { existing.title = title; }
      renderCenterChatTabs();
      return;
    }
    const cur = centerChatTabs.find(function (tb) { return tb.id === activeCenterTabId; });
    if (cur && !cur.chatId) {
      cur.chatId = cid; cur.title = title || ""; cur.draft = "";
    } else {
      const id = "ct_" + (++wbTabSeq);
      centerChatTabs.push({ id: id, chatId: cid, title: title || "", agentId: typeof activeAgentId !== "undefined" ? activeAgentId : "", draft: "" });
      activeCenterTabId = id;
    }
  } else {
    const cur = centerChatTabs.find(function (tb) { return tb.id === activeCenterTabId; });
    if (cur && !cur.chatId) {
      renderCenterChatTabs();
      return;
    }
    const blank = centerChatTabs.find(function (tb) { return !tb.chatId; });
    if (blank) { activeCenterTabId = blank.id; }
    else {
      const id = "ct_" + (++wbTabSeq);
      centerChatTabs.push({ id: id, chatId: "", title: "", agentId: typeof defaultAgentId !== "undefined" ? defaultAgentId : "", draft: "" });
      activeCenterTabId = id;
    }
  }
  renderCenterChatTabs();
}

function activateCenterChatTab(tabId) {
  const tb = centerChatTabs.find(function (item) { return item.id === tabId; });
  if (!tb) { return; }
  if (tabId !== activeCenterTabId) { snapshotActiveCenterTab(); }
  activeCenterTabId = tb.id;
  if (typeof setActiveRailSection === "function") { setActiveRailSection("chat", false); }
  if (tb.chatId) {
    if (tb.chatId !== currentChatId && typeof openSavedChat === "function") { openSavedChat(tb.chatId); }
    else if (typeof setViewMode === "function") { setViewMode(Boolean(currentTurns && currentTurns.length)); }
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
  renderCenterChatTabs();
}

function closeCenterChatTab(tabId) {
  const wasActive = activeCenterTabId === tabId;
  centerChatTabs = centerChatTabs.filter(function (tb) { return tb.id !== tabId; });
  if (!centerChatTabs.length) {
    centerChatTabs = [{ id: "ct_" + (++wbTabSeq), chatId: "", title: "", agentId: "", draft: "" }];
  }
  if (wasActive) { activateCenterChatTab(centerChatTabs[centerChatTabs.length - 1].id); }
  else { renderCenterChatTabs(); }
}

function resetCenterChatTabsOnAreaChange() {
  centerChatTabs = [{ id: "ct_" + (++wbTabSeq), chatId: "", title: "", agentId: "", draft: "" }];
  activeCenterTabId = centerChatTabs[0].id;
  renderCenterChatTabs();
}

function bindWorkbenchTabsUX() {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) { return; }
  const addBtn = document.getElementById("center-add-tab-btn");
  if (addBtn) {
    addBtn.addEventListener("click", function () {
      snapshotActiveCenterTab();
      const id = "ct_" + (++wbTabSeq);
      centerChatTabs.push({ id: id, chatId: "", title: "", agentId: typeof defaultAgentId !== "undefined" ? defaultAgentId : "", draft: "" });
      activeCenterTabId = id;
      if (typeof setActiveRailSection === "function") { setActiveRailSection("chat", false); }
      if (typeof resetHome === "function") { resetHome(); }
      renderCenterChatTabs();
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
