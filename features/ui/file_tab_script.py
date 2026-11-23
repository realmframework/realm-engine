"""Workspace Files Tree (with live filter & folder actions) & Center File Tabs (3-Mode Markdown + Code Editor)."""

FILE_TAB_SCRIPT: str = r"""
const ftExpanded = new Set();
let ftAutoExpandedKey = "";
const FT_CHEV_SVG = "<svg class='ft-chev' aria-hidden='true' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='m9 6 6 6-6 6'/></svg>";
const FT_FOLDER_SVG = "<svg class='ft-icon' aria-hidden='true' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'><path d='M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z'/></svg>";
const FT_FILE_SVG = "<svg class='ft-icon' aria-hidden='true' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'><path d='M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8Z'/><path d='M14 3v5h5'/></svg>";

function ftStripFrontmatter(raw) {
  return String(raw || "").replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n*/, "");
}

function ftRenderNodeHtml(node, depth, activeDocId, filtering) {
  const folderList = Array.from(node.folders.values()).sort(function (a, b) { return a.name.localeCompare(b.name); });
  const fileList = node.files.slice().sort(function (a, b) { return a.filename.localeCompare(b.filename); });
  let html = "";
  folderList.forEach(function (f) {
    const open = filtering || ftExpanded.has(f.key);
    const isAreaRoot = depth === 0 && Boolean(f.color);
    const label = isAreaRoot && typeof areaTitle === "function" ? areaTitle(f.name) : f.name;
    const leadIcon = f.color
      ? "<span aria-hidden='true' class='w-2 h-2 rounded-full shrink-0' style='background:" + escapeHtml(f.color) + "'></span>"
      : FT_FOLDER_SVG;
    const moreBtn = isAreaRoot ? "" : "<button type='button' class='ft-row-more' data-ft-folder-menu='" + escapeHtml(f.key) + "' aria-label='Folder actions' title='Folder actions'>⋯</button>";
    html += "<div class='ft-row-wrap'><button type='button' class='ft-row ft-folder' data-ft-folder='" + escapeHtml(f.key) + "' data-ft-area-root='" + (isAreaRoot ? "1" : "0") + "' aria-expanded='" + String(open) + "' style='--ft-depth:" + depth + "'>"
      + FT_CHEV_SVG + leadIcon + "<span class='ft-row-name'>" + escapeHtml(label) + "</span></button>" + moreBtn + "</div>";
    if (open) { html += ftRenderNodeHtml(f, depth + 1, activeDocId, filtering); }
  });
  fileList.forEach(function (f) {
    const isAct = activeDocId && f.docId === activeDocId;
    const extTxt = f.ext ? f.ext.slice(1) : "";
    html += "<div class='ft-row-wrap'><button type='button' class='ft-row ft-file" + (isAct ? " is-active" : "") + "' data-ft-doc='" + escapeHtml(f.docId) + "' title='" + escapeHtml(f.title) + "' style='--ft-depth:" + depth + "'>"
      + FT_FILE_SVG + "<span class='ft-row-name'>" + escapeHtml(f.filename) + "</span>"
      + (extTxt ? ("<span class='ft-ext'>" + escapeHtml(extTxt) + "</span>") : "") + "</button>"
      + "<button type='button' class='ft-row-more' data-ft-menu='" + escapeHtml(f.docId) + "' aria-label='File actions' title='File actions'>⋯</button></div>";
  });
  return html;
}

function renderWorkspaceFilesTree() {
  const tree = document.getElementById("workspace-files-tree"), wsLbl = document.getElementById("files-tree-ws-title");
  if (!tree) { return; }
  const dirs = typeof selectedAreas === "function" ? selectedAreas() : [];
  const hasWs = dirs.length > 0 && typeof knowledgeAreas !== "undefined" && knowledgeAreas.length > 0;
  if (wsLbl) { wsLbl.textContent = t("sh_rail_files"); }
  if (!hasWs) {
    const areas = typeof knowledgeAreas !== "undefined" && Array.isArray(knowledgeAreas) ? knowledgeAreas : [];
    const pills = areas.map(function (a) {
      return "<button type='button' data-area='" + escapeHtml(a.name) + "' class='ft-row'><span aria-hidden='true' class='w-2 h-2 rounded-full shrink-0' style='background:" + escapeHtml(a.color) + "'></span><span class='ft-row-name'>" + escapeHtml(areaTitle(a)) + "</span><span class='ft-ext'>" + a.doc_count + "</span></button>";
    }).join("");
    tree.innerHTML = "<div class='p-3 flex flex-col gap-2 text-xs text-[#A0B0C8]'><p style='margin:0'>" + escapeHtml(t("no_ws_sel_d")) + "</p>" + pills + "</div>";
    if (typeof bindAreaButtons === "function") { bindAreaButtons(tree); }
    return;
  }
  const selKey = dirs.join(",");
  if (selKey !== ftAutoExpandedKey) {
    ftAutoExpandedKey = selKey;
    if (dirs.length > 1) { dirs.forEach(function (d) { ftExpanded.add(d); }); }
  }
  const activeTab = typeof centerChatTabs !== "undefined" ? centerChatTabs.find(function (tb) { return tb.id === activeCenterTabId; }) : null;
  const fvEl = document.getElementById("center-file-view");
  const activeDocId = activeTab && activeTab.kind === "file" && fvEl && !fvEl.hidden ? activeTab.docId : "";
  const q = String(ftFilterQuery || "").trim().toLowerCase();
  const root = ftFilterNode(ftBuildTreeModel(), q);
  const markup = ftRenderNodeHtml(root, 0, activeDocId, Boolean(q));
  if (!markup) {
    tree.innerHTML = "<div class='p-4 text-xs text-[#738196] text-center'>" + escapeHtml(q ? t("ft_no_filter_matches") : t("ft_empty_ws")) + "</div>";
    return;
  }
  tree.innerHTML = markup;
  tree.querySelectorAll("[data-ft-folder]").forEach(function (btn) {
    const k = btn.getAttribute("data-ft-folder") || "";
    btn.addEventListener("click", function () {
      if (ftExpanded.has(k)) { ftExpanded.delete(k); } else { ftExpanded.add(k); }
      renderWorkspaceFilesTree();
    });
    if (btn.getAttribute("data-ft-area-root") !== "1") {
      btn.addEventListener("contextmenu", function (e) { e.preventDefault(); if (typeof openFolderRowMenu === "function") { openFolderRowMenu(k, btn, { x: e.clientX, y: e.clientY }); } });
    }
  });
  tree.querySelectorAll("[data-ft-folder-menu]").forEach(function (btn) {
    btn.addEventListener("click", function (e) { e.stopPropagation(); if (typeof openFolderRowMenu === "function") { openFolderRowMenu(btn.getAttribute("data-ft-folder-menu") || "", btn); } });
  });
  tree.querySelectorAll("[data-ft-doc]").forEach(function (btn) {
    const did = btn.getAttribute("data-ft-doc") || "";
    btn.addEventListener("click", function () { openFileInCenterTab(did, { pin: false }); });
    btn.addEventListener("dblclick", function () { openFileInCenterTab(did, { pin: true }); });
    btn.addEventListener("contextmenu", function (e) { e.preventDefault(); if (typeof openFileRowMenu === "function") { openFileRowMenu(did, btn, { x: e.clientX, y: e.clientY }); } });
  });
  tree.querySelectorAll("[data-ft-menu]").forEach(function (btn) {
    btn.addEventListener("click", function (e) { e.stopPropagation(); if (typeof openFileRowMenu === "function") { openFileRowMenu(btn.getAttribute("data-ft-menu") || "", btn); } });
  });
}

function ftBuildBreadcrumb(guide, filename) {
  const parts = [];
  if (guide && guide.area && typeof areaTitle === "function") { parts.push(areaTitle(guide.area)); }
  else if (typeof activeKnowledgeArea !== "undefined" && activeKnowledgeArea && typeof areaTitle === "function") { parts.push(areaTitle(activeKnowledgeArea)); }
  const sub = String((guide && guide.subfolder) || "").replace(/^\/+|\/+$/g, "");
  if (sub) { sub.split("/").filter(Boolean).forEach(function (s) { parts.push(s); }); }
  parts.push(filename);
  return parts.join(" › ");
}

async function openFileInCenterTab(docId, opts) {
  if (!docId || typeof centerChatTabs === "undefined") { return; }
  const pin = Boolean((opts && opts.pin) || (typeof ftPrefs === "undefined" || ftPrefs.alwaysNewTab));
  const existing = centerChatTabs.find(function (tb) { return tb.kind === "file" && tb.docId === docId; });
  if (existing) {
    if (pin && existing.preview) { existing.preview = false; }
    activateCenterChatTab(existing.id);
    return;
  }
  const guide = (typeof allGuides !== "undefined" && Array.isArray(allGuides)) ? allGuides.find(function (g) { return g.doc_id === docId; }) : null;
  if (!guide) { return; }
  const filename = ftFileNameOf(guide), ext = ftExtOf(filename), codeLang = ftCodeLabelFor(filename);
  const isCode = Boolean(codeLang);
  const editable = ext === ".md" || isCode;
  const areaObj = (typeof knowledgeAreas !== "undefined" ? knowledgeAreas : []).find(function (a) { return a.name === (guide.area || activeKnowledgeArea); });
  const reuse = !pin ? centerChatTabs.find(function (tb) { return tb.kind === "file" && tb.preview && !tb.dirty && !tb.pinned; }) : null;
  const tab = reuse || { id: "ft_" + (++wbTabSeq), kind: "file" };
  Object.assign(tab, {
    docId: docId, title: filename, filename: filename, breadcrumb: ftBuildBreadcrumb(guide, filename),
    editable: editable, isCode: isCode, codeLang: codeLang,
    readOnly: !editable || Boolean(areaObj && areaObj.linked),
    mdMode: isCode ? "raw" : "preview", rawContent: null, dirty: false, preview: !pin, loading: false, error: "",
  });
  if (typeof snapshotActiveCenterTab === "function") { snapshotActiveCenterTab(); }
  if (!reuse) { centerChatTabs.push(tab); }
  activateCenterChatTab(tab.id);
}

function ftEncodeDocPath(docId) {
  return String(docId || "").split("/").map(encodeURIComponent).join("/");
}

async function loadFileTabRaw(tab) {
  if (!tab || !tab.editable || tab.rawContent !== null) { return; }
  const ver = areaVersion;
  tab.loading = true; tab.error = "";
  renderCenterFileTab(tab);
  try {
    const res = await areaFetch("/api/guides/" + ftEncodeDocPath(tab.docId) + "/raw");
    const data = await safeJson(res);
    if (ver !== areaVersion) { return; }
    if (!res.ok) { throw new Error((data && data.detail) || t("md_load_err")); }
    tab.rawContent = String(data.raw_markdown || "");
    if (data.filename) { tab.filename = data.filename; tab.title = data.filename; }
    if (data.language && !tab.codeLang) { tab.codeLang = String(data.language).toUpperCase(); tab.isCode = true; }
    tab.loading = false;
  } catch (err) {
    tab.loading = false; tab.error = (err && err.message) || t("md_load_err");
  }
  if (activeCenterTabId === tab.id) { renderCenterFileTab(tab); }
  if (typeof renderCenterChatTabs === "function") { renderCenterChatTabs(); }
}

async function saveCenterFileTab(tab) {
  if (!tab || !tab.editable || tab.readOnly || tab.saving || tab.rawContent === null) { return; }
  const ver = areaVersion;
  tab.saving = true;
  const saveBtn = document.getElementById("cf-save-btn"), st = document.getElementById("cf-status");
  if (saveBtn) { saveBtn.disabled = true; }
  if (st) { st.textContent = t("sg_saving"); }
  try {
    const res = await areaFetch("/api/guides/" + ftEncodeDocPath(tab.docId) + "/raw", {
      method: "PUT", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: tab.rawContent }),
    });
    const saved = await safeJson(res);
    if (ver !== areaVersion) { return; }
    if (!res.ok) { throw new Error((saved && saved.detail) || "Could not save file."); }
    tab.dirty = false;
    if (typeof applyWorkspacePayload === "function") { applyWorkspacePayload(saved); }
    if (typeof loadGuidesCatalog === "function") { await loadGuidesCatalog(null); }
    if (typeof showToast === "function") { showToast(t("ed_saved_toast"), 2800); }
    if (typeof renderCenterChatTabs === "function") { renderCenterChatTabs(); }
    if (activeCenterTabId === tab.id) { renderCenterFileTab(tab); }
  } catch (err) {
    if (st && ver === areaVersion) { st.textContent = (err && err.message) || "Save failed."; }
    if (saveBtn) { saveBtn.disabled = false; }
  } finally { tab.saving = false; }
}

function ftPreviewHtmlForTab(tab) {
  if (tab.editable && tab.rawContent !== null) { return formatMarkdown(ftStripFrontmatter(tab.rawContent)); }
  const guide = (typeof allGuides !== "undefined" && Array.isArray(allGuides)) ? allGuides.find(function (g) { return g.doc_id === tab.docId; }) : null;
  if (!guide) { return "<div class='wb-empty'>" + escapeHtml(t("md_load_err")) + "</div>"; }
  return "<h1 style='margin:0;font-size:calc(1.45rem * var(--ui-scale,1));font-weight:600'>" + escapeHtml(guide.title || tab.filename) + "</h1>"
    + (guide.sections || []).map(function (s) {
      return "<section style='padding:0.95rem 1.1rem;border-radius:0.85rem;background:var(--surface-raised);border:1px solid var(--border-subtle)'><h2 style='margin:0 0 0.5rem;font-size:calc(1.05rem * var(--ui-scale,1));font-weight:600'>" + escapeHtml(s.section_title) + "</h2><div class='md-body text-sm leading-relaxed flex flex-col gap-2'>" + formatMarkdown(s.content || "", false, 3) + "</div></section>";
    }).join("");
}

function ftSyncGutter(gutter, text) {
  if (!gutter) { return; }
  const count = Math.max(1, String(text || "").split("\n").length);
  if (Number(gutter.dataset.lines || 0) === count) { return; }
  gutter.dataset.lines = String(count);
  const nums = [];
  for (let i = 1; i <= count; i++) { nums.push(String(i)); }
  gutter.textContent = nums.join("\n");
}

function renderCenterFileTab(tab) {
  const box = document.getElementById("center-file-view"); if (!box || !tab) { return; }
  if (tab.editable && tab.rawContent === null && !tab.loading && !tab.error) { loadFileTabRaw(tab); return; }
  const isCode = Boolean(tab.isCode);
  const mode = isCode ? "raw" : (tab.editable ? (tab.mdMode || "preview") : "preview");
  const langBadge = isCode && tab.codeLang ? "<span class='cf-lang-badge'>" + escapeHtml(tab.codeLang) + "</span>" : "";
  const roBadge = tab.readOnly ? "<span class='wb-stat-pill'>" + escapeHtml(t("md_readonly_badge")) + "</span>" : "";
  const modeSeg = tab.editable && !isCode
    ? "<div class='cf-seg' role='group' aria-label='Markdown view mode'>"
      + "<button type='button' data-cf-mode='preview' aria-pressed='" + String(mode === "preview") + "'>" + escapeHtml(t("md_mode_preview")) + "</button>"
      + "<button type='button' data-cf-mode='raw' aria-pressed='" + String(mode === "raw") + "'>" + escapeHtml(t("md_mode_raw")) + "</button>"
      + "<button type='button' data-cf-mode='split' aria-pressed='" + String(mode === "split") + "'>" + escapeHtml(t("md_mode_split")) + "</button></div>"
    : "";
  const saveBtn = tab.editable && !tab.readOnly
    ? "<button id='cf-save-btn' type='button' class='wb-btn wb-btn-sm" + (tab.dirty ? " wb-btn-primary" : "") + "'" + (tab.dirty ? "" : " disabled") + ">" + escapeHtml(t("save")) + "</button>"
    : "";
  let bodyHtml = "";
  if (tab.loading) {
    bodyHtml = "<div class='cf-preview-pane'><div class='cf-preview-inner'><p class='text-sm text-[#A0B0C8]'>" + escapeHtml(t("graph_loading")) + "</p></div></div>";
  } else if (tab.error) {
    bodyHtml = "<div class='cf-preview-pane'><div class='cf-preview-inner'><div class='wb-empty'>" + escapeHtml(tab.error) + "</div></div></div>";
  } else if (isCode) {
    bodyHtml = "<div class='cf-code-wrap'><pre id='cf-code-gutter' class='cf-code-gutter' aria-hidden='true'>1</pre><textarea id='cf-editor-ta' class='cf-editor' spellcheck='false' wrap='off' aria-label='" + escapeHtml(tab.filename) + "'" + (tab.readOnly ? " readonly" : "") + "></textarea></div>";
  } else {
    const edPane = mode === "raw" || mode === "split"
      ? "<div class='cf-editor-pane'><textarea id='cf-editor-ta' class='cf-editor' spellcheck='false' aria-label='" + escapeHtml(tab.filename) + "'" + (tab.readOnly ? " readonly" : "") + "></textarea></div>" : "";
    const pvPane = mode === "preview" || mode === "split"
      ? "<div class='cf-preview-pane'><div id='cf-preview-inner' class='cf-preview-inner md-body md-prose'>" + ftPreviewHtmlForTab(tab) + "</div></div>" : "";
    bodyHtml = edPane + pvPane;
  }
  box.innerHTML = "<div class='cf-bar'><div class='cf-crumb' title='" + escapeHtml(tab.breadcrumb) + "'>" + FT_FILE_SVG + "<span>" + escapeHtml(tab.breadcrumb) + "</span>" + langBadge + roBadge + "</div>"
    + "<div class='cf-controls'><span id='cf-status' class='cf-status'></span>" + modeSeg + saveBtn
    + "<button id='cf-copilot-btn' type='button' class='wb-btn wb-btn-sm'>✦ " + escapeHtml(t("md_copilot_btn")) + "</button></div></div>"
    + "<div class='cf-body" + (mode === "split" ? " is-split" : "") + "'>" + bodyHtml + "</div>";
  box.querySelectorAll("[data-cf-mode]").forEach(function (b) {
    b.addEventListener("click", function () { tab.mdMode = b.getAttribute("data-cf-mode") || "preview"; renderCenterFileTab(tab); });
  });
  const ta = document.getElementById("cf-editor-ta"), gutter = document.getElementById("cf-code-gutter");
  if (ta) {
    ta.value = tab.rawContent || "";
    if (gutter) { ftSyncGutter(gutter, ta.value); ta.addEventListener("scroll", function () { gutter.scrollTop = ta.scrollTop; }); }
    ta.addEventListener("input", function () {
      tab.rawContent = ta.value;
      if (gutter) { ftSyncGutter(gutter, ta.value); }
      if (!tab.dirty && !tab.readOnly) { tab.dirty = true; tab.preview = false; const sb = document.getElementById("cf-save-btn"); if (sb) { sb.disabled = false; sb.classList.add("wb-btn-primary"); } if (typeof renderCenterChatTabs === "function") { renderCenterChatTabs(); } }
      const pv = document.getElementById("cf-preview-inner");
      if (pv) { pv.innerHTML = formatMarkdown(ftStripFrontmatter(tab.rawContent)); }
    });
    ta.addEventListener("keydown", function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") { e.preventDefault(); saveCenterFileTab(tab); }
      else if (e.key === "Tab" && !tab.readOnly) {
        e.preventDefault();
        const s = ta.selectionStart, end = ta.selectionEnd;
        ta.value = ta.value.slice(0, s) + "  " + ta.value.slice(end);
        ta.selectionStart = ta.selectionEnd = s + 2;
        ta.dispatchEvent(new Event("input"));
      }
    });
  }
  const sBtn = document.getElementById("cf-save-btn"), cBtn = document.getElementById("cf-copilot-btn");
  if (sBtn) { sBtn.addEventListener("click", function () { saveCenterFileTab(tab); }); }
  if (cBtn) { cBtn.addEventListener("click", function () { if (typeof openCopilotForCurrentContext === "function") { openCopilotForCurrentContext(); } }); }
  renderWorkspaceFilesTree();
  if (typeof syncCopilotContextUI === "function") { syncCopilotContextUI(); }
}

function bindFileTabUX() {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) { return; }
  const nBtn = document.getElementById("tree-new-note-btn"), rBtn = document.getElementById("tree-refresh-btn"), cBtn = document.getElementById("tree-collapse-btn");
  if (nBtn) { nBtn.addEventListener("click", function () { if (typeof openNewNoteModal === "function") { openNewNoteModal(); } }); }
  if (rBtn) { rBtn.addEventListener("click", async function () { const p = document.getElementById("ft-options-menu"); if (p && p.hidePopover) { try { p.hidePopover(); } catch (_e) {} } if (typeof loadGuidesCatalog === "function") { await loadGuidesCatalog(null); } renderWorkspaceFilesTree(); }); }
  if (cBtn) { cBtn.addEventListener("click", function () { ftExpanded.clear(); renderWorkspaceFilesTree(); }); }
  renderWorkspaceFilesTree();
}
"""
