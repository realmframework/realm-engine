"""IDE Actions: Tab Context Menu (Pin/Bulk Close), Folder Context Menu, Name Prompt Dialog, File Filter & Cmd+P Quick Open."""

IDE_ACTIONS_SCRIPT: str = r"""
let tcmTabId = "";
let ftMenuFolderKey = "";
let idePinnedScopeRestored = "";

function idePinnedStorageKey() {
  const dirs = typeof selectedAreas === "function" ? selectedAreas() : [];
  const scope = dirs.length ? dirs.slice().sort().join(",") : ((typeof activeKnowledgeArea !== "undefined" && activeKnowledgeArea) || "global");
  return "realm_pinned_tabs::" + scope;
}

function ideSavePinnedTabs() {
  if (typeof centerChatTabs === "undefined") { return; }
  const pinnedIds = centerChatTabs.filter(function (tb) { return tb.kind === "file" && tb.pinned && tb.docId; }).map(function (tb) { return tb.docId; }).slice(0, 8);
  safeStorageSet(idePinnedStorageKey(), JSON.stringify(pinnedIds));
}

function ideRestorePinnedTabs() {
  const key = idePinnedStorageKey();
  if (key === idePinnedScopeRestored || typeof allGuides === "undefined" || !Array.isArray(allGuides) || !allGuides.length || typeof centerChatTabs === "undefined") { return; }
  idePinnedScopeRestored = key;
  try {
    const raw = safeStorageGet(key);
    const ids = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(ids) || !ids.length) { return; }
    let added = false;
    ids.forEach(function (docId) {
      if (centerChatTabs.some(function (tb) { return tb.kind === "file" && tb.docId === docId; })) { return; }
      const g = allGuides.find(function (x) { return x.doc_id === docId; });
      if (!g) { return; }
      const fn = ftFileNameOf(g), ext = ftExtOf(fn), cl = ftCodeLabelFor(fn), isCode = Boolean(cl);
      const areaObj = (typeof knowledgeAreas !== "undefined" ? knowledgeAreas : []).find(function (a) { return a.name === (g.area || activeKnowledgeArea); });
      centerChatTabs.unshift({ id: "ft_" + (++wbTabSeq), kind: "file", docId: docId, title: fn, filename: fn, breadcrumb: ftBuildBreadcrumb(g, fn), editable: ext === ".md" || isCode, isCode: isCode, codeLang: cl, readOnly: !(ext === ".md" || isCode) || Boolean(areaObj && areaObj.linked), mdMode: isCode ? "raw" : "preview", rawContent: null, dirty: false, preview: false, pinned: true, loading: false, error: "" });
      added = true;
    });
    if (added && typeof renderCenterChatTabs === "function") { renderCenterChatTabs(); }
  } catch (_e) {}
}

async function createAnyFileInFolder(subfolder, area) {
  const fname = await promptNameDialog({ title: t("ft_new_file_t"), label: t("ft_new_file_lbl"), value: "", placeholder: "e.g. notes.md, script.py, config.yml", confirmLabel: t("ft_fld_create_btn"), selectAll: true });
  if (!fname) { return; }
  const cleanSub = String(subfolder || "").replace(/^\/+|\/+$/g, "");
  const exists = (typeof allGuides !== "undefined" && Array.isArray(allGuides)) && allGuides.some(function (g) {
    return String(g.subfolder || "") === cleanSub && ftFileNameOf(g).toLowerCase() === fname.toLowerCase();
  });
  if (exists) { if (typeof showToast === "function") { showToast(t("ft_new_file_exists"), 3000); } return; }
  const ext = ftExtOf(fname), starter = ext === ".json" ? "{\n}\n" : (ext === ".md" ? ("# " + fname.replace(/\.md$/i, "") + "\n\n") : ("// " + fname + "\n"));
  const body = { filename: fname, subfolder: cleanSub, content: ext === ".py" || ext === ".yml" || ext === ".yaml" || ext === ".sh" ? ("# " + fname + "\n") : starter, anonymize: false };
  if (area) { body.save_area = area; }
  try {
    const res = await areaFetch("/api/upload", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const data = await safeJson(res);
    if (!res.ok) { throw new Error((data && data.detail) || "Could not create file."); }
    if (typeof applyWorkspacePayload === "function") { applyWorkspacePayload(data); }
    if (typeof loadGuidesCatalog === "function") { await loadGuidesCatalog(null); }
    if (cleanSub) { ftExpanded.add(cleanSub); }
    renderWorkspaceFilesTree();
    const created = (allGuides || []).find(function (g) { return String(g.subfolder || "") === cleanSub && ftFileNameOf(g).toLowerCase() === fname.toLowerCase(); });
    if (created && typeof openFileInCenterTab === "function") { openFileInCenterTab(created.doc_id, { pin: true }); }
  } catch (err) { if (typeof showToast === "function") { showToast((err && err.message) || "Create file failed.", 3200); } }
}

function promptNameDialog(opts) {
  const modal = document.getElementById("name-prompt-modal");
  const titleEl = document.getElementById("np-title"), lblEl = document.getElementById("np-label");
  const inp = document.getElementById("np-input"), errEl = document.getElementById("np-error");
  const cancelBtn = document.getElementById("np-cancel-btn"), subBtn = document.getElementById("np-submit-btn");
  const form = document.getElementById("name-prompt-form");
  if (!modal || !inp || !form) { return Promise.resolve(null); }
  if (titleEl) { titleEl.textContent = (opts && opts.title) || "Rename"; }
  if (lblEl) { lblEl.textContent = (opts && opts.label) || "Name"; }
  if (subBtn) { subBtn.textContent = (opts && opts.confirmLabel) || t("save"); }
  if (errEl) { errEl.textContent = ""; }
  inp.value = (opts && opts.value) || "";
  inp.placeholder = (opts && opts.placeholder) || "";
  return new Promise(function (resolve) {
    let settled = false;
    const done = function (val) {
      if (settled) { return; }
      settled = true;
      form.removeEventListener("submit", onSubmit);
      if (cancelBtn) { cancelBtn.removeEventListener("click", onCancel); }
      modal.removeEventListener("close", onClose);
      if (modal.open) { modal.close(); }
      resolve(val);
    };
    const onSubmit = function (e) {
      e.preventDefault();
      const v = (inp.value || "").trim();
      if (!v) { if (errEl) { errEl.textContent = t("np_required_err"); } inp.focus(); return; }
      done(v);
    };
    const onCancel = function () { done(null); };
    const onClose = function () { done(null); };
    form.addEventListener("submit", onSubmit);
    if (cancelBtn) { cancelBtn.addEventListener("click", onCancel); }
    modal.addEventListener("close", onClose);
    modal.showModal();
    inp.focus();
    const dot = inp.value.lastIndexOf(".");
    if (dot > 0 && !(opts && opts.selectAll)) { inp.setSelectionRange(0, dot); } else { inp.select(); }
  });
}

function idePositionPopoverAt(pop, anchorEl, point) {
  try { if (pop.matches(":popover-open")) { pop.hidePopover(); } pop.showPopover(); } catch (_e) { return false; }
  if (point && typeof point.x === "number") {
    const pad = 8, pw = pop.offsetWidth || 210, ph = pop.offsetHeight || 200;
    pop.style.left = Math.round(Math.max(pad, Math.min(window.innerWidth - pw - pad, point.x))) + "px";
    pop.style.top = Math.round(Math.max(pad, Math.min(window.innerHeight - ph - pad, point.y))) + "px";
  } else if (anchorEl && typeof positionPopoverNearTrigger === "function") {
    positionPopoverNearTrigger(pop, anchorEl, { side: "right", align: "top" });
  }
  return true;
}

function openTabContextMenu(tabId, point) {
  const pop = document.getElementById("tab-context-menu");
  const tb = typeof centerChatTabs !== "undefined" ? centerChatTabs.find(function (x) { return x.id === tabId; }) : null;
  if (!pop || !tb) { return; }
  tcmTabId = tabId;
  const pinSpan = document.querySelector("#tcm-pin-btn span");
  if (pinSpan) { pinSpan.textContent = tb.pinned ? t("tcm_unpin") : t("tcm_pin"); }
  const closeBtn = document.getElementById("tcm-close-btn");
  if (closeBtn) { closeBtn.disabled = Boolean(tb.pinned) || centerChatTabs.length <= 1; }
  idePositionPopoverAt(pop, null, point);
}

function togglePinCenterTab(tabId) {
  const tb = typeof centerChatTabs !== "undefined" ? centerChatTabs.find(function (x) { return x.id === tabId; }) : null;
  if (!tb) { return; }
  tb.pinned = !tb.pinned;
  if (tb.pinned) { tb.preview = false; }
  centerChatTabs = centerChatTabs.filter(function (x) { return x.pinned; }).concat(centerChatTabs.filter(function (x) { return !x.pinned; }));
  ideSavePinnedTabs();
  if (typeof renderCenterChatTabs === "function") { renderCenterChatTabs(); }
}

async function runTabContextAction(act) {
  const pop = document.getElementById("tab-context-menu");
  if (pop && pop.matches && pop.matches(":popover-open") && pop.hidePopover) { try { pop.hidePopover(); } catch (_e) {} }
  const idx = typeof centerChatTabs !== "undefined" ? centerChatTabs.findIndex(function (x) { return x.id === tcmTabId; }) : -1;
  if (idx < 0) { return; }
  const tb = centerChatTabs[idx];
  if (act === "pin") { togglePinCenterTab(tb.id); return; }
  if (act === "close") {
    if (!tb.pinned && centerChatTabs.length > 1) { await closeCenterChatTab(tb.id); }
    return;
  }
  let targets = [];
  if (act === "close-others") { targets = centerChatTabs.filter(function (x) { return x.id !== tb.id && !x.pinned; }).map(function (x) { return x.id; }); }
  else if (act === "close-right") { targets = centerChatTabs.slice(idx + 1).filter(function (x) { return !x.pinned; }).map(function (x) { return x.id; }); }
  else if (act === "close-saved") { targets = centerChatTabs.filter(function (x) { return !x.pinned && !x.dirty; }).map(function (x) { return x.id; }); }
  else if (act === "close-all") { targets = centerChatTabs.filter(function (x) { return !x.pinned; }).map(function (x) { return x.id; }); }
  for (const tid of targets) {
    const ok = await closeCenterChatTab(tid);
    if (ok === false) { break; }
  }
}

function ftFolderMeta(folderKey) {
  const dirs = typeof selectedAreas === "function" ? selectedAreas() : [];
  const multi = dirs.length > 1;
  const parts = String(folderKey || "").split("/").filter(Boolean);
  const area = multi && parts.length ? parts[0] : (typeof activeKnowledgeArea !== "undefined" ? activeKnowledgeArea : (dirs[0] || ""));
  const relPath = multi ? parts.slice(1).join("/") : parts.join("/");
  const areaObj = (typeof knowledgeAreas !== "undefined" ? knowledgeAreas : []).find(function (a) { return a.name === area; });
  return { area: area, relPath: relPath, apiPath: folderKey, leaf: parts[parts.length - 1] || "", readOnly: Boolean(areaObj && areaObj.linked) };
}

function openFolderRowMenu(folderKey, anchorEl, point) {
  const pop = document.getElementById("ft-folder-menu");
  if (!pop || !folderKey) { return; }
  ftMenuFolderKey = folderKey;
  const meta = ftFolderMeta(folderKey);
  pop.querySelectorAll("[data-fm-writable]").forEach(function (el) { el.hidden = meta.readOnly; });
  idePositionPopoverAt(pop, anchorEl, point);
}

async function runFolderMenuAction(act) {
  const pop = document.getElementById("ft-folder-menu");
  if (pop && pop.matches && pop.matches(":popover-open") && pop.hidePopover) { try { pop.hidePopover(); } catch (_e) {} }
  if (!ftMenuFolderKey) { return; }
  const meta = ftFolderMeta(ftMenuFolderKey);
  if (act === "new-file") {
    await createAnyFileInFolder(meta.relPath, meta.area);
  } else if (act === "new-note") {
    if (typeof openSaveGuideModal === "function") {
      openSaveGuideModal({ isNew: true, title: "", content: "## Overview\n\n", tags: "notes", area: meta.area, subfolder: meta.relPath });
    }
  } else if (act === "copy-path") {
    try { await navigator.clipboard.writeText(meta.relPath || meta.apiPath); } catch (_e) {}
    if (typeof showToast === "function") { showToast(t("ft_copied_path", { path: meta.relPath || meta.apiPath }), 2200); }
  } else if (act === "new-subfolder") {
    const sub = await promptNameDialog({ title: t("ft_fld_new_sub_t"), label: t("ft_fld_name_lbl"), value: "", placeholder: "e.g. specs", confirmLabel: t("ft_fld_create_btn"), selectAll: true });
    if (!sub) { return; }
    try {
      const fullPath = meta.apiPath + "/" + sub;
      const res = await areaFetch("/api/subfolders", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: fullPath }) });
      const data = await safeJson(res);
      if (!res.ok) { throw new Error((data && data.detail) || "Could not create subfolder."); }
      if (typeof applySubfolders === "function") { applySubfolders(data); }
      ftExpanded.add(meta.apiPath);
      if (data.created) { ftExpanded.add(data.created); }
      renderWorkspaceFilesTree();
      if (typeof showToast === "function") { showToast(t("ft_fld_created_toast", { name: sub }), 2400); }
    } catch (err) { if (typeof showToast === "function") { showToast((err && err.message) || "Create folder failed.", 3200); } }
  } else if (act === "rename") {
    const next = await promptNameDialog({ title: t("ft_fld_rename_t"), label: t("ft_fld_name_lbl"), value: meta.leaf, confirmLabel: t("ft_act_rename_btn"), selectAll: true });
    if (!next || next === meta.leaf) { return; }
    try {
      const res = await areaFetch("/api/subfolders/rename", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path: meta.apiPath, new_name: next }) });
      const data = await safeJson(res);
      if (!res.ok) { throw new Error((data && data.detail) || "Rename folder failed."); }
      if (typeof applyWorkspacePayload === "function") { applyWorkspacePayload(data); }
      if (typeof loadGuidesCatalog === "function") { await loadGuidesCatalog(null); }
      const newPath = data.new_path || meta.apiPath;
      const oldRel = meta.relPath, newRel = selectedAreas().length > 1 ? newPath.split("/").slice(1).join("/") : newPath;
      if (typeof centerChatTabs !== "undefined" && oldRel && newRel && oldRel !== newRel) {
        const prefix = selectedAreas().length > 1 ? (meta.area + "::" + oldRel + "/") : (oldRel + "/");
        const nextPrefix = selectedAreas().length > 1 ? (meta.area + "::" + newRel + "/") : (newRel + "/");
        centerChatTabs.forEach(function (tb) {
          if (tb.kind === "file" && tb.docId && tb.docId.startsWith(prefix)) {
            tb.docId = nextPrefix + tb.docId.slice(prefix.length);
            const gNew = (allGuides || []).find(function (x) { return x.doc_id === tb.docId; });
            if (gNew) { tb.breadcrumb = ftBuildBreadcrumb(gNew, tb.filename); }
          }
        });
        if (typeof renderCenterChatTabs === "function") { renderCenterChatTabs(); }
        const actTab = centerChatTabs.find(function (x) { return x.id === activeCenterTabId; });
        if (actTab && actTab.kind === "file" && typeof renderCenterFileTab === "function") { renderCenterFileTab(actTab); }
      }
      ftExpanded.delete(meta.apiPath); ftExpanded.add(newPath);
      renderWorkspaceFilesTree();
      if (typeof showToast === "function") { showToast(t("ft_renamed_toast", { name: next }), 2400); }
    } catch (err) { if (typeof showToast === "function") { showToast((err && err.message) || "Rename folder failed.", 3200); } }
  } else if (act === "delete") {
    if (!await confirmDeletion(t("cf_del_sub_t"), t("cf_del_sub_m", { path: meta.relPath || meta.apiPath, files: "?", subfolders: "?" }))) { return; }
    try {
      const res = await areaFetch("/api/subfolders?path=" + encodeURIComponent(meta.apiPath), { method: "DELETE" }, meta.area);
      const data = await safeJson(res);
      if (!res.ok) { throw new Error((data && data.detail) || "Delete folder failed."); }
      if (typeof applyWorkspacePayload === "function") { applyWorkspacePayload(data); }
      if (typeof loadGuidesCatalog === "function") { await loadGuidesCatalog(null); }
      const delPfx = selectedAreas().length > 1 ? (meta.area + "::" + meta.relPath + "/") : (meta.relPath + "/");
      if (typeof centerChatTabs !== "undefined" && meta.relPath) {
        centerChatTabs.filter(function (tb) { return tb.kind === "file" && tb.docId && tb.docId.startsWith(delPfx); }).forEach(function (tb) { tb.dirty = false; closeCenterChatTab(tb.id, true); });
      }
      ftExpanded.delete(meta.apiPath);
      renderWorkspaceFilesTree();
      if (typeof showToast === "function") { showToast(t("ft_fld_deleted_toast"), 2400); }
    } catch (err) { if (typeof showToast === "function") { showToast((err && err.message) || "Delete folder failed.", 3200); } }
  }
}

function buildQuickFileItems() {
  const guides = typeof allGuides !== "undefined" && Array.isArray(allGuides) ? allGuides : [];
  return guides.slice(0, 500).map(function (g) {
    const fname = typeof ftFileNameOf === "function" ? ftFileNameOf(g) : (g.title || g.doc_id);
    const sub = [g.subfolder, g.title && g.title !== fname ? g.title : ""].filter(Boolean).join(" · ");
    return {
      group: "cmd_grp_files",
      id: "qfile-" + g.doc_id,
      label: fname,
      sub: sub,
      run: function () { if (typeof openFileInCenterTab === "function") { openFileInCenterTab(g.doc_id, { pin: true }); } },
    };
  });
}

function bindIdeActionsUX() {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) { return; }
  const tMenu = document.getElementById("tab-context-menu");
  if (tMenu) {
    tMenu.querySelectorAll("[data-tcm-act]").forEach(function (b) {
      b.addEventListener("click", function () { runTabContextAction(b.getAttribute("data-tcm-act") || ""); });
    });
  }
  const fldMenu = document.getElementById("ft-folder-menu");
  if (fldMenu) {
    fldMenu.querySelectorAll("[data-folder-act]").forEach(function (b) {
      b.addEventListener("click", function () { runFolderMenuAction(b.getAttribute("data-folder-act") || ""); });
    });
  }
  const newFileBtn = document.getElementById("ft-act-new-file");
  if (newFileBtn) {
    newFileBtn.addEventListener("click", function () {
      const p = document.getElementById("ft-options-menu");
      if (p && p.hidePopover) { try { p.hidePopover(); } catch (_e) {} }
      createAnyFileInFolder("", typeof activeKnowledgeArea !== "undefined" ? activeKnowledgeArea : "");
    });
  }
  const flt = document.getElementById("ft-filter-input"), clr = document.getElementById("ft-filter-clear");
  if (flt) {
    const syncFlt = function () {
      ftFilterQuery = flt.value || "";
      if (clr) { clr.hidden = !ftFilterQuery; }
      if (typeof renderWorkspaceFilesTree === "function") { renderWorkspaceFilesTree(); }
    };
    flt.addEventListener("input", syncFlt);
    flt.addEventListener("keydown", function (e) { if (e.key === "Escape" && flt.value) { e.stopPropagation(); flt.value = ""; syncFlt(); } });
    if (clr) { clr.addEventListener("click", function () { flt.value = ""; syncFlt(); flt.focus(); }); }
  }
  document.addEventListener("keydown", function (e) {
    if ((e.metaKey || e.ctrlKey) && !e.shiftKey && !e.altKey && e.key.toLowerCase() === "p") {
      e.preventDefault();
      const modal = document.getElementById("cmd-palette-modal");
      const otherOpen = document.querySelector("dialog[open]");
      if (otherOpen && otherOpen !== modal) { return; }
      if (typeof openCommandPalette === "function") { openCommandPalette("files"); }
    }
  });
}
"""
