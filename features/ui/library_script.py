"""Client-side Markdown, dynamic workspace metadata, document upload, and Library helpers."""

from features.ui.folder_script import FOLDER_SCRIPT
from features.ui.markdown_script import MARKDOWN_SCRIPT
from features.ui.reader_script import READER_SCRIPT

LIBRARY_SCRIPT: str = MARKDOWN_SCRIPT + r"""
let allGuides = [], workspacePrompts = [], workspaceDocCount = 0, ideaOffset = 0, currentScrollId = 0, defaultPlaceholder = "Ask anything...", stagedFiles = [];
function withViewTransition(updateFn, focusEl) {
  const red = typeof prefersReducedMotion === "function" ? prefersReducedMotion() : window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!document.startViewTransition || red) { updateFn(); if (focusEl) { focusEl.focus({ preventScroll: true }); } return Promise.resolve(); }
  const transition = document.startViewTransition(updateFn), operation = currentScrollId;
  transition.ready.catch(function () {});
  return Promise.allSettled([transition.updateCallbackDone, transition.finished]).then(function (results) { if (results[0].status === "rejected") { throw results[0].reason; } if (operation === currentScrollId && focusEl && focusEl.isConnected) { focusEl.focus({ preventScroll: true }); } });
}
function scrollIntoViewAsync(element, options) {
  const red = typeof prefersReducedMotion === "function" ? prefersReducedMotion() : window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const result = element.scrollIntoView(Object.assign({}, options, red ? { behavior: "instant" } : {}));
  if (result instanceof Promise) { return result; }
  return new Promise(function (resolve) {
    let timeoutId;
    const scroller = element.closest("#active-stream") || window;
    const finish = function () { clearTimeout(timeoutId); scroller.removeEventListener("scrollend", finish); scroller.removeEventListener("scroll", onScroll); resolve(); };
    const onScroll = function () { clearTimeout(timeoutId); timeoutId = setTimeout(finish, 100); };
    scroller.addEventListener("scrollend", finish, { once: true }); scroller.addEventListener("scroll", onScroll, { passive: true }); timeoutId = setTimeout(finish, 100);
  });
}
function buildIdeaPool() {
  const clean = workspacePrompts.filter(prompt => !/\[REDACTED_|\bpage\s+\d+\b/i.test(prompt));
  const rawPool = clean.length ? clean : [t("seed_1"), t("seed_2"), t("seed_3")];
  return rawPool.map(function (prompt) { return typeof localizeIdea === "function" ? localizeIdea(prompt) : prompt; });
}
function renderSeedIdeas() {
  const pool = buildIdeaPool(), listEl = document.getElementById("seed-list"); if (!listEl || !pool.length) { return; }
  listEl.innerHTML = [0, 1, 2].map(function (i) { const seed = pool[(ideaOffset + i) % pool.length]; return "<button class='seed-chip text-left text-[#A0B0C8] hover:text-[#EEF2F8] text-sm py-1.5 transition-colors flex items-center gap-2.5 group w-fit' data-seed='" + escapeHtml(seed) + "' type='button'><span class='text-[#738196] group-hover:text-[#4BB8E8] transition-colors'>↳</span><span>" + escapeHtml(seed) + "</span></button>"; }).join("");
  listEl.querySelectorAll(".seed-chip").forEach(function (chip) { chip.addEventListener("click", function () { queryEl.value = chip.getAttribute("data-seed") || ""; askTutor(); }); });
}
function cycleIdeas() { const pool = buildIdeaPool(); ideaOffset = (ideaOffset + 3) % Math.max(pool.length, 3); renderSeedIdeas(); }
function syncFolderHelper(dirVal, helperId) {
  const el = document.getElementById(helperId), clean = String(dirVal || "").trim();
  const area = clean ? knowledgeAreas.find(function (a) { return a.name === clean; }) : null;
  if (el) {
    el.textContent = !clean ? t("folder_none_free") : (area && area.linked && area.linked_path
      ? t("folder_linked_in_place", { path: area.linked_path })
      : t("folder_saved_local", { dir: clean }));
  }
}
function applyWorkspacePayload(ws) {
  if (!ws) { return; }
  if (activeKnowledgeArea && ws.config && ws.config.knowledge_dir !== activeKnowledgeArea) { return; }
  adoptWorkspace(ws); applySubfolders(ws); applyLocalPolicy(); applyScopeWorkspace(); syncRunMode(); syncThemeFromWorkspace(ws.config || {}); if (typeof applyReadingComfort === "function") { applyReadingComfort(ws.config || {}, true); } if (typeof syncEcoModeUI === "function") { syncEcoModeUI(ws.config || {}); } if (typeof syncLocalApiUI === "function") { syncLocalApiUI(ws.config || {}); }
  document.getElementById("daily-cloud-request-limit").value = String(workspaceConfig.daily_cloud_request_limit ?? 50);
  document.getElementById("daily-budget-usd-limit").value = String(workspaceConfig.daily_budget_usd_limit ?? 1);
  const cfg = ws.config || {}, kDir = cfg.knowledge_dir || "", dirs = Array.isArray(ws.available_dirs) ? ws.available_dirs : [];
  const title = cfg.app_title || "My Knowledge Base";
  document.title = title;
  const greeting = cfg.hero_greeting && cfg.hero_greeting !== "Where should we start?" ? cfg.hero_greeting : t("hero_greeting");
  document.getElementById("hero-greeting-text").textContent = greeting;
  if (!isActiveView) { queryEl.placeholder = defaultPlaceholder; }
  document.getElementById("cfg-app-title").value = title;
  const obTitleEl = document.getElementById("onboarding-title"); if (obTitleEl) { obTitleEl.value = title; }
  document.getElementById("cfg-knowledge-dir").value = kDir; document.getElementById("cfg-anonymize-uploads").checked = cfg.anonymize_uploads !== false;
  for (const selId of ["cfg-folder-select", "onboarding-folder-select"]) {
    const sel = document.getElementById(selId);
    if (sel) {
      sel.innerHTML = dirs.length ? dirs.map(function (d) {
        const a = knowledgeAreas.find(function (item) { return item.name === d; });
        const lbl = a && a.linked ? ((a.display_name || d) + " (Linked)") : d;
        return "<option value='" + escapeHtml(d) + "'>" + escapeHtml(lbl) + "</option>";
      }).join("") : "<option value=''>" + escapeHtml(t("free_chat_short")) + "</option>";
      sel.value = dirs.includes(kDir) ? kDir : (dirs[0] || "");
    }
  }
  for (const bId of ["download-backup-btn", "restore-backup-btn"]) { const b = document.getElementById(bId); if (b) { b.disabled = !kDir; } }
  syncFolderHelper(kDir, "cfg-folder-helper"); syncFolderHelper(kDir, "onboarding-folder-helper");
  workspaceDocCount = Number(ws.doc_count || 0); workspacePrompts = Array.isArray(ws.starter_prompts) ? ws.starter_prompts : [];
  document.getElementById("sidebar-guide-count").textContent = String(workspaceDocCount); document.getElementById("home-guide-count").textContent = String(workspaceDocCount);
  renderLibraryTopics(); if (workspacePrompts.length) { ideaOffset = 0; renderSeedIdeas(); }
  if (typeof loadWorkBoardSummary === "function") { loadWorkBoardSummary(false); }
}
async function loadWorkspace() {
  const version = areaVersion;
  try {
    const response = await areaFetch("/api/workspace");
    if (!response.ok || version !== areaVersion) { return; }
    const data = await safeJson(response);
    if (version === areaVersion) { applyWorkspacePayload(data); }
  } catch (_e) {}
}
async function saveWorkspace() {
  const statusEl = document.getElementById("workspace-status"); statusEl.textContent = "Re-indexing folder...";
  const nextDir = document.getElementById("cfg-knowledge-dir").value.trim();
  const payload = { ...workspaceConfig, app_title: document.getElementById("cfg-app-title").value.trim() || "My Knowledge Base", hero_greeting: "Where should we start?", search_placeholder: "Ask anything...", knowledge_dir: nextDir, anonymize_uploads: document.getElementById("cfg-anonymize-uploads").checked, strict_local_only: localOnly() };
  payload.active_dirs = !nextDir ? [] : (nextDir === activeKnowledgeArea ? selectedAreas() : [nextDir]);
  try {
    const res = await areaFetch("/api/workspace", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const ws = await safeJson(res);
    if (!res.ok) { statusEl.textContent = ws.detail || "Invalid folder path."; return; }
    const view = currentWorkspaceView(); ++areaVersion; resetHome(); allGuides = []; savedChats = []; clearRedactionPreview(); activeKnowledgeArea = null; selectedTag = null; applyWorkspacePayload(ws); await loadGuidesCatalog(null); await loadRecentChats(); await restoreWorkspaceView(view);
    statusEl.textContent = "Indexed " + ws.doc_count + " guides."; settingsModal.close();
  } catch (err) { statusEl.textContent = err.message || "Could not save workspace."; }
}
function fileRelPath(file) { return (file && (file._relPath || file.webkitRelativePath)) || ""; }
function stageUploadFiles(fileList) {
  stagedFiles = fileList ? Array.from(fileList) : [];
  const stEl = document.getElementById("upload-staged-list"), statusEl = document.getElementById("upload-status");
  if (stEl) {
    const folders = new Set(stagedFiles.map(function (f) { const r = fileRelPath(f); return r.includes("/") ? r.slice(0, r.lastIndexOf("/")) : ""; }).filter(Boolean));
    stEl.textContent = !stagedFiles.length ? "" : (folders.size ? (stagedFiles.length + " files across " + folders.size + " folders ready (preserving subfolders)") : ("Selected: " + stagedFiles.map(function (f) { return f.name; }).join(", ")));
  }
  if (statusEl) { statusEl.textContent = ""; }
  clearRedactionPreview(); if (stagedFiles.length) { previewUploads(); }
}
let uploadToastTimeout;
function showToast(message, durationMs) {
  const toast = document.getElementById("upload-toast");
  clearTimeout(uploadToastTimeout);
  toast.textContent = message;
  toast.classList.remove("hidden");
  const live = document.getElementById("app-live-status");
  if (live) { live.textContent = message; }
  uploadToastTimeout = setTimeout(function () { toast.classList.add("hidden"); }, durationMs || 5500);
}
function showUploadToast(title) { showToast(t("toast_indexed_lib", { title: title })); }
async function uploadFiles(fileList) {
  const version = areaVersion;
  const files = Array.from(fileList && fileList.length ? fileList : stagedFiles);
  if (typeof uploadDestinationMode !== "undefined" && uploadDestinationMode === "chat" && typeof attachFilesToCurrentChat === "function") {
    await attachFilesToCurrentChat(files); return;
  }
  const statusEl = document.getElementById("upload-status"), button = document.getElementById("confirm-upload-btn");
  if (!files.length) { statusEl.textContent = "Select one or more files first."; return; }
  if (button.disabled) { return; }
  const subfolder = destinationValue("upload"), saveArea = document.getElementById("upload-save-area").value || activeKnowledgeArea;
  if (subfolder === null) { return; }
  const hasFolderTree = files.some(function (f) { return fileRelPath(f).includes("/"); });
  const anon = String(document.getElementById("cfg-anonymize-uploads").checked);
  const batches = []; let cur = [], curBytes = 0;
  for (const file of files) {
    const sz = Number(file.size || 0);
    if (cur.length && (curBytes + sz > 35 * 1024 * 1024 || cur.length >= 40)) { batches.push(cur); cur = []; curBytes = 0; }
    cur.push(file); curBytes += sz;
  }
  if (cur.length) { batches.push(cur); }
  button.disabled = true;
  let indexed = false, lastData = null, totalUploaded = 0, totalSkipped = 0;
  try {
    for (let b = 0; b < batches.length; b++) {
      const label = batches.length > 1 ? ("Uploading batch " + (b + 1) + " / " + batches.length + "…") : ("Converting & indexing " + files.length + (files.length === 1 ? " file…" : " files…"));
      statusEl.textContent = label;
      if (typeof setUploadProgress === "function") { setUploadProgress(true, label, (b + 1) + " / " + batches.length, Math.round(((b + 0.5) / batches.length) * 90), batches[b].map(f => f.name).slice(0, 3).join(", ")); }
      const fd = new FormData();
      for (const file of batches[b]) { fd.append("files", file); fd.append("relative_paths", fileRelPath(file)); }
      fd.append("subfolder", subfolder); fd.append("area", saveArea); fd.append("anonymize", anon);
      if (hasFolderTree) { fd.append("skip_unsupported", "true"); }
      const response = await areaFetch("/api/upload", { method: "POST", body: fd });
      const data = await safeJson(response);
      if (version !== areaVersion) { return; }
      if (!response.ok) { throw new Error(data.detail || "Upload failed."); }
      indexed = true; lastData = data;
      totalUploaded += (data.uploaded_files || []).length;
      totalSkipped += Number(data.skipped_files || 0);
    }
    uploadModal.close();
    stageUploadFiles([]); document.getElementById("upload-file-input").value = "";
    const folderIn = document.getElementById("upload-folder-input"); if (folderIn) { folderIn.value = ""; }
    if (lastData) { applyWorkspacePayload(lastData); }
    selectedSubfolder = selectedAreas().length > 1 ? saveArea + (subfolder ? "/" + subfolder : "") : subfolder;
    document.getElementById("upload-new-subfolder").value = "";
    document.getElementById("upload-new-subfolder").required = false;
    document.getElementById("upload-new-subfolder-group").classList.add("hidden");
    const summary = totalUploaded > 1 ? (totalUploaded + " documents" + (totalSkipped ? " (" + totalSkipped + " unsupported skipped)" : "")) : ((lastData && (lastData.uploaded_titles || lastData.uploaded_files) || []).join(", ") || "document");
    showUploadToast(summary);
    await loadGuidesCatalog(null);
    if (version === areaVersion && isActiveView && !currentChatId) { await openLibraryCatalog(selectedTag); }
  } catch (error) {
    if (version === areaVersion) {
      if (indexed) { areaStatus(t("st_indexed_refresh")); }
      else { statusEl.textContent = error.message || "Upload failed. Please try again."; }
    }
  } finally {
    button.disabled = false;
    if (typeof setUploadProgress === "function") { setUploadProgress(false); }
  }
}
async function loadGuidesCatalog(tagFilter) {
  const version = areaVersion;
  try {
    const res = await areaFetch(tagFilter ? "/api/guides?tag=" + encodeURIComponent(tagFilter) : "/api/guides");
    if (!res.ok || version !== areaVersion) { return []; }
    const guides = await safeJson(res);
    if (version !== areaVersion) { return []; }
    if (!tagFilter && Array.isArray(guides)) { allGuides = guides; renderScopeChoices(); }
    return Array.isArray(guides) ? guides : [];
  } catch (_e) { return []; }
}
async function openLibraryCatalog(tagFilter) {
  const version = areaVersion;
  abortActiveRequest(); stopGraphSimulation(); currentChatId = null; currentTurns = []; if (typeof syncInspectorSidebar === "function") { inspectorOpen = false; syncInspectorSidebar(); } document.getElementById("chat-stream").replaceChildren(); renderRecentChats();
  await setViewMode(true, true);
  if (version !== areaVersion) { return; }
  renderTutor(null); chunksHeader.classList.add("hidden"); document.getElementById("stream-divider").classList.add("hidden"); resultsEl.classList.remove("hidden");
  if (!knowledgeAreas.length) {
    resultsEl.innerHTML = "<section id='library-view' class='library-empty-state pt-16 flex flex-col items-center gap-4'><h1 id='catalog-heading' class='text-xl font-medium text-[#EEF2F8]'>" + escapeHtml(t("no_ws_empty_t")) + "</h1><p class='text-sm text-[#A0B0C8] max-w-md'>" + escapeHtml(t("no_ws_empty_d")) + "</p><div class='flex flex-wrap items-center justify-center gap-2.5 pt-2'><button type='button' data-new-area class='px-4 py-2 rounded-xl bg-[#4BB8E8] text-[#04060F] text-xs font-semibold hover:brightness-110 transition'>" + escapeHtml(t("new_area_btn")) + "</button><button id='empty-lib-link-btn' type='button' class='px-4 py-2 rounded-xl bg-[#0B1020] border border-white/15 hover:border-[#4BB8E8] text-xs text-[#EEF2F8] transition'>" + escapeHtml(t("open_vault")) + "</button></div></section>";
    bindAreaButtons(resultsEl);
    const lb = document.getElementById("empty-lib-link-btn"); if (lb) { lb.addEventListener("click", linkExistingFolder); }
    return;
  }
  const operation = currentScrollId;
  const loaded = await loadGuidesCatalog(tagFilter), guides = loaded.filter(matchesSubfolder), unit = guides.length === 1 ? t("lib_guide_1") : t("lib_guide_n"), heading = tagFilter ? t("lib_guides_tag", { tag: tagFilter, n: guides.length }) : t("lib_heading", { n: guides.length, unit: unit });
  if (version !== areaVersion || operation !== currentScrollId) { return; }
  const curAreaObj = knowledgeAreas.find(function (a) { return a.name === activeKnowledgeArea; });
  const unloadVaultBtn = curAreaObj && curAreaObj.linked && selectedAreas().length === 1
    ? "<button id='library-unload-vault-btn' type='button' title='Unlink folder from REALM without deleting any files on disk' class='turn-popover-item'>" + escapeHtml(t("lib_unlink")) + "</button>"
    : "";
  const libToolsMenu = "<details id='library-tools-menu' class='turn-more-menu relative inline-block'><summary class='list-none cursor-pointer px-3 py-1.5 rounded-xl bg-[#0B1020] border border-white/15 hover:border-[#4BB8E8] text-xs font-medium text-[#A0B0C8] hover:text-[#EEF2F8] transition inline-flex items-center gap-1'><span>" + escapeHtml(t("lib_tools_menu")) + "</span><span aria-hidden='true'>⌄</span></summary><div class='header-popover-panel'><button id='library-gap-scan-btn' type='button' class='turn-popover-item'>" + escapeHtml(t("gap_btn")) + "</button><button id='library-briefing-btn' type='button' class='turn-popover-item'>" + escapeHtml(t("br_btn")) + "</button><button id='library-sync-btn' type='button' class='turn-popover-item'>" + escapeHtml(t("sync_folder")) + "</button><button id='library-reveal-btn' type='button' class='turn-popover-item'>" + escapeHtml(revealFolderLabel()) + "</button>" + unloadVaultBtn + "</div></details>";
  resultsEl.innerHTML = "<section id='library-view' aria-labelledby='catalog-heading'><div class='flex items-center justify-between gap-3 pt-6 mb-4 flex-wrap'><h1 id='catalog-heading' tabindex='-1' class='text-xl font-medium text-[#EEF2F8] outline-none'>" + escapeHtml(heading) + "</h1><div class='flex items-center gap-2 flex-wrap'>" + libToolsMenu + "<button id='library-study-btn' type='button' class='px-3 py-1.5 rounded-xl bg-[#0B1020] border border-white/15 hover:border-[#4BB8E8] text-xs font-medium text-[#A0B0C8] hover:text-[#EEF2F8] transition'>" + escapeHtml(t("study_btn")) + "</button><button id='library-new-note-btn' type='button' class='px-3 py-1.5 rounded-xl bg-[#0B1020] border border-white/15 hover:border-[#4BB8E8] text-xs font-medium text-[#EEF2F8] transition'>" + escapeHtml(t("lib_new_note")) + "</button><button id='library-upload-btn' type='button' class='px-3.5 py-1.5 rounded-xl bg-[#4BB8E8]/10 hover:bg-[#4BB8E8]/20 text-[#4BB8E8] border border-[#4BB8E8]/30 text-xs font-medium transition'>" + escapeHtml(t("lib_upload")) + "</button></div></div>" + subfolderLibraryHeader() + "<nav id='library-topics' aria-label='Library topics' class='library-topics'></nav><div id='library-guides' class='flex flex-col gap-4'>" + (guides.length ? "" : "<div class='library-empty-state'><p class='text-sm text-[#A0B0C8]'>" + escapeHtml(t("lib_empty_t")) + "</p><p class='text-xs text-[#738196] mt-2'>" + escapeHtml(t("lib_empty_d")) + "</p></div>") + guides.map(function (g, idx) {
    const tagLine = (g.tags || []).length ? "<div class='text-xs font-mono text-[#4BB8E8]/80 tracking-wide'>// " + (g.tags || []).map(escapeHtml).join(" · ") + "</div>" : "";
    const secs = (g.sections || []).map(function (s, i) { return "<div class='text-sm text-[#A0B0C8]'>" + escapeHtml(/^\d+\./.test(s.section_title) ? s.section_title : (i + 1) + ". " + s.section_title) + "</div>"; }).join("");
    return "<article data-guide-idx='" + idx + "' class='group w-full p-5 rounded-xl bg-[#0B1020] border border-[rgba(238,242,248,0.08)] hover:border-[#4BB8E8]/50 transition-all cursor-pointer flex flex-col gap-2.5'><div class='flex items-baseline justify-between gap-3'><h2 class='text-lg font-medium text-[#EEF2F8] group-hover:text-[#4BB8E8] transition-colors'><button type='button' data-open-guide='" + idx + "' class='text-left hover:underline'>" + escapeHtml(g.title) + "</button></h2><button type='button' data-delete-guide='" + idx + "' aria-label='" + escapeHtml(t("aria_del_doc", { title: g.title })) + "' class='text-[#738196] hover:text-[#EF4444] p-2 shrink-0'><svg aria-hidden='true' class='w-4 h-4' viewBox='0 0 24 24' fill='none' stroke='currentColor'><path d='M3 6h18M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7m4-7v7'/></svg></button></div>" + cardFolderPill(g, idx) + scopedChatButton(g.doc_id) + tagLine + "<div class='flex flex-col gap-1 pt-2 border-t border-[rgba(238,242,248,0.06)]'>" + secs + "</div></article>";
  }).join("") + "</div></section>";
  renderLibraryTopics();
  bindAreaButtons(resultsEl); bindSubfolderLibrary(resultsEl);
  bindCardFolderPills(resultsEl, guides, tagFilter); bindScopedChatButtons(resultsEl);
  resultsEl.querySelectorAll("[data-delete-guide]").forEach(function (button) { button.addEventListener("click", function (event) { event.stopPropagation(); deleteLibraryGuide(guides[Number(button.dataset.deleteGuide)], tagFilter); }); });
  const closeLibTools = function () { const m = document.getElementById("library-tools-menu"); if (m) { m.open = false; } };
  const ulBtn = document.getElementById("library-unload-vault-btn"); if (ulBtn) { ulBtn.addEventListener("click", function () { closeLibTools(); deleteKnowledgeArea(activeKnowledgeArea); }); }
  const revBtn = document.getElementById("library-reveal-btn"); if (revBtn) { revBtn.addEventListener("click", function () { closeLibTools(); revealWorkspaceFolder(selectedSubfolder || ""); }); }
  const synBtn = document.getElementById("library-sync-btn"); if (synBtn) { synBtn.addEventListener("click", function () { closeLibTools(); syncWorkspaceFolder(false); }); }
  const gapBtn = document.getElementById("library-gap-scan-btn"); if (gapBtn) { gapBtn.addEventListener("click", function () { closeLibTools(); if (typeof openGapAnalysisModal === "function") { openGapAnalysisModal(); } }); }
  const stBtn = document.getElementById("library-study-btn"); if (stBtn) { stBtn.addEventListener("click", function () { if (typeof openStudyDeck === "function") { openStudyDeck({ subfolder: selectedSubfolder || null }); } }); }
  const brBtn = document.getElementById("library-briefing-btn"); if (brBtn) { brBtn.addEventListener("click", function () { closeLibTools(); if (typeof openBriefingModal === "function") { openBriefingModal({ subfolder: selectedSubfolder || "" }); } }); }
  const nnBtn = document.getElementById("library-new-note-btn"); if (nnBtn) { nnBtn.addEventListener("click", function () { if (typeof openNewNoteModal === "function") { openNewNoteModal(); } }); }
  const upBtn = document.getElementById("library-upload-btn"); if (upBtn) { upBtn.addEventListener("click", function () { openUploadDialog(); }); }
  resultsEl.querySelectorAll("[data-open-guide]").forEach(function (btn) { btn.addEventListener("click", function (e) { e.stopPropagation(); const g = guides[Number(btn.getAttribute("data-open-guide") || 0)]; if (g) { renderGuideReader(g, tagFilter); } }); });
  resultsEl.querySelectorAll("[data-guide-idx]").forEach(function (card) { card.addEventListener("click", function (e) { if (e.target.closest("button, a, details, select, input")) { return; } const g = guides[Number(card.getAttribute("data-guide-idx") || 0)]; if (g) { renderGuideReader(g, tagFilter); } }); });
}
""" + FOLDER_SCRIPT + READER_SCRIPT
