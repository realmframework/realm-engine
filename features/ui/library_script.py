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
    const finish = function () { clearTimeout(timeoutId); window.removeEventListener("scrollend", finish); window.removeEventListener("scroll", onScroll); resolve(); };
    const onScroll = function () { clearTimeout(timeoutId); timeoutId = setTimeout(finish, 100); };
    window.addEventListener("scrollend", finish, { once: true }); window.addEventListener("scroll", onScroll, { passive: true }); timeoutId = setTimeout(finish, 100);
  });
}
function buildIdeaPool() {
  const clean = workspacePrompts.filter(prompt => !/\[REDACTED_|\bpage\s+\d+\b/i.test(prompt));
  return clean.length ? clean : ["Summarize the key points across my documents", "Extract key action items and important details", "What should I focus on next?"];
}
function renderSeedIdeas() {
  const pool = buildIdeaPool(), listEl = document.getElementById("seed-list"); if (!listEl || !pool.length) { return; }
  listEl.innerHTML = [0, 1, 2].map(function (i) { const seed = pool[(ideaOffset + i) % pool.length]; return "<button class='seed-chip text-left text-[#A0B0C8] hover:text-[#EEF2F8] text-[15px] py-1.5 transition-colors flex items-center gap-2.5 group w-fit' data-seed='" + escapeHtml(seed) + "' type='button'><span class='text-[#738196] group-hover:text-[#4BB8E8] transition-colors'>↳</span><span>" + escapeHtml(seed) + "</span></button>"; }).join("");
  listEl.querySelectorAll(".seed-chip").forEach(function (chip) { chip.addEventListener("click", function () { queryEl.value = chip.getAttribute("data-seed") || ""; askTutor(); }); });
}
function cycleIdeas() { const pool = buildIdeaPool(); ideaOffset = (ideaOffset + 3) % Math.max(pool.length, 3); renderSeedIdeas(); }
function syncFolderHelper(dirVal, helperId) {
  const el = document.getElementById(helperId), clean = (dirVal || "knowledge_base").trim() || "knowledge_base";
  if (el) { el.textContent = "Saved locally in your library folder (" + clean + "/)"; }
}
function applyWorkspacePayload(ws) {
  if (!ws) { return; }
  if (activeKnowledgeArea && ws.config && ws.config.knowledge_dir !== activeKnowledgeArea) { return; }
  adoptWorkspace(ws); applySubfolders(ws); applyLocalPolicy(); applyScopeWorkspace(); syncRunMode();
  document.getElementById("daily-cloud-request-limit").value = String(workspaceConfig.daily_cloud_request_limit ?? 50);
  document.getElementById("daily-budget-usd-limit").value = String(workspaceConfig.daily_budget_usd_limit ?? 1);
  const cfg = ws.config || {}, kDir = cfg.knowledge_dir || "knowledge_base", dirs = Array.isArray(ws.available_dirs) && ws.available_dirs.length ? ws.available_dirs : ["knowledge_base"];
  const title = cfg.app_title || "My Knowledge Base";
  document.title = title;
  document.getElementById("hero-greeting-text").textContent = cfg.hero_greeting || "Where should we start?";
  if (!isActiveView) { queryEl.placeholder = defaultPlaceholder; }
  document.getElementById("cfg-app-title").value = title;
  const obTitleEl = document.getElementById("onboarding-title"); if (obTitleEl) { obTitleEl.value = title; }
  document.getElementById("cfg-knowledge-dir").value = kDir; document.getElementById("cfg-anonymize-uploads").checked = cfg.anonymize_uploads !== false;
  for (const selId of ["cfg-folder-select", "onboarding-folder-select"]) {
    const sel = document.getElementById(selId);
    if (sel) { sel.innerHTML = dirs.map(function (d) { return "<option value='" + escapeHtml(d) + "'>" + escapeHtml(d) + "</option>"; }).join(""); sel.value = dirs.includes(kDir) ? kDir : dirs[0]; }
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
function stageUploadFiles(fileList) {
  stagedFiles = fileList ? Array.from(fileList) : [];
  const stEl = document.getElementById("upload-staged-list"), statusEl = document.getElementById("upload-status");
  if (stEl) { stEl.textContent = stagedFiles.length ? "Selected: " + stagedFiles.map(function (f) { return f.name; }).join(", ") : ""; }
  if (statusEl) { statusEl.textContent = ""; }
  clearRedactionPreview(); if (stagedFiles.length) { previewUploads(); }
}
let uploadToastTimeout;
function showToast(message) {
  const toast = document.getElementById("upload-toast");
  clearTimeout(uploadToastTimeout);
  toast.textContent = message;
  toast.classList.remove("hidden");
  uploadToastTimeout = setTimeout(function () { toast.classList.add("hidden"); }, 5500);
}
function showUploadToast(title) { showToast("Indexed " + title + " into Library"); }
async function uploadFiles(fileList) {
  const version = areaVersion;
  const files = Array.from(fileList && fileList.length ? fileList : stagedFiles);
  const statusEl = document.getElementById("upload-status"), button = document.getElementById("confirm-upload-btn");
  if (!files.length) { statusEl.textContent = "Select one or more files first."; return; }
  if (button.disabled) { return; }
  const subfolder = destinationValue("upload"), saveArea = document.getElementById("upload-save-area").value || activeKnowledgeArea;
  if (subfolder === null) { return; }
  button.disabled = true; statusEl.textContent = "Converting & indexing...";
  const fd = new FormData();
  for (const file of files) { fd.append("files", file); }
  fd.append("subfolder", subfolder); fd.append("area", saveArea);
  fd.append("anonymize", String(document.getElementById("cfg-anonymize-uploads").checked));
  let indexed = false;
  try {
    const response = await areaFetch("/api/upload", { method: "POST", body: fd });
    const data = await response.json();
    if (version !== areaVersion) { return; }
    if (!response.ok) { throw new Error(data.detail || "Upload failed."); }
    indexed = true;
    uploadModal.close();
    stageUploadFiles([]); document.getElementById("upload-file-input").value = "";
    applyWorkspacePayload(data); selectedSubfolder = selectedAreas().length > 1 ? saveArea + (subfolder ? "/" + subfolder : "") : subfolder;
    document.getElementById("upload-new-subfolder").value = "";
    document.getElementById("upload-new-subfolder").required = false;
    document.getElementById("upload-new-subfolder-group").classList.add("hidden");
    const title = (data.uploaded_titles || data.uploaded_files || []).join(", ");
    showUploadToast(title || "document");
    await loadGuidesCatalog(null);
    if (version === areaVersion && isActiveView && !currentChatId) { await openLibraryCatalog(selectedTag); }
  } catch (error) {
    if (version === areaVersion) {
      if (indexed) { areaStatus("Indexed successfully. Reopen Library to refresh its catalog."); }
      else { statusEl.textContent = error.message || "Upload failed. Please try again."; }
    }
  } finally { button.disabled = false; }
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
  abortActiveRequest(); stopGraphSimulation(); currentChatId = null; currentTurns = []; document.getElementById("chat-stream").innerHTML = ""; renderRecentChats();
  setViewMode(true, true); renderTutor(null); chunksHeader.classList.add("hidden"); document.getElementById("stream-divider").classList.add("hidden"); resultsEl.classList.remove("hidden");
  const operation = currentScrollId;
  const loaded = await loadGuidesCatalog(tagFilter), guides = loaded.filter(matchesSubfolder), heading = tagFilter ? "Guides · " + tagFilter + " (" + guides.length + ")" : "Library (" + guides.length + " Guides)";
  if (version !== areaVersion || operation !== currentScrollId) { return; }
  resultsEl.innerHTML = "<section id='library-view' aria-labelledby='catalog-heading'><div class='flex items-center justify-between gap-3 pt-6 mb-4 flex-wrap'><h2 id='catalog-heading' tabindex='-1' class='text-xl font-medium text-[#EEF2F8] outline-none'>" + escapeHtml(heading) + "</h2><div class='flex items-center gap-3'><button id='library-upload-btn' type='button' class='px-3 py-1.5 rounded-xl bg-[#4BB8E8]/10 hover:bg-[#4BB8E8]/20 text-[#4BB8E8] border border-[#4BB8E8]/30 text-xs font-medium transition'>+ Upload</button></div></div>" + subfolderLibraryHeader() + "<nav id='library-topics' aria-label='Library topics' class='library-topics'></nav><div id='library-guides' class='flex flex-col gap-4'>" + (guides.length ? "" : "<div class='library-empty-state'><p class='text-sm text-[#A0B0C8]'>No guides here yet</p><p class='text-xs text-[#738196] mt-2'>Upload a document or choose another folder to get started.</p></div>") + guides.map(function (g, idx) {
    const tagLine = (g.tags || []).length ? "<div class='text-xs font-mono text-[#4BB8E8]/80 tracking-wide'>// " + (g.tags || []).map(escapeHtml).join(" · ") + "</div>" : "";
    const secs = (g.sections || []).map(function (s, i) { return "<div class='text-sm text-[#A0B0C8]'>" + escapeHtml(/^\d+\./.test(s.section_title) ? s.section_title : (i + 1) + ". " + s.section_title) + "</div>"; }).join("");
    return "<article data-guide-idx='" + idx + "' tabindex='0' class='group w-full p-5 rounded-xl bg-[#0B1020] border border-[rgba(238,242,248,0.08)] hover:border-[#4BB8E8]/50 transition-all cursor-pointer flex flex-col gap-2.5'><div class='flex items-baseline justify-between gap-3'><h3 class='text-lg font-medium text-[#EEF2F8] group-hover:text-[#4BB8E8] transition-colors'>" + escapeHtml(g.title) + "</h3><button type='button' data-delete-guide='" + idx + "' aria-label='Delete guide " + escapeHtml(g.title) + "' class='text-[#738196] hover:text-[#EF4444] p-2 shrink-0'><svg aria-hidden='true' class='w-4 h-4' viewBox='0 0 24 24' fill='none' stroke='currentColor'><path d='M3 6h18M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7m4-7v7'/></svg></button></div>" + cardFolderPill(g, idx) + scopedChatButton(g.doc_id) + tagLine + "<div class='flex flex-col gap-1 pt-2 border-t border-[rgba(238,242,248,0.06)]'>" + secs + "</div></article>";
  }).join("") + "</div></section>";
  renderLibraryTopics();
  bindAreaButtons(resultsEl); bindSubfolderLibrary(resultsEl);
  bindCardFolderPills(resultsEl, guides, tagFilter); bindScopedChatButtons(resultsEl);
  resultsEl.querySelectorAll("[data-delete-guide]").forEach(function (button) { button.addEventListener("click", function (event) { event.stopPropagation(); deleteLibraryGuide(guides[Number(button.dataset.deleteGuide)], tagFilter); }); });
  const upBtn = document.getElementById("library-upload-btn"); if (upBtn) { upBtn.addEventListener("click", function () { openUploadDialog(); }); }
  resultsEl.querySelectorAll("[data-guide-idx]").forEach(function (card) { card.addEventListener("click", function () { const g = guides[Number(card.getAttribute("data-guide-idx") || 0)]; if (g) { renderGuideReader(g, tagFilter); } }); });
}
""" + FOLDER_SCRIPT + READER_SCRIPT
