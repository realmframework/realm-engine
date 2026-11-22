"""A deliberately requested model download with honest indeterminate progress."""

INSTALL_SCRIPT: str = r"""
async function installRecommendedLocalAI() {
  const button = document.getElementById("download-local-model-btn"), status = document.getElementById("local-install-status"), version = areaVersion;
  button.disabled = true; button.setAttribute("aria-busy", "true");
  status.textContent = "Downloading Ollama search helper (~274 MB)… You can keep using the app.";
  try {
    const response = await areaFetch("/api/system/pull-model", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ model: "embedding" }) }), data = await response.json();
    if (!response.ok) { throw new Error(data.detail || "Download could not be completed."); }
    if (version !== areaVersion) { status.textContent = "Ollama search helper installed."; return; }
    const refreshed = await areaFetch("/api/workspace", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(workspaceConfig) });
    if (version !== areaVersion) { return; }
    if (!refreshed.ok) { throw new Error("Search helper installed. Reopen this workspace to refresh its search index."); }
    applyWorkspacePayload(await refreshed.json()); await loadSystemStatus();
    status.textContent = "Ollama search helper is ready.";
  } catch (error) { status.textContent = error.message || "Download could not be completed."; }
  finally { button.disabled = false; button.removeAttribute("aria-busy"); }
}
"""
