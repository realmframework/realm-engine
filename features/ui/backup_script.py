"""Workspace archive downloads and safe, area-bound restore feedback."""

BACKUP_SCRIPT: str = r"""
let backupBusy = false;
async function downloadWorkspaceBackup() {
  if (backupBusy) { return; }
  backupBusy = true;
  const version = areaVersion, status = document.getElementById("backup-status"), button = document.getElementById("download-backup-btn");
  button.disabled = true; status.textContent = "Preparing your workspace backup…";
  try {
    const response = await areaFetch("/api/backup/export");
    if (version !== areaVersion) { return; }
    if (!response.ok) { throw new Error((await response.json()).detail || "Backup could not be created."); }
    const blob = await response.blob(); if (version !== areaVersion) { return; }
    const url = URL.createObjectURL(blob), link = document.createElement("a");
    link.href = url; link.download = (response.headers.get("content-disposition") || "").match(/filename="([^"]+)"/)?.[1] || "workspace-backup.zip";
    document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    status.textContent = "Backup download started. Keep the file somewhere safe.";
  } catch (error) { if (version === areaVersion) { status.textContent = error.message; } }
  finally { button.disabled = false; backupBusy = false; }
}
async function restoreWorkspaceBackup(event) {
  const input = event.target, file = input.files[0], status = document.getElementById("backup-status"), button = document.getElementById("restore-backup-btn");
  let version = areaVersion;
  if (!file || backupBusy) { input.value = ""; return; }
  if (file.size > 64 * 1024 * 1024) { status.textContent = "Choose a backup ZIP smaller than 64 MiB."; input.value = ""; return; }
  backupBusy = true; button.disabled = true; status.textContent = "Restoring your workspace…";
  const body = new FormData(); body.append("file", file);
  try {
    const response = await areaFetch("/api/backup/import", { method: "POST", body }), data = await response.json();
    if (version !== areaVersion) { return; }
    if (!response.ok) { throw new Error(data.detail || "Backup could not be restored."); }
    version = ++areaVersion; abortActiveRequest(); stopActiveAudio(); resetHome(); clearRedactionPreview();
    allGuides = []; applyWorkspacePayload(data); await Promise.all([loadGuidesCatalog(null), loadRecentChats(), loadModels(), refreshBudget()]);
    status.textContent = "Restored " + data.restored_files + " guide(s). Your Library and chats are ready.";
  } catch (error) { if (version === areaVersion) { status.textContent = error.message; } }
  finally { input.value = ""; button.disabled = false; backupBusy = false; }
}
function bindBackupControls() {
  document.getElementById("download-backup-btn").addEventListener("click", downloadWorkspaceBackup);
  document.getElementById("restore-backup-btn").addEventListener("click", () => { if (!backupBusy) { document.getElementById("backup-restore-file").click(); } });
  document.getElementById("backup-restore-file").addEventListener("change", restoreWorkspaceBackup);
}
"""
