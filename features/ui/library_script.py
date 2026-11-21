"""Client-side Markdown, dynamic workspace metadata, document upload, and Library helpers."""

from features.ui.folder_script import FOLDER_SCRIPT
from features.ui.markdown_script import MARKDOWN_SCRIPT
from features.ui.reader_script import READER_SCRIPT

LIBRARY_SCRIPT: str = MARKDOWN_SCRIPT + r"""
let allGuides = [], workspacePrompts = [], workspaceTags = [], workspaceDocCount = 0, ideaOffset = 0, currentScrollId = 0, defaultPlaceholder = "Ask anything...", stagedFiles = [];
function withViewTransition(updateFn, focusEl) {
  if (!document.startViewTransition || window.matchMedia("(prefers-reduced-motion: reduce)").matches) { updateFn(); if (focusEl) { focusEl.focus({ preventScroll: true }); } return Promise.resolve(); }
  const transition = document.startViewTransition(updateFn), operation = currentScrollId;
  transition.ready.catch(function () {});
  return Promise.allSettled([transition.updateCallbackDone, transition.finished]).then(function (results) { if (results[0].status === "rejected") { throw results[0].reason; } if (operation === currentScrollId && focusEl && focusEl.isConnected) { focusEl.focus({ preventScroll: true }); } });
}
function scrollIntoViewAsync(element, options) {
  const result = element.scrollIntoView(Object.assign({}, options, window.matchMedia("(prefers-reduced-motion: reduce)").matches ? { behavior: "instant" } : {}));
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
  listEl.innerHTML = [0, 1, 2].map(function (i) { const seed = pool[(ideaOffset + i) % pool.length]; return "<button class='seed-chip text-left text-[#A0B0C8] hover:text-[#EEF2F8] text-[15px] py-1.5 transition-colors flex items-center gap-2.5 group w-fit' data-seed='" + escapeHtml(seed) + "' type='button'><span class='text-[#738196] group-hover:text-[#4BB8E8] transition-colors'>↳</span><span>" + escapeHtml(seed) + "</span></button>"; }).join("");
  listEl.querySelectorAll(".seed-chip").forEach(function (chip) { chip.addEventListener("click", function () { queryEl.value = chip.getAttribute("data-seed") || ""; askTutor(); }); });
}
function cycleIdeas() { const pool = buildIdeaPool(); ideaOffset = (ideaOffset + 3) % Math.max(pool.length, 3); renderSeedIdeas(); }
function syncFolderHelper(dirVal, helperId) {
  const el = document.getElementById(helperId), clean = (dirVal || "knowledge_base").trim() || "knowledge_base";
  const area = knowledgeAreas.find(function (a) { return a.name === clean; });
  if (el) {
    el.textContent = area && area.linked && area.linked_path
      ? "Linked in place: " + area.linked_path + " (files stay where they are)"
      : "Saved locally in your library folder (" + clean + "/)";
  }
}
function applyWorkspacePayload(ws) {
  if (!ws) { return; }
  if (activeKnowledgeArea && ws.config && ws.config.knowledge_dir !== activeKnowledgeArea) { return; }
  adoptWorkspace(ws); applySubfolders(ws); applyLocalPolicy(); applyScopeWorkspace(); syncRunMode(); syncThemeFromWorkspace(ws.config || {});
  document.getElementById("daily-cloud-request-limit").value = String(workspaceConfig.daily_cloud_request_limit ?? 50);
  document.getElementById("daily-budget-usd-limit").value = String(workspaceConfig.daily_budget_usd_limit ?? 1);
  const cfg = ws.config || {}, kDir = cfg.knowledge_dir || "knowledge_base", dirs = Array.isArray(ws.available_dirs) && ws.available_dirs.length ? ws.available_dirs : ["knowledge_base"];
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
      sel.innerHTML = dirs.map(function (d) {
        const a = knowledgeAreas.find(function (item) { return item.name === d; });
        const lbl = a && a.linked ? ((a.display_name || d) + " (Linked)") : d;
        return "<option value='" + escapeHtml(d) + "'>" + escapeHtml(lbl) + "</option>";
      }).join("");
      sel.value = dirs.includes(kDir) ? kDir : dirs[0];
    }
  }
  syncFolderHelper(kDir, "cfg-folder-helper"); syncFolderHelper(kDir, "onboarding-folder-helper");
  workspaceDocCount = Number(ws.doc_count || 0); workspaceTags = Array.isArray(ws.tags) ? ws.tags : []; workspacePrompts = Array.isArray(ws.starter_prompts) ? ws.starter_prompts : [];
  document.getElementById("sidebar-guide-count").textContent = String(workspaceDocCount); document.getElementById("home-guide-count").textContent = String(workspaceDocCount);
  renderLibraryTopics(); if (workspacePrompts.length) { ideaOffset = 0; renderSeedIdeas(); }
}
async function loadWorkspace() { const version = areaVersion, response = await areaFetch("/api/workspace"), data = await response.json(); if (response.ok && version === areaVersion) { applyWorkspacePayload(data); } }
async function saveWorkspace() {
  const statusEl = document.getElementById("workspace-status"); statusEl.textContent = "Re-indexing folder...";
  const payload = { ...workspaceConfig, app_title: document.getElementById("cfg-app-title").value.trim() || "My Knowledge Base", hero_greeting: "Where should we start?", search_placeholder: "Ask anything...", knowledge_dir: document.getElementById("cfg-knowledge-dir").value.trim() || "knowledge_base", anonymize_uploads: document.getElementById("cfg-anonymize-uploads").checked, strict_local_only: localOnly() };
  payload.active_dirs = payload.knowledge_dir === activeKnowledgeArea ? selectedAreas() : [payload.knowledge_dir];
  const res = await areaFetch("/api/workspace", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  if (!res.ok) { statusEl.textContent = (await res.json()).detail || "Invalid folder path."; return; }
  const ws = await res.json(), view = currentWorkspaceView(); ++areaVersion; resetHome(); allGuides = []; savedChats = []; clearRedactionPreview(); activeKnowledgeArea = null; selectedTag = null; applyWorkspacePayload(ws); await loadGuidesCatalog(null); await loadRecentChats(); await restoreWorkspaceView(view);
  statusEl.textContent = "Indexed " + ws.doc_count + " guides."; settingsModal.close();
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
  uploadToastTimeout = setTimeout(function () { toast.classList.add("hidden"); }, durationMs || 5500);
}
function showUploadToast(title) { showToast("Indexed " + title + " into Library"); }
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
      const data = await response.json();
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
      if (indexed) { areaStatus("Indexed successfully. Reopen Library to refresh its catalog."); }
      else { statusEl.textContent = error.message || "Upload failed. Please try again."; }
    }
  } finally {
    button.disabled = false;
    if (typeof setUploadProgress === "function") { setUploadProgress(false); }
  }
}
async function loadGuidesCatalog(tagFilter) {
  const version = areaVersion;
  const guides = await (await areaFetch(tagFilter ? "/api/guides?tag=" + encodeURIComponent(tagFilter) : "/api/guides")).json();
  if (version !== areaVersion) { return []; }
  if (!tagFilter && Array.isArray(guides)) { allGuides = guides; renderScopeChoices(); }
  return Array.isArray(guides) ? guides : [];
}
async function openLibraryCatalog(tagFilter) {
  const version = areaVersion;
  abortActiveRequest(); stopGraphSimulation(); currentChatId = null; currentTurns = []; if (typeof syncInspectorSidebar === "function") { inspectorOpen = false; syncInspectorSidebar(); } document.getElementById("chat-stream").innerHTML = ""; renderRecentChats();
  setViewMode(true, true); renderTutor(null); chunksHeader.classList.add("hidden"); document.getElementById("stream-divider").classList.add("hidden"); resultsEl.classList.remove("hidden");
  const operation = currentScrollId;
  const loaded = await loadGuidesCatalog(tagFilter), guides = loaded.filter(matchesSubfolder), unit = guides.length === 1 ? " Guide" : " Guides", heading = tagFilter ? "Guides · " + tagFilter + " (" + guides.length + ")" : "Library (" + guides.length + unit + ")";
  if (version !== areaVersion || operation !== currentScrollId) { return; }
  const curAreaObj = knowledgeAreas.find(function (a) { return a.name === activeKnowledgeArea; });
  const unloadVaultBtn = curAreaObj && curAreaObj.linked && selectedAreas().length === 1
    ? "<button id='library-unload-vault-btn' type='button' title='Unlink folder from REALM without deleting any files on disk' class='px-3 py-1.5 rounded-xl bg-[#0B1020] border border-white/15 hover:border-[#4BB8E8] text-xs font-medium text-[#A0B0C8] hover:text-[#EEF2F8] transition'>Unlink Folder</button>"
    : "";
  resultsEl.innerHTML = "<section id='library-view' aria-labelledby='catalog-heading'><div class='flex items-center justify-between gap-3 pt-6 mb-4 flex-wrap'><h2 id='catalog-heading' tabindex='-1' class='text-xl font-medium text-[#EEF2F8] outline-none'>" + escapeHtml(heading) + "</h2><div class='flex items-center gap-2 flex-wrap'>" + unloadVaultBtn + "<button id='library-reveal-btn' type='button' class='px-3 py-1.5 rounded-xl bg-[#0B1020] border border-white/15 hover:border-[#4BB8E8] text-xs font-medium text-[#A0B0C8] hover:text-[#EEF2F8] transition'>" + escapeHtml(revealFolderLabel()) + "</button><button id='library-sync-btn' type='button' class='px-3 py-1.5 rounded-xl bg-[#0B1020] border border-white/15 hover:border-[#4BB8E8] text-xs font-medium text-[#A0B0C8] hover:text-[#EEF2F8] transition'>" + escapeHtml(t("sync_folder")) + "</button><button id='library-upload-btn' type='button' class='px-3 py-1.5 rounded-xl bg-[#4BB8E8]/10 hover:bg-[#4BB8E8]/20 text-[#4BB8E8] border border-[#4BB8E8]/30 text-xs font-medium transition'>+ Upload</button></div></div>" + subfolderLibraryHeader() + "<nav id='library-topics' aria-label='Library topics' class='library-topics'></nav><div id='library-guides' class='flex flex-col gap-4'>" + (guides.length ? "" : "<div class='library-empty-state'><p class='text-sm text-[#A0B0C8]'>No guides here yet</p><p class='text-xs text-[#738196] mt-2'>Upload a document, import a folder, or open this workspace in Finder/Explorer.</p></div>") + guides.map(function (g, idx) {
    const tagLine = (g.tags || []).length ? "<div class='text-xs font-mono text-[#4BB8E8]/80 tracking-wide'>// " + (g.tags || []).map(escapeHtml).join(" · ") + "</div>" : "";
    const secs = (g.sections || []).map(function (s, i) { return "<div class='text-sm text-[#A0B0C8]'>" + escapeHtml(/^\d+\./.test(s.section_title) ? s.section_title : (i + 1) + ". " + s.section_title) + "</div>"; }).join("");
    return "<article data-guide-idx='" + idx + "' tabindex='0' class='group w-full p-5 rounded-xl bg-[#0B1020] border border-[rgba(238,242,248,0.08)] hover:border-[#4BB8E8]/50 transition-all cursor-pointer flex flex-col gap-2.5'><div class='flex items-baseline justify-between gap-3'><h3 class='text-lg font-medium text-[#EEF2F8] group-hover:text-[#4BB8E8] transition-colors'>" + escapeHtml(g.title) + "</h3><button type='button' data-delete-guide='" + idx + "' aria-label='Delete guide " + escapeHtml(g.title) + "' class='text-[#738196] hover:text-[#EF4444] p-2 shrink-0'><svg aria-hidden='true' class='w-4 h-4' viewBox='0 0 24 24' fill='none' stroke='currentColor'><path d='M3 6h18M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7m4-7v7'/></svg></button></div>" + cardFolderPill(g, idx) + scopedChatButton(g.doc_id) + tagLine + "<div class='flex flex-col gap-1 pt-2 border-t border-[rgba(238,242,248,0.06)]'>" + secs + "</div></article>";
  }).join("") + "</div></section>";
  renderLibraryTopics();
  bindAreaButtons(resultsEl); bindSubfolderLibrary(resultsEl);
  bindCardFolderPills(resultsEl, guides, tagFilter); bindScopedChatButtons(resultsEl);
  resultsEl.querySelectorAll("[data-delete-guide]").forEach(function (button) { button.addEventListener("click", function (event) { event.stopPropagation(); deleteLibraryGuide(guides[Number(button.dataset.deleteGuide)], tagFilter); }); });
  const ulBtn = document.getElementById("library-unload-vault-btn"); if (ulBtn) { ulBtn.addEventListener("click", function () { deleteKnowledgeArea(activeKnowledgeArea); }); }
  const revBtn = document.getElementById("library-reveal-btn"); if (revBtn) { revBtn.addEventListener("click", function () { revealWorkspaceFolder(selectedSubfolder || ""); }); }
  const synBtn = document.getElementById("library-sync-btn"); if (synBtn) { synBtn.addEventListener("click", function () { syncWorkspaceFolder(false); }); }
  const upBtn = document.getElementById("library-upload-btn"); if (upBtn) { upBtn.addEventListener("click", function () { openUploadDialog(); }); }
  resultsEl.querySelectorAll("[data-guide-idx]").forEach(function (card) { card.addEventListener("click", function () { const g = guides[Number(card.getAttribute("data-guide-idx") || 0)]; if (g) { renderGuideReader(g, tagFilter); } }); });
}
""" + FOLDER_SCRIPT + READER_SCRIPT
