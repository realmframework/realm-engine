"""Create children beneath their parent and confirm bounded recursive deletion."""

FOLDER_ACTIONS_SCRIPT: str = r"""
let folderMutationPending = false;
function closeFolderCreator(button, restoreFocus = false) {
  const panel = document.getElementById(button.getAttribute("aria-controls"));
  panel.hidden = true; button.setAttribute("aria-expanded", "false");
  if (restoreFocus) { button.focus({ preventScroll: true }); }
}
function bindFolderActions(root) {
  root.querySelectorAll("[data-create-child]").forEach(function (button) {
    button.addEventListener("click", function () {
      const panel = document.getElementById(button.getAttribute("aria-controls")), opening = panel.hidden;
      root.querySelectorAll("[data-create-child][aria-expanded='true']").forEach(b => closeFolderCreator(b));
      panel.hidden = !opening; button.setAttribute("aria-expanded", String(opening));
      if (opening) { panel.querySelector("input").focus(); }
    });
    const panel = document.getElementById(button.getAttribute("aria-controls"));
    panel.querySelector("input").addEventListener("input", event => event.target.setCustomValidity(""));
    panel.querySelector("[data-cancel-child]").addEventListener("click", () => closeFolderCreator(button, true));
    panel.querySelector("input").addEventListener("keydown", function (event) {
      if (event.key === "Escape" && !event.isComposing) { event.preventDefault(); closeFolderCreator(button, true); }
    });
  });
  root.querySelectorAll("[data-child-form]").forEach(function (form) {
    form.addEventListener("submit", createChildFolder);
  });
  root.querySelectorAll("[data-delete-folder]").forEach(function (button) {
    button.addEventListener("click", () => deleteSubfolder(button.dataset.deleteFolder));
  });
}
async function createChildFolder(event) {
  event.preventDefault();
  const form = event.currentTarget, input = form.elements.name, status = form.querySelector("[data-child-status]");
  if (folderMutationPending || !form.reportValidity()) { return; }
  const name = input.value.trim(), parent = form.dataset.childForm;
  if (!name || /[/\\]/.test(name)) { input.setCustomValidity("Enter one folder name without slashes."); input.reportValidity(); return; }
  input.setCustomValidity("");
  const path = parent ? parent + "/" + name : name, version = areaVersion, operation = currentScrollId;
  const buttons = Array.from(form.querySelectorAll("button"));
  folderMutationPending = true; buttons.forEach(b => { b.disabled = true; }); status.textContent = "Creating subfolder...";
  try {
    const response = await areaFetch("/api/subfolders", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: path }) });
    const data = await response.json();
    if (version !== areaVersion) { return; }
    if (!response.ok) { throw new Error(data.detail || "Subfolder could not be created."); }
    applySubfolders(data); renderScopeChoices();
    if (operation !== currentScrollId || !document.getElementById("catalog-heading")) { return; }
    selectedSubfolder = path;
    const parts = path.split("/"); collapsedFolders.delete("");
    for (let i = 1; i <= parts.length; i++) { collapsedFolders.delete(parts.slice(0, i).join("/")); }
    await openLibraryCatalog(selectedTag);
    if (version !== areaVersion) { return; }
    showToast("Created folder “" + name + "”");
    const selected = Array.from(document.querySelectorAll("[data-subfolder]")).find(b => b.dataset.subfolder === path);
    if (selected) { selected.focus({ preventScroll: true }); }
  } catch (error) {
    if (version === areaVersion && status.isConnected) { status.textContent = error.message || "Subfolder could not be created."; }
  } finally { folderMutationPending = false; buttons.forEach(b => { b.disabled = false; }); }
}
async function deleteSubfolder(path) {
  if (folderMutationPending) { return; }
  if (!path || selectedAreas().length > 1 && selectedAreas().includes(path)) { await deleteKnowledgeArea(path || activeKnowledgeArea); return; }
  const version = areaVersion, area = activeKnowledgeArea, operation = currentScrollId;
  const warning = "Permanently delete “" + area + "/" + path + "”, all nested subfolders and every file inside it, including their indexed passages? This cannot be undone.";
  if (!await confirmDeletion("Delete subfolder?", warning) || version !== areaVersion) { return; }
  folderMutationPending = true;
  try {
    const response = await areaFetch("/api/subfolders?path=" + encodeURIComponent(path), { method: "DELETE" }, area);
    const data = await response.json();
    if (version !== areaVersion) { return; }
    if (!response.ok) { throw new Error(data.detail || "Subfolder could not be deleted."); }
    const stillInLibrary = operation === currentScrollId && document.getElementById("catalog-heading");
    if (stillInLibrary && (selectedSubfolder === path || selectedSubfolder && selectedSubfolder.startsWith(path + "/"))) {
      selectedSubfolder = path.includes("/") ? path.slice(0, path.lastIndexOf("/")) : "";
    }
    for (const folder of collapsedFolders) { if (folder === path || folder.startsWith(path + "/")) { collapsedFolders.delete(folder); } }
    applyWorkspacePayload(data); invalidateAudit(); await loadGuidesCatalog(null);
    if (version !== areaVersion) { return; }
    if (stillInLibrary && operation === currentScrollId) {
      await openLibraryCatalog(selectedTag);
      if (version !== areaVersion) { return; }
      document.getElementById("catalog-heading").focus({ preventScroll: true });
    }
    areaStatus("Deleted subfolder /" + path);
  } catch (error) { if (version === areaVersion) { areaStatus(error.message || "Subfolder deletion failed."); } }
  finally { folderMutationPending = false; }
}
"""
