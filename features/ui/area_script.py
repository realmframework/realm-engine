"""Knowledge-area navigation and request context for isolated browser sessions."""

AREA_SCRIPT: str = r"""
let activeKnowledgeArea = null, knowledgeAreas = [], areaVersion = 0, areaSwitching = false, workspaceConfig = {};
function areaFetch(url, options, expectedArea) {
  const init = Object.assign({}, options || {}), headers = new Headers(init.headers || {}), area = expectedArea === undefined ? activeKnowledgeArea : expectedArea;
  if (area) { headers.set("x-knowledge-area", area); headers.set("x-knowledge-selection", selectedAreas().join(",")); } init.headers = headers;
  return fetch(url, init);
}
function areaStatus(message) { const el = document.getElementById("area-status"); if (el) { el.textContent = message; } }
function areaLabel(name) { return String(name).replace(/[_-]+/g, " "); }
function selectedAreas() { return workspaceConfig.active_dirs || (activeKnowledgeArea ? [activeKnowledgeArea] : []); }
function areaButtons() {
  const dirs = selectedAreas();
  return knowledgeAreas.map(function (area, index) {
    const selected = dirs.includes(area.name), disabled = areaSwitching || selected && dirs.length === 1;
    return "<div class='flex items-center gap-1'>"
      + "<label for='area-check-" + index + "' class='inline-flex items-center justify-center shrink-0' style='width:44px;height:44px;cursor:pointer'>"
      + "<input id='area-check-" + index + "' type='checkbox' name='active_dirs' value='" + escapeHtml(area.name) + "' data-area-toggle='" + escapeHtml(area.name) + "' style='accent-color:#4BB8E8' " + (selected ? "checked " : "") + (disabled ? "disabled " : "") + ">"
      + "<span class='visually-hidden'>Include " + escapeHtml(areaLabel(area.name)) + " in search</span></label>"
      + "<button type='button' data-area='" + escapeHtml(area.name) + "' aria-current='" + (area.name === activeKnowledgeArea ? "page" : "false") + "' " + (areaSwitching ? "disabled " : "")
      + "class='flex-1 min-w-0 flex items-center gap-2 px-2 py-2 rounded-lg text-xs text-left " + (selected ? "bg-white/10 text-[#EEF2F8]" : "text-[#A0B0C8] hover:bg-white/5") + "'>"
      + "<span aria-hidden='true' class='w-2 h-2 rounded-full shrink-0' style='background:" + area.color + "'></span><span class='truncate'>" + escapeHtml(areaLabel(area.name))
      + "</span><span class='ml-auto font-mono opacity-70'>" + area.doc_count + "</span></button>"
      + (area.can_delete ? "<button type='button' data-delete-area='" + escapeHtml(area.name) + "' aria-label='Delete area " + escapeHtml(areaLabel(area.name)) + "' class='text-[#738196] hover:text-[#EF4444] px-2 py-2'>✕</button>" : "") + "</div>";
  }).join("");
}
async function toggleAreaSelection(name) {
  if (areaSwitching) { return; }
  const dirs = selectedAreas(), next = dirs.includes(name) ? dirs.filter(dir => dir !== name) : [...dirs, name];
  if (!next.length) { return; }
  await switchKnowledgeArea(next[0], null, null, next);
  const input = Array.from(document.querySelectorAll("[data-area-toggle]")).find(el => el.dataset.areaToggle === name);
  if (input && document.getElementById("workspace-menu").matches(":popover-open")) { input.focus({ preventScroll: true }); }
}
function bindAreaButtons(root) {
  root.querySelectorAll("[data-area]").forEach(function (button) { button.addEventListener("click", async function () { closeWorkspaceMenu(); if (!await switchKnowledgeArea(button.dataset.area)) { document.getElementById("workspace-menu").showPopover(); } }); });
  root.querySelectorAll("[data-area-toggle]").forEach(input => input.addEventListener("change", () => toggleAreaSelection(input.dataset.areaToggle)));
  root.querySelectorAll("[data-delete-area]").forEach(function (button) { button.addEventListener("click", function () { closeWorkspaceMenu(); deleteKnowledgeArea(button.dataset.deleteArea); }); });
  root.querySelectorAll("[data-new-area]").forEach(function (button) { button.addEventListener("click", openNewAreaDialog); });
}
function renderKnowledgeAreas() {
  const dirs = selectedAreas(), all = dirs.length > 0 && knowledgeAreas.every(a => dirs.includes(a.name));
  const label = dirs.length > 1 ? (all ? "All Areas (" + dirs.length + ")" : dirs.length + " Areas Active") : areaLabel(activeKnowledgeArea || "Workspaces");
  document.getElementById("brand-title").textContent = label;
  document.getElementById("brand-title").style.fontSize = dirs.length > 1 ? ".875rem" : "";
  document.getElementById("workspace-color-dot").style.gap = dirs.length > 3 ? ".125rem" : "";
  document.getElementById("workspace-switcher-btn").setAttribute("aria-label", "Switch workspace: " + label);
  document.getElementById("workspace-color-dot").innerHTML = dirs.slice(0, 6).map(name => {
    const area = knowledgeAreas.find(a => a.name === name);
    return "<span class='w-2 h-2 rounded-full shrink-0' style='background:" + (area ? area.color : "#4BB8E8") + "'></span>";
  }).join("");
  const selectAll = document.getElementById("select-all-areas-btn");
  selectAll.setAttribute("aria-pressed", String(all)); selectAll.disabled = areaSwitching; document.getElementById("new-area-btn").disabled = areaSwitching;
  const note = document.getElementById("selection-primary-note"); note.hidden = dirs.length < 2; note.textContent = "Primary: " + areaLabel(activeKnowledgeArea || "") + ". Backups and vault audits use this area.";
  document.getElementById("backup-scope-note").textContent = "Backup covers the primary area “" + areaLabel(activeKnowledgeArea || "") + "” and its single-area chats. Combined chats stay saved locally; they are outside this ZIP backup.";
  const nav = document.getElementById("knowledge-areas"), scroll = nav.scrollTop; nav.innerHTML = areaButtons(); bindAreaButtons(nav); nav.scrollTop = scroll;
}
function adoptWorkspace(data) {
  if (JSON.stringify(selectedAreas()) !== JSON.stringify((data.config || {}).active_dirs || [])) { invalidateAudit(); }
  workspaceConfig = data.config || {}; activeKnowledgeArea = workspaceConfig.knowledge_dir || "knowledge_base";
  knowledgeAreas = Array.isArray(data.areas) ? data.areas : [];
  renderKnowledgeAreas();
}
function currentWorkspaceView() {
  if (!document.getElementById("graph-view").classList.contains("hidden")) { return "graph"; }
  return document.getElementById("library-view") || document.getElementById("reader-heading") ? "library" : "chat";
}
async function restoreWorkspaceView(view) {
  if (view === "graph") { await openGraphView(); }
  else if (view === "library") { await openLibraryCatalog(null); }
}
async function switchKnowledgeArea(name, showLibrary = null, template = null, dirs = [name]) {
  if (areaSwitching) { return false; }
  if (JSON.stringify(dirs) === JSON.stringify(selectedAreas()) && template === null) { return true; }
  const view = showLibrary === null ? currentWorkspaceView() : showLibrary ? "library" : "chat";
  areaSwitching = true; document.querySelectorAll("#knowledge-areas input, #knowledge-areas button, #select-all-areas-btn, #new-area-btn").forEach(el => { el.disabled = true; }); const version = ++areaVersion, previous = activeKnowledgeArea;
  abortActiveRequest(); stopActiveAudio(); stopGraphSimulation(); resetHome(); stagedFiles = []; clearRedactionPreview();
  const navigation = currentScrollId;
  allGuides = []; savedChats = []; workspacePrompts = []; workspaceTags = []; renderRecentChats(); document.getElementById("seed-list").innerHTML = "";
  areaStatus("Opening " + areaLabel(name) + "...");
  try {
    const response = await areaFetch(template === null ? "/api/workspace" : "/api/workspace/create", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(template === null ? Object.assign({}, workspaceConfig, { knowledge_dir: dirs[0], active_dirs: dirs }) : { name, template }) }, previous);
    const data = await response.json();
    if (!response.ok) { throw new Error(data.detail || "Knowledge area could not be opened."); }
    if (version !== areaVersion) { return false; }
    activeKnowledgeArea = null; applyWorkspacePayload(data); await Promise.all([loadGuidesCatalog(null), loadRecentChats(), loadModels()]);
    areaStatus(dirs.length > 1 ? "Searching " + dirs.length + " selected areas." : "Current workspace: " + areaLabel(name));
    if (navigation === currentScrollId) { await restoreWorkspaceView(view); }
    return true;
  } catch (error) {
    try { const response = await areaFetch("/api/workspace", {}, null); if (response.ok) { activeKnowledgeArea = null; applyWorkspacePayload(await response.json()); await Promise.all([loadGuidesCatalog(null), loadRecentChats(), loadModels()]); if (navigation === currentScrollId) { await restoreWorkspaceView(view); } } } catch (_recoveryError) {}
    areaStatus(error.message || "Area switch failed. Please select an area again."); return false;
  }
  finally { areaSwitching = false; renderKnowledgeAreas(); }
}
function openNewAreaDialog() {
  closeWorkspaceMenu();
  document.getElementById("area-name").value = ""; document.getElementById("area-template").value = "blank"; document.getElementById("new-area-status").textContent = ""; document.getElementById("area-modal").showModal();
}
async function createKnowledgeArea(event) {
  if (event.submitter && event.submitter.value === "cancel") { return; }
  event.preventDefault(); const name = document.getElementById("area-name").value.trim().normalize("NFKD").replace(/\p{M}/gu, "").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, ""), button = document.getElementById("create-area-btn");
  button.disabled = true;
  try { if (await switchKnowledgeArea(name, null, document.getElementById("area-template").value)) { document.getElementById("area-modal").close(); } else { document.getElementById("new-area-status").textContent = "Area could not be created. Check the name and try again."; } }
  finally { button.disabled = false; }
}
async function deleteKnowledgeArea(name) {
  const area = knowledgeAreas.find(function (a) { return a.name === name; }), version = areaVersion, expected = activeKnowledgeArea;
  if (!area || !area.can_delete || !await confirmDeletion("Delete knowledge area?", "Permanently delete “" + areaLabel(name) + "” and all its guides, chats and stored files? This cannot be undone.")) { return; }
  if (version !== areaVersion) { return; }
  try {
    const response = await areaFetch("/api/workspace/" + encodeURIComponent(name), { method: "DELETE" }, expected), data = await response.json();
    if (!response.ok) { throw new Error(data.detail || "Area could not be deleted."); }
    if (JSON.stringify(data.config.active_dirs) !== JSON.stringify(selectedAreas())) {
      const view = currentWorkspaceView();
      ++areaVersion; resetHome(); allGuides = []; savedChats = []; clearRedactionPreview(); activeKnowledgeArea = null; applyWorkspacePayload(data); await Promise.all([loadGuidesCatalog(null), loadRecentChats(), loadModels()]); await restoreWorkspaceView(view);
    } else {
      applyWorkspacePayload(data);
      if (!document.getElementById("graph-view").classList.contains("hidden")) { await openGraphView(); }
      else if (document.getElementById("catalog-heading")) { await openLibraryCatalog(selectedTag); }
    }
    areaStatus("Deleted area: " + areaLabel(name));
  } catch (error) { areaStatus(error.message); }
}
document.getElementById("select-all-areas-btn").addEventListener("click", async function () {
  if (areaSwitching) { return; }
  const primary = activeKnowledgeArea, all = knowledgeAreas.every(area => selectedAreas().includes(area.name));
  const dirs = all ? [primary] : [primary, ...knowledgeAreas.map(area => area.name).filter(name => name !== primary)];
  await switchKnowledgeArea(primary, null, null, dirs);
  if (document.getElementById("workspace-menu").matches(":popover-open")) { document.getElementById("select-all-areas-btn").focus(); }
});
async function initializeWorkspace() {
  try { await loadWorkspace(); await Promise.all([loadKeyStatus(), loadModels(), loadSystemStatus(), loadRecentChats(), loadGuidesCatalog(null)]); }
  catch (error) { areaStatus("Workspace could not be loaded. Reload to try again."); }
}
"""
