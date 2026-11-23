"""Copilot Extras: Highlight-to-Copilot pill, #file autocomplete & chips, localStorage persistence & Universal Undo."""

COPILOT_EXTRAS_SCRIPT: str = r"""
let cpSelection = null;
let cpAttachedFiles = [];
let cpFileMenuMatches = [], cpFileMenuIdx = 0, cpFileMenuOpen = false, cpFileTokenStart = -1;
let cpPendingSel = null;
let cpPersistedAreaKey = "";

function cpStorageKey() {
  const dirs = typeof selectedAreas === "function" ? selectedAreas() : [];
  const scope = dirs.length ? dirs.slice().sort().join(",") : ((typeof activeKnowledgeArea !== "undefined" && activeKnowledgeArea) || "global");
  return "realm_cp_threads::" + scope;
}

function cpEnsureThreadsLoaded() {
  const key = cpStorageKey();
  if (key === cpPersistedAreaKey) { return; }
  cpPersistedAreaKey = key;
  if (typeof cpThreads !== "undefined") { cpThreads.clear(); }
  try {
    const raw = safeStorageGet(key);
    if (!raw) { return; }
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object" && typeof cpThreads !== "undefined") {
      Object.entries(parsed).slice(0, 12).forEach(function ([ctxKey, list]) {
        if (Array.isArray(list)) { cpThreads.set(ctxKey, list.slice(-16)); }
      });
    }
  } catch (_e) {}
}

function cpSavePersistedThreads() {
  if (typeof cpThreads === "undefined") { return; }
  const key = cpStorageKey();
  cpPersistedAreaKey = key;
  try {
    const entries = [];
    cpThreads.forEach(function (list, ctxKey) {
      if (!Array.isArray(list) || !list.length) { return; }
      const clean = list.slice(-16).map(function (m) {
        if (m.role === "user") { return { role: "user", content: String(m.content || "").slice(0, 6000) }; }
        const acts = Array.isArray(m.actions) ? m.actions.map(function (a) {
          const copy = Object.assign({}, a);
          if (copy.status === "applying") { copy.status = "pending"; }
          if (typeof copy.prevContent === "string" && copy.prevContent.length > 16000) { delete copy.prevContent; }
          return copy;
        }) : [];
        return { role: "assistant", content: String(m.content || "").slice(0, 8000), streaming: false, actions: acts, error: m.error || "", meta: m.meta || null };
      });
      entries.push([ctxKey, clean]);
    });
    const obj = {};
    entries.slice(-12).forEach(function ([k, v]) { obj[k] = v; });
    safeStorageSet(key, JSON.stringify(obj));
  } catch (_e) {}
}

function cpRenderChips() {
  const box = document.getElementById("cp-chips");
  if (!box) { return; }
  let html = "";
  if (cpSelection && cpSelection.text) {
    const preview = cpSelection.text.replace(/\s+/g, " ").slice(0, 34) + (cpSelection.text.length > 34 ? "…" : "");
    html += "<span class='cp-chip cp-chip-sel' title='" + escapeHtml(cpSelection.text.slice(0, 300)) + "'><span class='cp-chip-lbl'>✦ " + escapeHtml(t("cp_chip_sel_pfx")) + ": " + escapeHtml(preview) + "</span>"
      + "<button type='button' data-cp-rm-sel='1' aria-label='Remove selection' class='cp-chip-x'>✕</button></span>";
  }
  cpAttachedFiles.forEach(function (f) {
    html += "<span class='cp-chip' title='" + escapeHtml(f.docId) + "'><span class='cp-chip-lbl'>#" + escapeHtml(f.filename) + "</span>"
      + "<button type='button' data-cp-rm-file='" + escapeHtml(f.docId) + "' aria-label='Remove file reference' class='cp-chip-x'>✕</button></span>";
  });
  box.innerHTML = html;
  const rmSel = box.querySelector("[data-cp-rm-sel]");
  if (rmSel) { rmSel.addEventListener("click", function () { cpSelection = null; cpRenderChips(); }); }
  box.querySelectorAll("[data-cp-rm-file]").forEach(function (b) {
    b.addEventListener("click", function () {
      const id = b.getAttribute("data-cp-rm-file") || "";
      cpAttachedFiles = cpAttachedFiles.filter(function (x) { return x.docId !== id; });
      cpRenderChips();
    });
  });
}

function cpHideSelPill() {
  const pill = document.getElementById("cf-sel-pill");
  if (pill) { pill.hidden = true; }
  cpPendingSel = null;
}

function cpShowSelPillAt(x, y, selObj) {
  const pill = document.getElementById("cf-sel-pill");
  if (!pill || !selObj || !selObj.text) { cpHideSelPill(); return; }
  cpPendingSel = selObj;
  pill.hidden = false;
  const pw = pill.offsetWidth || 230, ph = pill.offsetHeight || 36, pad = 10;
  const left = Math.max(pad, Math.min(window.innerWidth - pw - pad, x - pw / 2));
  const top = y - ph - 10 >= pad ? (y - ph - 10) : Math.min(window.innerHeight - ph - pad, y + 14);
  pill.style.left = Math.round(left) + "px";
  pill.style.top = Math.round(top) + "px";
}

function cpInspectFileSelection(mouseEvt) {
  const fv = document.getElementById("center-file-view");
  const tab = typeof cpActiveFileTab === "function" ? cpActiveFileTab() : null;
  if (!fv || fv.hidden || !tab) { cpHideSelPill(); return; }
  const ta = document.getElementById("cf-editor-ta");
  if (ta && document.activeElement === ta) {
    const s = ta.selectionStart, e = ta.selectionEnd;
    if (typeof s === "number" && typeof e === "number" && e > s) {
      const txt = ta.value.slice(s, e).trim();
      if (txt.length >= 3) {
        const rect = ta.getBoundingClientRect();
        const x = mouseEvt && typeof mouseEvt.clientX === "number" ? mouseEvt.clientX : (rect.left + Math.min(260, rect.width / 2));
        const y = mouseEvt && typeof mouseEvt.clientY === "number" ? mouseEvt.clientY : (rect.top + 44);
        cpShowSelPillAt(x, y, { docId: tab.docId, filename: tab.filename || tab.title, text: txt.slice(0, 5800) });
        return;
      }
    }
    cpHideSelPill();
    return;
  }
  const sel = window.getSelection();
  if (!sel || sel.isCollapsed || !sel.rangeCount) { cpHideSelPill(); return; }
  const range = sel.getRangeAt(0);
  if (!fv.contains(range.commonAncestorContainer)) { cpHideSelPill(); return; }
  const txt = sel.toString().trim();
  if (txt.length < 3) { cpHideSelPill(); return; }
  const rect = range.getBoundingClientRect();
  if (!rect || (!rect.width && !rect.height)) { cpHideSelPill(); return; }
  cpShowSelPillAt(rect.left + rect.width / 2, rect.top, { docId: tab.docId, filename: tab.filename || tab.title, text: txt.slice(0, 5800) });
}

function cpCloseFileMenu() {
  const menu = document.getElementById("cp-file-menu");
  cpFileMenuOpen = false; cpFileMenuMatches = []; cpFileTokenStart = -1;
  if (menu) { menu.hidden = true; menu.replaceChildren(); }
}

function cpPickFileMenu(idx) {
  const item = cpFileMenuMatches[idx], inp = document.getElementById("cp-input");
  if (!item || !inp) { cpCloseFileMenu(); return; }
  const caret = typeof inp.selectionStart === "number" ? inp.selectionStart : inp.value.length;
  if (cpFileTokenStart >= 0 && caret >= cpFileTokenStart) {
    const before = inp.value.slice(0, cpFileTokenStart), after = inp.value.slice(caret);
    inp.value = before + after.replace(/^\s+/, "");
    inp.selectionStart = inp.selectionEnd = before.length;
  }
  if (!cpAttachedFiles.some(function (x) { return x.docId === item.docId; })) {
    if (cpAttachedFiles.length >= 4) { cpAttachedFiles.shift(); }
    cpAttachedFiles.push({ docId: item.docId, filename: item.filename });
  }
  cpCloseFileMenu();
  cpRenderChips();
  inp.focus();
}

function cpUpdateFileMenu() {
  const inp = document.getElementById("cp-input"), menu = document.getElementById("cp-file-menu");
  if (!inp || !menu) { return; }
  const caret = typeof inp.selectionStart === "number" ? inp.selectionStart : inp.value.length;
  const match = inp.value.slice(0, caret).match(/(^|\s)#([^\s#]*)$/);
  if (!match) { cpCloseFileMenu(); return; }
  cpFileTokenStart = caret - match[2].length - 1;
  const q = match[2].toLowerCase();
  const guides = typeof allGuides !== "undefined" && Array.isArray(allGuides) ? allGuides : [];
  const attached = new Set(cpAttachedFiles.map(function (x) { return x.docId; }));
  const scored = [];
  guides.forEach(function (g) {
    if (attached.has(g.doc_id)) { return; }
    const fn = typeof ftFileNameOf === "function" ? ftFileNameOf(g) : (g.title || g.doc_id);
    const hay = (fn + " " + (g.subfolder || "") + " " + (g.title || "")).toLowerCase();
    const sc = !q ? 1 : (fn.toLowerCase().startsWith(q) ? 80 : (hay.includes(q) ? 40 : 0));
    if (sc > 0) { scored.push({ docId: g.doc_id, filename: fn, sub: g.subfolder || "", sc: sc }); }
  });
  scored.sort(function (a, b) { return b.sc - a.sc || a.filename.localeCompare(b.filename); });
  cpFileMenuMatches = scored.slice(0, 8);
  if (!cpFileMenuMatches.length) { cpCloseFileMenu(); return; }
  cpFileMenuIdx = Math.min(cpFileMenuIdx, cpFileMenuMatches.length - 1);
  menu.innerHTML = cpFileMenuMatches.map(function (m, idx) {
    return "<button type='button' role='option' data-cp-fidx='" + idx + "' class='cp-file-opt" + (idx === cpFileMenuIdx ? " is-active" : "") + "'>"
      + "<span class='cp-file-opt-name'>#" + escapeHtml(m.filename) + "</span>"
      + (m.sub ? ("<span class='cp-file-opt-sub'>" + escapeHtml(m.sub) + "</span>") : "") + "</button>";
  }).join("");
  menu.hidden = false; cpFileMenuOpen = true;
  menu.querySelectorAll("[data-cp-fidx]").forEach(function (b) {
    b.addEventListener("mouseenter", function () { cpFileMenuIdx = Number(b.getAttribute("data-cp-fidx") || 0); menu.querySelectorAll("[data-cp-fidx]").forEach(function (x, i) { x.classList.toggle("is-active", i === cpFileMenuIdx); }); });
    b.addEventListener("mousedown", function (e) { e.preventDefault(); cpPickFileMenu(Number(b.getAttribute("data-cp-fidx") || 0)); });
  });
}

function cpHandleFileMenuKeydown(e) {
  if (!cpFileMenuOpen || !cpFileMenuMatches.length) { return false; }
  if (e.key === "ArrowDown") { e.preventDefault(); cpFileMenuIdx = (cpFileMenuIdx + 1) % cpFileMenuMatches.length; cpUpdateFileMenu(); return true; }
  if (e.key === "ArrowUp") { e.preventDefault(); cpFileMenuIdx = (cpFileMenuIdx - 1 + cpFileMenuMatches.length) % cpFileMenuMatches.length; cpUpdateFileMenu(); return true; }
  if (e.key === "Enter" || e.key === "Tab") { e.preventDefault(); cpPickFileMenu(cpFileMenuIdx); return true; }
  if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); cpCloseFileMenu(); return true; }
  return false;
}

async function cpBuildSendContext() {
  const ctx = typeof cpCollectContext === "function" ? cpCollectContext() : { view: "chat" };
  ctx.selected_text = cpSelection && cpSelection.text ? String(cpSelection.text).slice(0, 5800) : "";
  const extra = [];
  for (const ref of cpAttachedFiles.slice(0, 4)) {
    let text = "";
    const openTab = typeof centerChatTabs !== "undefined" ? centerChatTabs.find(function (tb) { return tb.kind === "file" && tb.docId === ref.docId && tb.rawContent !== null; }) : null;
    if (openTab) { text = String(openTab.rawContent || ""); }
    else {
      try {
        const enc = typeof ftEncodeDocPath === "function" ? ftEncodeDocPath(ref.docId) : encodeURIComponent(ref.docId);
        const res = await areaFetch("/api/guides/" + enc + "/raw");
        if (res.ok) { const d = await safeJson(res); text = String((d && d.raw_markdown) || ""); }
      } catch (_e) {}
      if (!text && typeof allGuides !== "undefined" && Array.isArray(allGuides)) {
        const g = allGuides.find(function (x) { return x.doc_id === ref.docId; });
        if (g && Array.isArray(g.sections)) { text = g.sections.map(function (s) { return "## " + s.section_title + "\n" + (s.content || ""); }).join("\n\n"); }
      }
    }
    if (text.trim()) { extra.push({ doc_id: ref.docId, filename: ref.filename, content: text.slice(0, 11500) }); }
  }
  ctx.extra_files = extra;
  cpSelection = null;
  cpRenderChips();
  return ctx;
}

function cpCanUndoAction(act) {
  if (!act || act.status !== "applied") { return false; }
  if (act.kind === "update_document" && act.prevContent !== undefined) { return true; }
  return Boolean(act.undoMeta && act.undoMeta.endpoint);
}

async function cpUndoAnyAction(mIdx, aIdx) {
  const m = typeof cpGetThread === "function" ? cpGetThread()[mIdx] : null;
  const act = m && m.actions && m.actions[aIdx];
  if (!act || !cpCanUndoAction(act)) { return; }
  try {
    if (act.kind === "update_document") {
      const docId = String((act.payload && act.payload.doc_id) || "");
      const enc = typeof ftEncodeDocPath === "function" ? ftEncodeDocPath(docId) : encodeURIComponent(docId);
      await cpSyncDocUi(docId, act.prevContent, await cpJsonReq("/api/guides/" + enc + "/raw", "PUT", { content: act.prevContent }, true));
    } else if (act.undoMeta && act.undoMeta.endpoint) {
      const fn = act.undoMeta.areaScoped ? areaFetch : fetch;
      const res = await fn(act.undoMeta.endpoint, { method: "DELETE" });
      if (!res.ok) { const e = await safeJson(res); throw new Error((e && e.detail) || "Undo failed."); }
      const kind = act.undoMeta.kind;
      if (kind === "create_note") {
        const tab = typeof centerChatTabs !== "undefined" ? centerChatTabs.find(function (tb) { return tb.kind === "file" && tb.docId === act.undoMeta.docId; }) : null;
        if (tab) { tab.dirty = false; if (typeof closeCenterChatTab === "function") { closeCenterChatTab(tab.id, true); } }
        if (typeof loadWorkspace === "function") { await loadWorkspace(); }
        if (typeof loadGuidesCatalog === "function") { await loadGuidesCatalog(null); }
        if (typeof renderWorkspaceFilesTree === "function") { renderWorkspaceFilesTree(); }
      } else if (kind === "create_task" || kind === "create_event") {
        if (typeof cpSyncWorkUi === "function") { await cpSyncWorkUi(); }
      } else if (kind === "create_goal") {
        if (typeof loadFocusSummary === "function") { await loadFocusSummary(); }
        if (typeof focViewOpen !== "undefined" && focViewOpen && typeof renderFocusView === "function") { renderFocusView(); }
      } else if (kind === "upsert_workflow") {
        if (typeof loadWorkflowsSummary === "function") { await loadWorkflowsSummary(); }
        if (typeof wfViewOpen !== "undefined" && wfViewOpen && typeof renderWorkflowsView === "function") { renderWorkflowsView(); }
      } else if (kind === "upsert_agent") {
        if (typeof loadAgentTeam === "function") { await loadAgentTeam(); }
      }
    }
    act.status = "pending";
    delete act.undoMeta;
    cpSavePersistedThreads();
    if (typeof showToast === "function") { showToast(t("cp_undo") + " ✓", 2200); }
    if (typeof renderCopilotThread === "function") { renderCopilotThread(); }
  } catch (err) {
    if (typeof showToast === "function") { showToast((err && err.message) || "Undo failed.", 3200); }
  }
}

function bindCopilotExtrasUX() {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) { return; }
  const fv = document.getElementById("center-file-view");
  if (fv) {
    fv.addEventListener("mouseup", function (e) { setTimeout(function () { cpInspectFileSelection(e); }, 10); });
    fv.addEventListener("keyup", function () { cpInspectFileSelection(null); });
    fv.addEventListener("scroll", cpHideSelPill, true);
  }
  const askBtn = document.getElementById("cf-sel-ask-btn"), editBtn = document.getElementById("cf-sel-edit-btn");
  const attachSel = function (prefill) {
    if (!cpPendingSel) { return; }
    cpSelection = Object.assign({}, cpPendingSel);
    cpHideSelPill();
    cpRenderChips();
    if (typeof openCopilotForCurrentContext === "function") { openCopilotForCurrentContext(); }
    const inp = document.getElementById("cp-input");
    if (inp && prefill && !inp.value.trim()) { inp.value = prefill; inp.focus(); inp.selectionStart = inp.selectionEnd = inp.value.length; }
  };
  if (askBtn) { askBtn.addEventListener("mousedown", function (e) { e.preventDefault(); attachSel(""); }); }
  if (editBtn) { editBtn.addEventListener("mousedown", function (e) { e.preventDefault(); attachSel(t("cp_sel_edit_prefill")); }); }
  document.addEventListener("mousedown", function (e) {
    const pill = document.getElementById("cf-sel-pill");
    if (pill && !pill.hidden && !pill.contains(e.target) && !(fv && fv.contains(e.target))) { cpHideSelPill(); }
    const menu = document.getElementById("cp-file-menu"), inp = document.getElementById("cp-input");
    if (cpFileMenuOpen && menu && !menu.contains(e.target) && e.target !== inp) { cpCloseFileMenu(); }
  });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") { cpHideSelPill(); } });
  const inp = document.getElementById("cp-input");
  if (inp) { inp.addEventListener("input", cpUpdateFileMenu); }
}
"""
