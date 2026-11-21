"""Native folder selectors, upload destinations and physical reader moves."""

from features.ui.folder_actions_script import FOLDER_ACTIONS_SCRIPT
from features.ui.folder_tree_script import FOLDER_TREE_SCRIPT
from features.ui.move_script import MOVE_SCRIPT

FOLDER_SCRIPT: str = FOLDER_TREE_SCRIPT + FOLDER_ACTIONS_SCRIPT + MOVE_SCRIPT + r"""
let workspaceFolders = [], unloadedFolders = [], selectedSubfolder = "", subfolderArea = null;
function folderOptions(selected) {
  const area = selectedAreas().length > 1 ? selected.split("/")[0] : null;
  return [{ path: area || "", doc_count: 0 }].concat(workspaceFolders.filter(f => f.path && (!area || f.area === area && f.path !== area))).map(function (folder) {
    return "<option value='" + escapeHtml(folder.path) + "'" + (folder.path === selected ? " selected" : "") + ">"
      + escapeHtml(folder.path && folder.path !== area ? folder.path : t("up_area_root")) + "</option>";
  }).join("") + "<option value=':new:'>" + escapeHtml(t("up_new_sub_opt")) + "</option>";
}
function applySubfolders(ws) {
  const area = selectedAreas().join(",");
  if (area !== subfolderArea) { selectedSubfolder = ""; collapsedFolders.clear(); expandedFolders.clear(); subfolderArea = area; }
  if (Array.isArray(ws.subfolders)) { workspaceFolders = ws.subfolders; }
  unloadedFolders = Array.isArray(ws.unloaded_subfolders) ? ws.unloaded_subfolders : [];
  if (selectedSubfolder && !workspaceFolders.some(f => f.path === selectedSubfolder)) { selectedSubfolder = ""; }
  syncUploadAreas();
}
function syncUploadAreas(reset = true) {
  const select = document.getElementById("upload-save-area"), dirs = selectedAreas(), previous = select.value;
  document.getElementById("upload-save-area-group").hidden = dirs.length < 2;
  select.innerHTML = dirs.map(dir => "<option value='" + escapeHtml(dir) + "'>" + escapeHtml(areaLabel(dir)) + "</option>").join("");
  select.value = !reset && dirs.includes(previous) ? previous : dirs[0];
  refreshUploadFolders();
}
function refreshUploadFolders() {
  const area = document.getElementById("upload-save-area").value, select = document.getElementById("upload-subfolder");
  const prefix = selectedAreas().length > 1 ? area + "/" : "", selected = selectedSubfolder.startsWith(prefix) ? selectedSubfolder.slice(prefix.length) : "";
  const paths = selectedAreas().length > 1 ? workspaceFolders.filter(f => f.area === area).map(f => f.path === area ? "" : f.path.slice(prefix.length)) : workspaceFolders.map(f => f.path);
  select.innerHTML = [...new Set(["", ...paths])].map(path => "<option value='" + escapeHtml(path) + "'>" + escapeHtml(path || t("up_area_root")) + "</option>").join("") + "<option value=':new:'>" + escapeHtml(t("up_new_sub_opt")) + "</option>";
  select.value = paths.includes(selected) ? selected : "";
  document.getElementById("upload-new-subfolder-group").classList.add("hidden"); document.getElementById("upload-new-subfolder").required = false;
}
document.getElementById("upload-save-area").addEventListener("change", refreshUploadFolders);
function destinationControls(prefix, selected) {
  return `<div class='flex flex-col gap-1.5 min-w-0'>
    <label for='${prefix}-subfolder' class='text-xs text-[#A0B0C8]'>${escapeHtml(t("up_save_sub"))}</label>
    <select id='${prefix}-subfolder' name='subfolder' class='rounded-lg bg-[#04060F] border border-white/15 px-3 py-2 text-sm'>${folderOptions(selected)}</select>
    <div id='${prefix}-new-subfolder-group' class='hidden'>
      <label for='${prefix}-new-subfolder' class='block text-xs text-[#A0B0C8] mb-1'>${escapeHtml(t("up_new_sub_lbl"))}</label>
      <input id='${prefix}-new-subfolder' name='new_subfolder' type='text' maxlength='255' placeholder='architecture/backend'
        autocapitalize='none' spellcheck='false' aria-describedby='${prefix}-folder-help'
        class='w-full rounded-lg bg-[#04060F] border border-white/15 px-3 py-2 text-sm'/>
    </div>
    <p id='${prefix}-folder-help' class='text-[11px] text-[#738196]'>${escapeHtml(t("up_sub_help"))}</p>
  </div>`;
}
function bindDestination(prefix) {
  const select = document.getElementById(prefix + "-subfolder");
  select.addEventListener("change", function () {
    const creating = select.value === ":new:", input = document.getElementById(prefix + "-new-subfolder");
    document.getElementById(prefix + "-new-subfolder-group").classList.toggle("hidden", !creating);
    input.required = creating;
    if (creating) { input.focus(); }
  });
}
function destinationValue(prefix) {
  const select = document.getElementById(prefix + "-subfolder");
  if (select.value !== ":new:") { return select.value; }
  const input = document.getElementById(prefix + "-new-subfolder");
  if (!input.reportValidity()) { return null; }
  return input.value.trim();
}
function openUploadDialog(preferredMode) {
  syncUploadAreas(true);
  document.getElementById("upload-new-subfolder-group").classList.add("hidden");
  document.getElementById("upload-new-subfolder").required = false;
  if (typeof setUploadDestinationMode === "function") {
    const mode = preferredMode || ((currentTurns.length > 0 || (typeof freeChatMode !== "undefined" && freeChatMode)) ? "chat" : "vault");
    setUploadDestinationMode(mode);
  }
  uploadModal.showModal();
}
function matchesSubfolder(guide) {
  const path = guide.subfolder || "";
  return !selectedSubfolder || path === selectedSubfolder || path.startsWith(selectedSubfolder + "/");
}
function bindSubfolderLibrary(root) {
  bindFolderTree(root);
  bindFolderActions(root);
}
function bindGuideFolder(guide, previousTag) {
  bindDestination("reader");
  document.getElementById("move-guide-btn").addEventListener("click", async function () {
    const subfolder = destinationValue("reader"), version = areaVersion;
    if (subfolder === null) { return; }
    const button = document.getElementById("move-guide-btn"), status = document.getElementById("move-guide-status");
    button.disabled = true; status.textContent = "Moving guide...";
    try {
      const data = await requestGuideMove(guide, subfolder, version);
      if (!data) { return; }
      const updated = data.guide;
      if (version === areaVersion && updated) { await renderGuideReader(updated, previousTag); }
    } catch (error) { if (version === areaVersion && status.isConnected) { status.textContent = error.message; } }
    finally { if (button.isConnected) { button.disabled = false; } }
  });
}
"""
