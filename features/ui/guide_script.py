"""Interactive tab navigation, OS-aware shortcut label, and quick-jump actions for #guide-modal."""

GUIDE_SCRIPT: str = r"""
function setGuideTab(name) {
  const modal = document.getElementById("guide-modal");
  if (!modal) { return; }
  const target = ["chat", "library", "privacy"].includes(name) ? name : "chat";
  modal.querySelectorAll("[data-guide-tab]").forEach((btn) => {
    const active = btn.getAttribute("data-guide-tab") === target;
    btn.setAttribute("aria-selected", active ? "true" : "false");
    btn.tabIndex = active ? 0 : -1;
  });
  ["chat", "library", "privacy"].forEach((id) => {
    const panel = document.getElementById("guide-panel-" + id);
    if (panel) { panel.hidden = id !== target; }
  });
}

function bindGuideUX() {
  const modal = document.getElementById("guide-modal");
  const tablist = document.getElementById("guide-tabs");
  if (!/mac|iphone|ipad/i.test(navigator.platform || navigator.userAgent || "")) {
    [["guide-kbd-search", "Ctrl+K"], ["guide-kbd-files", "Ctrl+P"], ["guide-kbd-copilot", "Ctrl+J"], ["guide-kbd-save", "Ctrl+S"]].forEach(function ([id, txt]) {
      const el = document.getElementById(id); if (el) { el.textContent = txt; }
    });
  }
  if (tablist) {
    tablist.querySelectorAll("[data-guide-tab]").forEach((btn) => {
      btn.addEventListener("click", () => setGuideTab(btn.getAttribute("data-guide-tab") || "chat"));
    });
    if (typeof bindRovingTablist === "function") {
      bindRovingTablist("#guide-tabs [data-guide-tab]", (btn) => setGuideTab(btn.getAttribute("data-guide-tab") || "chat"));
    }
  }
  const openGuide = () => {
    setGuideTab("chat");
    if (typeof openGuideModal === "function") { openGuideModal(); }
    else if (modal && !modal.open) { modal.showModal(); }
  };
  const settingsGuideBtn = document.getElementById("settings-open-guide-btn");
  if (settingsGuideBtn) {
    settingsGuideBtn.addEventListener("click", () => {
      const settingsModal = document.getElementById("settings-modal");
      if (settingsModal && settingsModal.open) { settingsModal.close(); }
      openGuide();
    });
  }
  if (modal) {
    modal.querySelectorAll("[data-guide-jump]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const target = btn.getAttribute("data-guide-jump");
        modal.close();
        if (target === "onboarding" && typeof openOnboardingWizard === "function") { openOnboardingWizard(1); }
        else if (target === "agents" && typeof openAgentStudio === "function") { openAgentStudio("roster"); }
        else if (target === "formats" && typeof openFormatStudio === "function") { openFormatStudio("browse"); }
        else if (target === "settings" && typeof openSettings === "function") { openSettings("workspace"); }
      });
    });
  }
}
"""
