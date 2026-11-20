"""A deliberately requested model download with honest indeterminate progress."""

INSTALL_SCRIPT: str = r"""
async function installRecommendedLocalAI() {
  const button = document.getElementById("download-local-model-btn"), status = document.getElementById("local-install-status"), version = areaVersion;
  button.disabled = true; button.setAttribute("aria-busy", "true");
  status.textContent = "Downloading your local AI and search helper… This can take several minutes. You can keep using the app.";
  try {
    const response = await areaFetch("/api/system/pull-model", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ model: "recommended" }) }), data = await response.json();
    if (!response.ok) { throw new Error(data.detail || "Download could not be completed."); }
    if (version !== areaVersion) { status.textContent = "Local AI downloaded. Choose Local AI in Settings when you are ready."; return; }
    document.getElementById("onboarding-mode-local").checked = true;
    if (!await applySelectedMode("onboarding")) { throw new Error("Models downloaded. Select Local AI and apply the mode to finish setup."); }
    modelEl.value = data.recommended_model; localStorage.setItem("preferred_local_model", data.recommended_model);
    const refreshed = await areaFetch("/api/workspace", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(workspaceConfig) });
    if (version !== areaVersion) { return; }
    if (!refreshed.ok) { throw new Error("Models downloaded. Reopen this workspace to refresh its search index."); }
    applyWorkspacePayload(await refreshed.json()); await loadSystemStatus();
    status.textContent = "Local AI is ready. Choose Start Exploring to begin.";
  } catch (error) { status.textContent = error.message || "Download could not be completed."; }
  finally { button.disabled = false; button.removeAttribute("aria-busy"); }
}
"""
