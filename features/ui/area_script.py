"""Knowledge-area navigation and request context for isolated browser sessions."""

AREA_SCRIPT: str = r"""
let activeKnowledgeArea = null, knowledgeAreas = [], areaVersion = 0, areaSwitching = false, workspaceConfig = {};
function areaFetch(url, options, expectedArea) {
  const init = Object.assign({}, options || {}), headers = new Headers(init.headers || {}), area = expectedArea === undefined ? activeKnowledgeArea : expectedArea;
  if (area) { headers.set("x-knowledge-area", area); headers.set("x-knowledge-selection", selectedAreas().join(",")); } init.headers = headers;
  return fetch(url, init);
}
function areaStatus(message) {
  const el = document.getElementById("area-status"); if (el) { el.textContent = message; }
  const live = document.getElementById("app-live-status"); if (live && message) { live.textContent = message; }
}
function areaLabel(name) { return String(name).replace(/[_-]+/g, " "); }
function areaTitle(areaOrName) {
  if (areaOrName && typeof areaOrName === "object") { return areaOrName.display_name || areaLabel(areaOrName.name || ""); }
  const found = knowledgeAreas.find(function (a) { return a.name === areaOrName; });
  return (found && found.display_name) || areaLabel(areaOrName || "");
}
function selectedAreas() { return workspaceConfig.active_dirs || (activeKnowledgeArea ? [activeKnowledgeArea] : []); }
function areaButtons() {
  const dirs = selectedAreas();
  if (!knowledgeAreas.length) { return "<div class='px-3 py-2 text-xs text-[#738196]'>" + escapeHtml(t("no_ws_menu_hint")) + "</div>"; }
  return knowledgeAreas.map(function (area, index) {
    const selected = dirs.includes(area.name), disabled = areaSwitching || selected && dirs.length === 1;
    const title = areaTitle(area);
    const subPath = area.linked && area.linked_path ? "<span class='block text-[11px] font-mono text-[#738196] truncate mt-0.5' title='" + escapeHtml(area.linked_path) + "'>" + escapeHtml(area.linked_path) + "</span>" : "";
    const rmLabel = area.linked ? "Unlink vault " + title + " (keeps files on disk)" : "Delete area " + title;
    return "<div class='flex items-center gap-1'>"
      + "<label for='area-check-" + index + "' class='inline-flex items-center justify-center shrink-0' style='width:38px;height:38px;cursor:pointer'>"
      + "<input id='area-check-" + index + "' type='checkbox' name='active_dirs' value='" + escapeHtml(area.name) + "' data-area-toggle='" + escapeHtml(area.name) + "' style='accent-color:#4BB8E8' " + (selected ? "checked " : "") + (disabled ? "disabled " : "") + ">"
      + "<span class='visually-hidden'>Include " + escapeHtml(title) + " in search</span></label>"
      + "<button type='button' data-area='" + escapeHtml(area.name) + "' aria-current='" + (area.name === activeKnowledgeArea ? "page" : "false") + "' " + (areaSwitching ? "disabled " : "")
      + "class='flex-1 min-w-0 flex items-center gap-2 px-2 py-2 rounded-lg text-xs text-left " + (selected ? "bg-white/10 text-[#EEF2F8]" : "text-[#A0B0C8] hover:bg-white/5") + "'>"
      + "<span aria-hidden='true' class='w-2 h-2 rounded-full shrink-0' style='background:" + area.color + "'></span><span class='min-w-0 flex-1'><span class='block truncate font-medium'>" + escapeHtml(title) + "</span>" + subPath + "</span>"
      + "<span class='ml-auto font-mono opacity-70 shrink-0'>" + area.doc_count + "</span></button>"
      + (area.can_delete ? "<button type='button' data-delete-area='" + escapeHtml(area.name) + "' title='" + escapeHtml(rmLabel) + "' aria-label='" + escapeHtml(rmLabel) + "' class='text-[#738196] hover:text-[#EF4444] px-2 py-2 shrink-0'>✕</button>" : "") + "</div>";
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
  const dirs = selectedAreas(), all = dirs.length > 0 && knowledgeAreas.length > 0 && knowledgeAreas.every(a => dirs.includes(a.name));
  if (!knowledgeAreas.length && typeof freeChatMode !== "undefined") { freeChatMode = true; }
  const label = !knowledgeAreas.length ? t("free_chat_short") : (dirs.length > 1 ? (all ? t("all_areas_n", { n: dirs.length }) : t("areas_active_n", { n: dirs.length })) : areaTitle(activeKnowledgeArea || t("workspaces_lbl")));
  document.getElementById("brand-title").textContent = label;
  document.getElementById("brand-title").style.fontSize = dirs.length > 1 ? ".875rem" : "";
  document.getElementById("workspace-color-dot").style.gap = dirs.length > 3 ? ".125rem" : "";
  document.getElementById("workspace-switcher-btn").setAttribute("aria-label", "Switch workspace: " + label);
  document.getElementById("workspace-color-dot").innerHTML = dirs.slice(0, 6).map(name => {
    const area = knowledgeAreas.find(a => a.name === name);
    return "<span class='w-2 h-2 rounded-full shrink-0' style='background:" + (area ? area.color : "#4BB8E8") + "'></span>";
  }).join("");
  const selectAll = document.getElementById("select-all-areas-btn"), linkBtn = document.getElementById("link-vault-btn");
  selectAll.setAttribute("aria-pressed", String(all)); selectAll.disabled = areaSwitching || !knowledgeAreas.length; document.getElementById("new-area-btn").disabled = areaSwitching; if (linkBtn) { linkBtn.disabled = areaSwitching; }
  const note = document.getElementById("selection-primary-note"); note.hidden = dirs.length < 2; note.textContent = t("primary_area_note", { area: areaTitle(activeKnowledgeArea || "") });
  document.getElementById("backup-scope-note").textContent = activeKnowledgeArea ? t("backup_scope_note", { area: areaTitle(activeKnowledgeArea) }) : t("backup_no_ws");
  const nav = document.getElementById("knowledge-areas"), scroll = nav.scrollTop; nav.innerHTML = areaButtons(); bindAreaButtons(nav); nav.scrollTop = scroll;
  if (typeof syncFreeChatUI === "function" && typeof freeChatMode !== "undefined" && freeChatMode) { syncFreeChatUI(); }
}
function adoptWorkspace(data) {
  if (JSON.stringify(selectedAreas()) !== JSON.stringify((data.config || {}).active_dirs || [])) { invalidateAudit(); }
  workspaceConfig = data.config || {}; activeKnowledgeArea = workspaceConfig.knowledge_dir || "";
  knowledgeAreas = Array.isArray(data.areas) ? data.areas : [];
  if (!activeKnowledgeArea && !knowledgeAreas.length && typeof freeChatMode !== "undefined") { freeChatMode = true; }
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
  const leavingFree = typeof freeChatMode !== "undefined" && freeChatMode;
  if (leavingFree) { freeChatMode = false; if (typeof syncFreeChatUI === "function") { syncFreeChatUI(); } }
  if (!leavingFree && JSON.stringify(dirs) === JSON.stringify(selectedAreas()) && template === null) { return true; }
  const view = showLibrary === null ? currentWorkspaceView() : showLibrary ? "library" : "chat";
  areaSwitching = true; document.querySelectorAll("#knowledge-areas input, #knowledge-areas button, #select-all-areas-btn, #new-area-btn").forEach(el => { el.disabled = true; }); const version = ++areaVersion, previous = activeKnowledgeArea;
  abortActiveRequest(); stopActiveAudio(); stopGraphSimulation(); resetHome(); stagedFiles = []; clearRedactionPreview();
  const navigation = currentScrollId;
  allGuides = []; savedChats = []; workspacePrompts = []; renderRecentChats(); document.getElementById("seed-list").replaceChildren();
  areaStatus(t("st_opening_ws", { name: areaLabel(name) }));
  try {
    const response = await areaFetch(template === null ? "/api/workspace" : "/api/workspace/create", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(template === null ? Object.assign({}, workspaceConfig, { knowledge_dir: dirs[0], active_dirs: dirs }) : { name, template }) }, previous);
    const data = await safeJson(response);
    if (!response.ok) { throw new Error(data.detail || t("st_switch_err")); }
    if (version !== areaVersion) { return false; }
    activeKnowledgeArea = null; applyWorkspacePayload(data); await Promise.all([loadGuidesCatalog(null), loadRecentChats(), loadModels()]);
    areaStatus(dirs.length > 1 ? t("st_searching_multi", { n: dirs.length }) : t("st_current_ws", { name: areaLabel(name) }));
    if (navigation === currentScrollId) { await restoreWorkspaceView(view); }
    return true;
  } catch (error) {
    try { const response = await areaFetch("/api/workspace", {}, null); if (response.ok) { activeKnowledgeArea = null; applyWorkspacePayload(await safeJson(response)); await Promise.all([loadGuidesCatalog(null), loadRecentChats(), loadModels()]); if (navigation === currentScrollId) { await restoreWorkspaceView(view); } } } catch (_recoveryError) {}
    areaStatus(error.message || t("st_switch_err")); return false;
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
  if (!area || !area.can_delete) { return; }
  const title = areaTitle(area);
  const confirmed = area.linked
    ? await confirmDeletion(t("cf_unlink_ws_t"), t("cf_unlink_ws_m", { title: title, path: area.linked_path || "" }), t("cf_unlink_ws_btn"))
    : await confirmDeletion(t("cf_del_ws_t"), t("cf_del_ws_m", { title: title }), t("cf_del_ws_btn"));
  if (!confirmed || version !== areaVersion) { return; }
  try {
    const response = await areaFetch("/api/workspace/" + encodeURIComponent(name), { method: "DELETE" }, expected), data = await safeJson(response);
    if (!response.ok) { throw new Error(data.detail || t("st_switch_err")); }
    if (version !== areaVersion) { return; }
    if (JSON.stringify(data.config.active_dirs) !== JSON.stringify(selectedAreas())) {
      const view = currentWorkspaceView();
      ++areaVersion; resetHome(); allGuides = []; savedChats = []; clearRedactionPreview(); activeKnowledgeArea = null; applyWorkspacePayload(data);
      if (typeof syncFreeChatUI === "function") { syncFreeChatUI(); }
      await Promise.all([loadGuidesCatalog(null), loadRecentChats(), loadModels()]); await restoreWorkspaceView(view);
    } else {
      applyWorkspacePayload(data);
      if (!document.getElementById("graph-view").classList.contains("hidden")) { await openGraphView(); }
      else if (document.getElementById("catalog-heading")) { await openLibraryCatalog(selectedTag); }
    }
    areaStatus(t(area.linked ? "st_unlinked_ws" : "st_deleted_ws", { title: title }));
  } catch (error) { areaStatus(error.message); }
}
async function linkExistingFolder() {
  if (areaSwitching) { return; }
  closeWorkspaceMenu();
  if (typeof settingsModal !== "undefined" && settingsModal && settingsModal.open) { settingsModal.close(); }
  const view = currentWorkspaceView(), version = ++areaVersion, previous = activeKnowledgeArea;
  areaSwitching = true; renderKnowledgeAreas(); areaStatus(t("st_picking_folder"));
  if (typeof showToast === "function") { showToast(t("toast_link_picking"), 90000); }
  try {
    const res = await areaFetch("/api/workspace/link-folder", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({}) }, previous);
    const data = await safeJson(res);
    if (!res.ok) { throw new Error(data.detail || t("st_link_err")); }
    if (data.cancelled || version !== areaVersion) {
      areaStatus("");
      const toast = document.getElementById("upload-toast"); if (toast) { toast.classList.add("hidden"); }
      return;
    }
    abortActiveRequest(); stopActiveAudio(); stopGraphSimulation(); resetHome(); stagedFiles = []; clearRedactionPreview();
    if (typeof freeChatMode !== "undefined" && freeChatMode) { freeChatMode = false; if (typeof syncFreeChatUI === "function") { syncFreeChatUI(); } }
    allGuides = []; savedChats = []; workspacePrompts = []; renderRecentChats(); document.getElementById("seed-list").replaceChildren();
    activeKnowledgeArea = null; applyWorkspacePayload(data);
    await Promise.all([loadGuidesCatalog(null), loadRecentChats(), loadModels()]);
    const label = areaTitle(data.linked_area || activeKnowledgeArea);
    areaStatus(t("st_linked_ws", { label: label }));
    if (typeof showToast === "function") { showToast(t("toast_linked_folder", { label: label, n: data.doc_count || 0 })); }
    await restoreWorkspaceView(view);
  } catch (error) { areaStatus(error.message || t("st_link_err")); }
  finally { areaSwitching = false; renderKnowledgeAreas(); }
}
document.getElementById("select-all-areas-btn").addEventListener("click", async function () {
  if (areaSwitching) { return; }
  const primary = activeKnowledgeArea, all = knowledgeAreas.every(area => selectedAreas().includes(area.name));
  const dirs = all ? [primary] : [primary, ...knowledgeAreas.map(area => area.name).filter(name => name !== primary)];
  await switchKnowledgeArea(primary, null, null, dirs);
  if (document.getElementById("workspace-menu").matches(":popover-open")) { document.getElementById("select-all-areas-btn").focus(); }
});
for (const linkId of ["link-vault-btn", "settings-link-vault-btn"]) {
  const el = document.getElementById(linkId);
  if (el) { el.addEventListener("click", linkExistingFolder); }
}
async function initializeWorkspace() {
  try { await loadWorkspace(); await Promise.all([loadKeyStatus().then(loadModels), loadSystemStatus(), loadRecentChats(), loadGuidesCatalog(null)]); }
  catch (error) { areaStatus(t("st_ws_load_err")); }
}
"""
