"""VS Code-style Files Explorer Controls: Auto-Reveal, Preview vs New-Tab Mode, Expand/Collapse All & File Row Actions."""

FILE_EXPLORER_SCRIPT: str = r"""
const ftPrefs = {
  autoReveal: safeStorageGet("realm_ft_auto_reveal") !== "0",
  alwaysNewTab: safeStorageGet("realm_ft_always_new_tab") !== "0",
};
let ftMenuDocId = "";
let ftFilterQuery = "";
const FT_CODE_LANGS = {
  ".py": "PYTHON", ".js": "JAVASCRIPT", ".mjs": "JAVASCRIPT", ".cjs": "JAVASCRIPT",
  ".ts": "TYPESCRIPT", ".tsx": "TSX", ".jsx": "JSX", ".json": "JSON", ".yaml": "YAML", ".yml": "YAML",
  ".toml": "TOML", ".ini": "INI", ".cfg": "INI", ".css": "CSS", ".scss": "SCSS", ".sql": "SQL",
  ".sh": "BASH", ".bash": "BASH", ".zsh": "BASH", ".xml": "XML", ".rs": "RUST", ".go": "GO",
  ".java": "JAVA", ".kt": "KOTLIN", ".c": "C", ".h": "C", ".cpp": "C++", ".hpp": "C++",
  ".cs": "C#", ".swift": "SWIFT", ".dart": "DART", ".rb": "RUBY", ".php": "PHP", ".r": "R",
  ".lua": "LUA", ".graphql": "GRAPHQL", ".proto": "PROTO", ".html": "HTML",
};

function ftFileNameOf(guide) {
  const fp = String((guide && guide.file_path) || "");
  if (fp) {
    const parts = fp.replace(/\\/g, "/").split("/");
    const base = parts[parts.length - 1];
    if (base) { return base; }
  }
  const raw = String((guide && guide.doc_id) || "note");
  const clean = raw.includes("::") ? raw.split("::").pop() : raw;
  const seg = clean.split("/").pop() || clean;
  return /\.[a-z0-9]{1,6}$/i.test(seg) ? seg : (seg + ".md");
}

function ftExtOf(filename) {
  const m = String(filename || "").match(/\.([a-z0-9]{1,6})$/i);
  return m ? ("." + m[1].toLowerCase()) : "";
}

function ftCodeLabelFor(filename) {
  const ext = ftExtOf(filename);
  return FT_CODE_LANGS[ext] || (ext === ".txt" ? "TEXT" : "");
}

function ftBuildTreeModel() {
  const dirs = typeof selectedAreas === "function" ? selectedAreas() : [];
  const guides = typeof allGuides !== "undefined" && Array.isArray(allGuides) ? allGuides : [];
  const multi = dirs.length > 1;
  const root = { key: "", name: "", folders: new Map(), files: [] };
  const ensureFolder = function (parent, seg, keyPrefix, color) {
    const k = keyPrefix ? (keyPrefix + "/" + seg) : seg;
    if (!parent.folders.has(seg)) {
      parent.folders.set(seg, { key: k, name: seg, color: color || "", folders: new Map(), files: [] });
    }
    return parent.folders.get(seg);
  };
  if (multi) {
    dirs.forEach(function (areaName) {
      const aObj = (typeof knowledgeAreas !== "undefined" ? knowledgeAreas : []).find(function (a) { return a.name === areaName; });
      ensureFolder(root, areaName, "", (aObj && aObj.color) || "#4BB8E8");
    });
  }
  if (typeof workspaceFolders !== "undefined" && Array.isArray(workspaceFolders)) {
    workspaceFolders.forEach(function (wf) {
      const rawPath = String((wf && wf.path) || "").replace(/^\/+|\/+$/g, "");
      if (!rawPath) { return; }
      let cur = root, prefix = "";
      rawPath.split("/").filter(Boolean).forEach(function (seg, idx) {
        const aObj = (multi && idx === 0) ? (typeof knowledgeAreas !== "undefined" ? knowledgeAreas : []).find(function (a) { return a.name === seg; }) : null;
        cur = ensureFolder(cur, seg, prefix, aObj ? (aObj.color || "#4BB8E8") : "");
        prefix = prefix ? (prefix + "/" + seg) : seg;
      });
    });
  }
  guides.forEach(function (g) {
    let cur = root, prefix = "";
    if (multi && g.area) {
      const aObj = (typeof knowledgeAreas !== "undefined" ? knowledgeAreas : []).find(function (a) { return a.name === g.area; });
      cur = ensureFolder(cur, g.area, "", (aObj && aObj.color) || "#4BB8E8");
      prefix = g.area;
    }
    const sub = String(g.subfolder || "").replace(/^\/+|\/+$/g, "");
    if (sub) {
      sub.split("/").filter(Boolean).forEach(function (seg) {
        cur = ensureFolder(cur, seg, prefix, "");
        prefix = prefix ? (prefix + "/" + seg) : seg;
      });
    }
    const fname = ftFileNameOf(g);
    cur.files.push({ docId: g.doc_id, filename: fname, ext: ftExtOf(fname), title: g.title || fname, guide: g });
  });
  return root;
}

function ftFilterNode(node, q) {
  if (!q) { return node; }
  const out = { key: node.key, name: node.name, color: node.color || "", folders: new Map(), files: [] };
  node.files.forEach(function (f) {
    if ((f.filename + " " + f.title + " " + node.key).toLowerCase().includes(q)) { out.files.push(f); }
  });
  node.folders.forEach(function (child, k) {
    const sub = ftFilterNode(child, q);
    if (sub.files.length || sub.folders.size || child.name.toLowerCase().includes(q)) { out.folders.set(k, sub); }
  });
  return out;
}

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
  } else if (act === "rename") {
    const curName = ftFileNameOf(guide);
    const next = typeof promptNameDialog === "function" ? await promptNameDialog({ title: t("ft_rename_file_t"), label: t("ft_rename_file_lbl"), value: curName, confirmLabel: t("ft_act_rename_btn") }) : null;
    if (!next || next === curName) { return; }
    try {
      const res = await areaFetch("/api/guides/" + ftEncodeDocPath(docId) + "/rename", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ new_name: next }) });
      const data = await safeJson(res);
      if (!res.ok) { throw new Error((data && data.detail) || "Rename failed."); }
      if (typeof applyWorkspacePayload === "function") { applyWorkspacePayload(data); }
      if (typeof loadGuidesCatalog === "function") { await loadGuidesCatalog(null); }
      const tab = typeof centerChatTabs !== "undefined" ? centerChatTabs.find(function (tb) { return tb.kind === "file" && tb.docId === docId; }) : null;
      if (tab && data.doc_id) {
        const gNew = (allGuides || []).find(function (x) { return x.doc_id === data.doc_id; });
        const fn = data.filename || (gNew ? ftFileNameOf(gNew) : next);
        const cl = ftCodeLabelFor(fn);
        Object.assign(tab, { docId: data.doc_id, filename: fn, title: fn, isCode: Boolean(cl), codeLang: cl, breadcrumb: gNew ? ftBuildBreadcrumb(gNew, fn) : fn });
        if (typeof renderCenterChatTabs === "function") { renderCenterChatTabs(); }
        if (activeCenterTabId === tab.id && typeof renderCenterFileTab === "function") { renderCenterFileTab(tab); }
      }
      renderWorkspaceFilesTree();
      if (typeof showToast === "function") { showToast(t("ft_renamed_toast", { name: data.filename || next }), 2400); }
    } catch (err) { if (typeof showToast === "function") { showToast((err && err.message) || "Rename failed.", 3200); } }
  } else if (act === "duplicate") {
    try {
      const res = await areaFetch("/api/guides/" + ftEncodeDocPath(docId) + "/duplicate", { method: "POST" });
      const data = await safeJson(res);
      if (!res.ok) { throw new Error((data && data.detail) || "Duplicate failed."); }
      if (typeof applyWorkspacePayload === "function") { applyWorkspacePayload(data); }
      if (typeof loadGuidesCatalog === "function") { await loadGuidesCatalog(null); }
      renderWorkspaceFilesTree();
      if (data.doc_id && typeof openFileInCenterTab === "function") { openFileInCenterTab(data.doc_id, { pin: true }); }
      if (typeof showToast === "function") { showToast(t("ft_dup_toast", { name: data.filename || "" }), 2400); }
    } catch (err) { if (typeof showToast === "function") { showToast((err && err.message) || "Duplicate failed.", 3200); } }
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
