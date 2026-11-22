"""VS Code-style Files Explorer Controls: Auto-Reveal, Preview vs New-Tab Mode, Expand/Collapse All & File Row Actions."""

FILE_EXPLORER_SCRIPT: str = r"""
const ftPrefs = {
  autoReveal: safeStorageGet("realm_ft_auto_reveal") !== "0",
  alwaysNewTab: safeStorageGet("realm_ft_always_new_tab") !== "0",
};
let ftMenuDocId = "";

function saveFtPrefs() {
  safeStorageSet("realm_ft_auto_reveal", ftPrefs.autoReveal ? "1" : "0");
  safeStorageSet("realm_ft_always_new_tab", ftPrefs.alwaysNewTab ? "1" : "0");
  syncFtOptionsUI();
}

function syncFtOptionsUI() {
  const rev = document.getElementById("ft-opt-reveal"), nt = document.getElementById("ft-opt-newtab");
  if (rev) { rev.setAttribute("aria-checked", String(ftPrefs.autoReveal)); }
  if (nt) { nt.setAttribute("aria-checked", String(ftPrefs.alwaysNewTab)); }
}

function ftCollectFolderKeys(node, out) {
  node.folders.forEach(function (f) { out.push(f.key); ftCollectFolderKeys(f, out); });
}

function ftExpandAllFolders() {
  if (typeof ftBuildTreeModel !== "function") { return; }
  const keys = [];
  ftCollectFolderKeys(ftBuildTreeModel(), keys);
  keys.forEach(function (k) { ftExpanded.add(k); });
  if (typeof renderWorkspaceFilesTree === "function") { renderWorkspaceFilesTree(); }
}

function ftRevealDocInTree(docId, forceScroll) {
  if (!docId || typeof allGuides === "undefined" || !Array.isArray(allGuides)) { return; }
  const guide = allGuides.find(function (g) { return g.doc_id === docId; });
  if (!guide) { return; }
  const dirs = typeof selectedAreas === "function" ? selectedAreas() : [];
  let prefix = "";
  if (dirs.length > 1 && guide.area) { ftExpanded.add(guide.area); prefix = guide.area; }
  const sub = String(guide.subfolder || "").replace(/^\/+|\/+$/g, "");
  if (sub) {
    sub.split("/").filter(Boolean).forEach(function (seg) {
      prefix = prefix ? (prefix + "/" + seg) : seg;
      ftExpanded.add(prefix);
    });
  }
  if (typeof renderWorkspaceFilesTree === "function") { renderWorkspaceFilesTree(); }
  if (forceScroll !== false) {
    const tree = document.getElementById("workspace-files-tree");
    const row = tree ? tree.querySelector("[data-ft-doc='" + CSS.escape(docId) + "']") : null;
    if (row && row.scrollIntoView) { row.scrollIntoView({ block: "nearest" }); }
  }
}

function ftRevealActiveFile() {
  const tb = typeof centerChatTabs !== "undefined" ? centerChatTabs.find(function (x) { return x.id === activeCenterTabId; }) : null;
  if (!tb || tb.kind !== "file") {
    if (typeof showToast === "function") { showToast(t("ft_no_active_file"), 2200); }
    return;
  }
  if (typeof setActiveRailSection === "function") { setActiveRailSection("files", true); }
  ftRevealDocInTree(tb.docId, true);
}

function ftIsDocReadOnly(guide) {
  const areaObj = (typeof knowledgeAreas !== "undefined" ? knowledgeAreas : []).find(function (a) {
    return a.name === ((guide && guide.area) || (typeof activeKnowledgeArea !== "undefined" ? activeKnowledgeArea : ""));
  });
  return Boolean(areaObj && areaObj.linked);
}

function openFileRowMenu(docId, anchorEl, point) {
  const pop = document.getElementById("ft-file-menu");
  const guide = (typeof allGuides !== "undefined" && Array.isArray(allGuides)) ? allGuides.find(function (g) { return g.doc_id === docId; }) : null;
  if (!pop || !guide) { return; }
  ftMenuDocId = docId;
  const ro = ftIsDocReadOnly(guide);
  pop.querySelectorAll("[data-fm-writable]").forEach(function (el) { el.hidden = ro; });
  try { if (pop.matches(":popover-open")) { pop.hidePopover(); } pop.showPopover(); } catch (_e) { return; }
  if (point && typeof point.x === "number") {
    const pad = 8, pw = pop.offsetWidth || 200, ph = pop.offsetHeight || 180;
    pop.style.left = Math.round(Math.max(pad, Math.min(window.innerWidth - pw - pad, point.x))) + "px";
    pop.style.top = Math.round(Math.max(pad, Math.min(window.innerHeight - ph - pad, point.y))) + "px";
  } else if (anchorEl && typeof positionPopoverNearTrigger === "function") {
    positionPopoverNearTrigger(pop, anchorEl, { side: "right", align: "top" });
  }
}

async function runFileMenuAction(act) {
  const pop = document.getElementById("ft-file-menu");
  if (pop && pop.matches && pop.matches(":popover-open") && pop.hidePopover) { try { pop.hidePopover(); } catch (_e) {} }
  const docId = ftMenuDocId;
  const guide = (typeof allGuides !== "undefined" && Array.isArray(allGuides)) ? allGuides.find(function (g) { return g.doc_id === docId; }) : null;
  if (!docId || !guide) { return; }
  if (act === "open-pin") {
    if (typeof openFileInCenterTab === "function") { openFileInCenterTab(docId, { pin: true }); }
  } else if (act === "copilot") {
    if (typeof openFileInCenterTab === "function") { await openFileInCenterTab(docId, { pin: true }); }
    if (typeof openCopilotForCurrentContext === "function") { openCopilotForCurrentContext(); }
  } else if (act === "move") {
    if (typeof openMoveModal === "function") { openMoveModal(guide, { tag: null }); }
  } else if (act === "copy-path") {
    const fname = typeof ftFileNameOf === "function" ? ftFileNameOf(guide) : docId;
    const rel = guide.subfolder ? (guide.subfolder + "/" + fname) : fname;
    try { await navigator.clipboard.writeText(rel); } catch (_e) {}
    if (typeof showToast === "function") { showToast(t("ft_copied_path", { path: rel }), 2200); }
  } else if (act === "anonymize") {
    try {
      const enc = typeof ftEncodeDocPath === "function" ? ftEncodeDocPath(docId) : encodeURIComponent(docId);
      const res = await areaFetch("/api/guides/" + enc + "/anonymize", { method: "POST" });
      if (!res.ok) { const e = await safeJson(res); throw new Error((e && e.detail) || "Anonymize failed."); }
      if (typeof loadGuidesCatalog === "function") { await loadGuidesCatalog(null); }
      const tab = typeof centerChatTabs !== "undefined" ? centerChatTabs.find(function (tb) { return tb.kind === "file" && tb.docId === docId; }) : null;
      if (tab) { tab.rawContent = null; tab.dirty = false; if (activeCenterTabId === tab.id && typeof renderCenterFileTab === "function") { renderCenterFileTab(tab); } }
      if (typeof showToast === "function") { showToast(t("ft_anon_done"), 2600); }
    } catch (err) { if (typeof showToast === "function") { showToast((err && err.message) || "Anonymize failed.", 3200); } }
  } else if (act === "delete") {
    const area = guide.area || (typeof activeKnowledgeArea !== "undefined" ? activeKnowledgeArea : "");
    if (!await confirmDeletion(t("cf_del_doc_t"), t("cf_del_doc_m", { title: guide.title || docId, area: typeof areaLabel === "function" ? areaLabel(area) : area }))) { return; }
    try {
      const enc = typeof ftEncodeDocPath === "function" ? ftEncodeDocPath(docId) : encodeURIComponent(docId);
      const res = await areaFetch("/api/guides/" + enc, { method: "DELETE" }, area);
      if (!res.ok) { const e = await safeJson(res); throw new Error((e && e.detail) || "Delete failed."); }
      const openTab = typeof centerChatTabs !== "undefined" ? centerChatTabs.find(function (tb) { return tb.kind === "file" && tb.docId === docId; }) : null;
      if (openTab) { openTab.dirty = false; if (typeof closeCenterChatTab === "function") { closeCenterChatTab(openTab.id, true); } }
      if (typeof loadWorkspace === "function") { await loadWorkspace(); }
      if (typeof loadGuidesCatalog === "function") { await loadGuidesCatalog(null); }
      if (typeof renderWorkspaceFilesTree === "function") { renderWorkspaceFilesTree(); }
      if (typeof showToast === "function") { showToast(t("st_doc_deleted"), 2400); }
    } catch (err) { if (typeof showToast === "function") { showToast((err && err.message) || "Delete failed.", 3200); } }
  }
}

function bindFileExplorerUX() {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) { return; }
  const expBtn = document.getElementById("tree-expand-btn");
  if (expBtn) { expBtn.addEventListener("click", ftExpandAllFolders); }
  const optRev = document.getElementById("ft-opt-reveal"), optNt = document.getElementById("ft-opt-newtab"), revNow = document.getElementById("ft-act-reveal-now");
  if (optRev) { optRev.addEventListener("click", function () { ftPrefs.autoReveal = !ftPrefs.autoReveal; saveFtPrefs(); if (ftPrefs.autoReveal) { ftRevealActiveFile(); } }); }
  if (optNt) { optNt.addEventListener("click", function () { ftPrefs.alwaysNewTab = !ftPrefs.alwaysNewTab; saveFtPrefs(); }); }
  if (revNow) { revNow.addEventListener("click", function () { const p = document.getElementById("ft-options-menu"); if (p && p.hidePopover) { try { p.hidePopover(); } catch (_e) {} } ftRevealActiveFile(); }); }
  if (typeof bindAnchoredPopover === "function") { bindAnchoredPopover("ft-options-menu", "tree-more-btn", { align: "right" }); }
  const fMenu = document.getElementById("ft-file-menu");
  if (fMenu) {
    fMenu.querySelectorAll("[data-fm-act]").forEach(function (b) {
      b.addEventListener("click", function () { runFileMenuAction(b.getAttribute("data-fm-act") || ""); });
    });
  }
  syncFtOptionsUI();
}
"""
