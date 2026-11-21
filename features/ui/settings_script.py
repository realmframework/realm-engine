"""Accessible Settings tabs; legacy label pairs keep the untouched answer renderer stable."""

SETTINGS_SCRIPT: str = r"""
let searchStatusOperation = 0;
async function refreshSearchStatus() {
  const version = areaVersion, operation = ++searchStatusOperation, badge = document.getElementById("rag-engine-status-badge");
  try {
    const response = await areaFetch("/api/system-status"), status = await response.json();
    if (version !== areaVersion || operation !== searchStatusOperation) { return; }
    if (!response.ok) { throw new Error(status.detail || "Search status is unavailable."); }
    badge.textContent = status.retrieval_tier === "hybrid_local" ? t("rag_hybrid_active") : t("rag_keyword_active");
  } catch (error) { if (version === areaVersion && operation === searchStatusOperation) { badge.textContent = error.message; } }
}
function modeCopy(everyday, specialist) {
  return "<span data-everyday-only>" + escapeHtml(everyday) + "</span><span data-specialist-only>" + escapeHtml(specialist) + "</span>";
}
function activateSettingsTab(name, focus = false) {
  const selected = document.getElementById("settings-tab-" + name);
  if (!selected) { return; }
  document.querySelectorAll("#settings-tabs [role='tab']").forEach(tab => {
    const active = tab === selected; tab.setAttribute("aria-selected", String(active)); tab.tabIndex = active ? 0 : -1;
    document.getElementById("settings-panel-" + tab.dataset.settingsTab).hidden = !active;
  });
  document.getElementById("settings-body").scrollTop = 0;
  if (focus) { selected.focus(); }
  if (name === "appearance" && typeof loadWorkspaceLogo === "function") { loadWorkspaceLogo(); }
  if (name === "ai") { refreshBudget(); loadKeyStatus(); }
  if (name === "rag") { syncRagStudioUI(); refreshSearchStatus(); }
  if (name === "privacy") { document.getElementById("compliance-area").textContent = activeKnowledgeArea || ""; runComplianceAudit(); }
}
function openSettings(name = "workspace") {
  activateSettingsTab(name);
  if (!settingsModal.open) { settingsModal.showModal(); }
  refreshBudget(); loadKeyStatus();
}
function bindSettingsTabs() {
  const tabs = Array.from(document.querySelectorAll("#settings-tabs [role='tab']"));
  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => activateSettingsTab(tab.dataset.settingsTab));
    tab.addEventListener("keydown", event => {
      let target;
      if (event.key === "ArrowRight") { target = tabs[(index + 1) % tabs.length]; }
      else if (event.key === "ArrowLeft") { target = tabs[(index + tabs.length - 1) % tabs.length]; }
      else if (event.key === "Home") { target = tabs[0]; }
      else if (event.key === "End") { target = tabs[tabs.length - 1]; }
      if (target) { event.preventDefault(); target.focus(); }
    });
  });
  document.querySelectorAll("[data-open-settings-tab]").forEach(button => button.addEventListener("click", () => {
    activateSettingsTab(button.dataset.openSettingsTab, true);
  }));
}
"""
