"""Interactive tab navigation, global ? / Cmd+/ shortcuts, and quick-jump actions for #guide-modal."""

GUIDE_SCRIPT: str = r"""
function setGuideTab(name) {
  const modal = document.getElementById("guide-modal");
  if (!modal) { return; }
  modal.querySelectorAll("[data-guide-tab]").forEach((btn) => {
    const active = btn.getAttribute("data-guide-tab") === name;
    btn.setAttribute("aria-selected", active ? "true" : "false");
    btn.tabIndex = active ? 0 : -1;
  });
  ["shortcuts", "chat", "library", "privacy"].forEach((id) => {
    const panel = document.getElementById("guide-panel-" + id);
    if (panel) { panel.hidden = id !== name; }
  });
}

function bindGuideUX() {
  const modal = document.getElementById("guide-modal");
  const tablist = document.getElementById("guide-tabs");
  if (tablist) {
    tablist.querySelectorAll("[data-guide-tab]").forEach((btn) => {
      btn.addEventListener("click", () => setGuideTab(btn.getAttribute("data-guide-tab") || "shortcuts"));
    });
    if (typeof bindRovingTablist === "function") {
      bindRovingTablist(tablist, (btn) => setGuideTab(btn.getAttribute("data-guide-tab") || "shortcuts"));
    }
  }
  const settingsGuideBtn = document.getElementById("settings-open-guide-btn");
  if (settingsGuideBtn) {
    settingsGuideBtn.addEventListener("click", () => {
      const settingsModal = document.getElementById("settings-modal");
      if (settingsModal && settingsModal.open) { settingsModal.close(); }
      if (typeof openQuickGuide === "function") { openQuickGuide(); }
    });
  }
  if (modal) {
    modal.querySelectorAll("[data-guide-jump]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const target = btn.getAttribute("data-guide-jump");
        modal.close();
        if (target === "onboarding" && typeof openOnboardingModal === "function") { openOnboardingModal(); }
        else if (target === "agents" && typeof openAgentsModal === "function") { openAgentsModal(); }
        else if (target === "formats" && typeof openFormatStudioModal === "function") { openFormatStudioModal(); }
        else if (target === "settings") {
          const sm = document.getElementById("settings-modal");
          if (sm && !sm.open) { sm.showModal(); }
        }
      });
    });
  }
  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "/") {
      e.preventDefault();
      if (modal && modal.open) { modal.close(); }
      else if (typeof openQuickGuide === "function") { openQuickGuide(); }
      return;
    }
    if (e.key === "?" && !e.metaKey && !e.ctrlKey && !e.altKey) {
      const tag = (document.activeElement && document.activeElement.tagName || "").toUpperCase();
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || (document.activeElement && document.activeElement.isContentEditable)) { return; }
      if (document.querySelector("dialog[open]")) { return; }
      e.preventDefault();
      if (typeof openQuickGuide === "function") { openQuickGuide(); }
    }
  });
}
"""
