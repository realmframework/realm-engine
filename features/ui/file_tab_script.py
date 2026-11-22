"""VS Code-style Right Sidebar Workspace File Tree & In-Tab 3-Mode Markdown Viewer/Editor (Preview / Raw / Side by Side)."""

FILE_TAB_SCRIPT: str = r"""
const ftExpanded = new Set();
let ftAutoExpandedKey = "";
const FT_CHEV_SVG = "<svg class='ft-chev' aria-hidden='true' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='m9 6 6 6-6 6'/></svg>";
const FT_FOLDER_SVG = "<svg class='ft-icon' aria-hidden='true' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'><path d='M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z'/></svg>";
const FT_FILE_SVG = "<svg class='ft-icon' aria-hidden='true' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'><path d='M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8Z'/><path d='M14 3v5h5'/></svg>";

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

function ftStripFrontmatter(raw) {
  return String(raw || "").replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n*/, "");
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

function ftRenderNodeHtml(node, depth, activeDocId) {
  const folderList = Array.from(node.folders.values()).sort(function (a, b) { return a.name.localeCompare(b.name); });
  const fileList = node.files.slice().sort(function (a, b) { return a.filename.localeCompare(b.filename); });
  let html = "";
  folderList.forEach(function (f) {
    const open = ftExpanded.has(f.key);
    const label = depth === 0 && f.color && typeof areaTitle === "function" ? areaTitle(f.name) : f.name;
    const leadIcon = f.color
      ? "<span aria-hidden='true' class='w-2 h-2 rounded-full shrink-0' style='background:" + escapeHtml(f.color) + "'></span>"
      : FT_FOLDER_SVG;
    html += "<button type='button' class='ft-row ft-folder' data-ft-folder='" + escapeHtml(f.key) + "' aria-expanded='" + String(open) + "' style='--ft-depth:" + depth + "'>"
      + FT_CHEV_SVG + leadIcon + "<span class='ft-row-name'>" + escapeHtml(label) + "</span></button>";
    if (open) { html += ftRenderNodeHtml(f, depth + 1, activeDocId); }
  });
  fileList.forEach(function (f) {
    const isAct = activeDocId && f.docId === activeDocId;
    const extTxt = f.ext ? f.ext.slice(1) : "";
    html += "<button type='button' class='ft-row ft-file" + (isAct ? " is-active" : "") + "' data-ft-doc='" + escapeHtml(f.docId) + "' title='" + escapeHtml(f.title) + "' style='--ft-depth:" + depth + "'>"
      + FT_FILE_SVG + "<span class='ft-row-name'>" + escapeHtml(f.filename) + "</span>"
      + (extTxt ? ("<span class='ft-ext'>" + escapeHtml(extTxt) + "</span>") : "") + "</button>";
  });
  return html;
}

function renderRightFilesTree() {
  const tree = document.getElementById("right-files-tree"), wsLbl = document.getElementById("right-files-ws-title");
  if (!tree) { return; }
  const dirs = typeof selectedAreas === "function" ? selectedAreas() : [];
  const hasWs = dirs.length > 0 && typeof knowledgeAreas !== "undefined" && knowledgeAreas.length > 0;
  if (wsLbl) {
    wsLbl.textContent = !hasWs ? t("no_ws_short") : (dirs.length > 1 ? t("areas_active_n", { n: dirs.length }) : areaTitle(dirs[0]));
  }
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
  const activeDocId = activeTab && activeTab.kind === "file" ? activeTab.docId : "";
  const root = ftBuildTreeModel();
  const markup = ftRenderNodeHtml(root, 0, activeDocId);
  if (!markup) {
    tree.innerHTML = "<div class='p-4 text-xs text-[#738196] text-center'>" + escapeHtml(t("ft_empty_ws")) + "</div>";
    return;
  }
  tree.innerHTML = markup;
  tree.querySelectorAll("[data-ft-folder]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const k = btn.getAttribute("data-ft-folder") || "";
      if (ftExpanded.has(k)) { ftExpanded.delete(k); } else { ftExpanded.add(k); }
      renderRightFilesTree();
    });
  });
  tree.querySelectorAll("[data-ft-doc]").forEach(function (btn) {
    btn.addEventListener("click", function () { openFileInCenterTab(btn.getAttribute("data-ft-doc") || ""); });
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

async function openFileInCenterTab(docId) {
  if (!docId || typeof centerChatTabs === "undefined") { return; }
  const existing = centerChatTabs.find(function (tb) { return tb.kind === "file" && tb.docId === docId; });
  if (existing) { activateCenterChatTab(existing.id); return; }
  const guide = (typeof allGuides !== "undefined" && Array.isArray(allGuides)) ? allGuides.find(function (g) { return g.doc_id === docId; }) : null;
  if (!guide) { return; }
  const filename = ftFileNameOf(guide), ext = ftExtOf(filename);
  const editable = ext === ".md" || ext === ".txt";
  const areaObj = (typeof knowledgeAreas !== "undefined" ? knowledgeAreas : []).find(function (a) { return a.name === (guide.area || activeKnowledgeArea); });
  const tab = {
    id: "ft_" + (++wbTabSeq), kind: "file", docId: docId, title: filename, filename: filename,
    breadcrumb: ftBuildBreadcrumb(guide, filename), editable: editable,
    readOnly: !editable || Boolean(areaObj && areaObj.linked),
    mdMode: "preview", rawContent: null, dirty: false, loading: false, error: "",
  };
  if (typeof snapshotActiveCenterTab === "function") { snapshotActiveCenterTab(); }
  centerChatTabs.push(tab);
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
  if (tab.editable && tab.rawContent !== null) {
    return formatMarkdown(ftStripFrontmatter(tab.rawContent));
  }
  const guide = (typeof allGuides !== "undefined" && Array.isArray(allGuides)) ? allGuides.find(function (g) { return g.doc_id === tab.docId; }) : null;
  if (!guide) { return "<div class='wb-empty'>" + escapeHtml(t("md_load_err")) + "</div>"; }
  return "<h1 style='margin:0;font-size:calc(1.45rem * var(--ui-scale,1));font-weight:600'>" + escapeHtml(guide.title || tab.filename) + "</h1>"
    + (guide.sections || []).map(function (s) {
      return "<section style='padding:0.95rem 1.1rem;border-radius:0.85rem;background:var(--surface-raised);border:1px solid var(--border-subtle)'><h2 style='margin:0 0 0.5rem;font-size:calc(1.05rem * var(--ui-scale,1));font-weight:600'>" + escapeHtml(s.section_title) + "</h2><div class='md-body text-sm leading-relaxed flex flex-col gap-2'>" + formatMarkdown(s.content || "", false, 3) + "</div></section>";
    }).join("");
}

function renderCenterFileTab(tab) {
  const box = document.getElementById("center-file-view"); if (!box || !tab) { return; }
  if (tab.editable && tab.rawContent === null && !tab.loading && !tab.error) { loadFileTabRaw(tab); return; }
  const mode = tab.editable ? (tab.mdMode || "preview") : "preview";
  const roBadge = tab.readOnly ? "<span class='wb-stat-pill'>" + escapeHtml(t("md_readonly_badge")) + "</span>" : "";
  const modeSeg = tab.editable
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
  } else {
    const edPane = mode === "raw" || mode === "split"
      ? "<div class='cf-editor-pane'><textarea id='cf-editor-ta' class='cf-editor' spellcheck='false' aria-label='" + escapeHtml(tab.filename) + "'" + (tab.readOnly ? " readonly" : "") + "></textarea></div>"
      : "";
    const pvPane = mode === "preview" || mode === "split"
      ? "<div class='cf-preview-pane'><div id='cf-preview-inner' class='cf-preview-inner md-body md-prose'>" + ftPreviewHtmlForTab(tab) + "</div></div>"
      : "";
    bodyHtml = edPane + pvPane;
  }
  box.innerHTML = "<div class='cf-bar'><div class='cf-crumb' title='" + escapeHtml(tab.breadcrumb) + "'>" + FT_FILE_SVG + "<span>" + escapeHtml(tab.breadcrumb) + "</span>" + roBadge + "</div>"
    + "<div class='cf-controls'><span id='cf-status' class='cf-status'></span>" + modeSeg + saveBtn
    + "<button id='cf-chat-file-btn' type='button' class='wb-btn wb-btn-sm'>" + escapeHtml(t("md_chat_file")) + "</button></div></div>"
    + "<div class='cf-body" + (mode === "split" ? " is-split" : "") + "'>" + bodyHtml + "</div>";
  box.querySelectorAll("[data-cf-mode]").forEach(function (b) {
    b.addEventListener("click", function () { tab.mdMode = b.getAttribute("data-cf-mode") || "preview"; renderCenterFileTab(tab); });
  });
  const ta = document.getElementById("cf-editor-ta");
  if (ta) {
    ta.value = tab.rawContent || "";
    ta.addEventListener("input", function () {
      tab.rawContent = ta.value;
      if (!tab.dirty && !tab.readOnly) { tab.dirty = true; const sb = document.getElementById("cf-save-btn"); if (sb) { sb.disabled = false; sb.classList.add("wb-btn-primary"); } if (typeof renderCenterChatTabs === "function") { renderCenterChatTabs(); } }
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
  const sBtn = document.getElementById("cf-save-btn"), cBtn = document.getElementById("cf-chat-file-btn");
  if (sBtn) { sBtn.addEventListener("click", function () { saveCenterFileTab(tab); }); }
  if (cBtn) { cBtn.addEventListener("click", function () { if (typeof startScopedChat === "function") { startScopedChat({ doc_id: tab.docId, subfolder: null }); } }); }
  renderRightFilesTree();
}

function bindFileTabUX() {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) { return; }
  const nBtn = document.getElementById("tree-new-note-btn"), rBtn = document.getElementById("tree-refresh-btn"), cBtn = document.getElementById("tree-collapse-btn");
  if (nBtn) { nBtn.addEventListener("click", function () { if (typeof openNewNoteModal === "function") { openNewNoteModal(); } }); }
  if (rBtn) { rBtn.addEventListener("click", async function () { if (typeof loadGuidesCatalog === "function") { await loadGuidesCatalog(null); } renderRightFilesTree(); }); }
  if (cBtn) { cBtn.addEventListener("click", function () { ftExpanded.clear(); renderRightFilesTree(); }); }
  renderRightFilesTree();
}
"""
