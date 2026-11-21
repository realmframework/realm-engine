"""Skippable 4-step Welcome Setup Tour controller."""

ONBOARDING_SCRIPT: str = r"""
let onboardingStep = 1;
const ONBOARDING_TOTAL = 4;

function renderOnboardingSummary() {
  const box = document.getElementById("onboarding-summary"); if (!box) { return; }
  const langNames = { en: "English", de: "Deutsch", es: "Español" };
  const titleVal = (document.getElementById("onboarding-title") && document.getElementById("onboarding-title").value.trim()) || "My Knowledge Base";
  const radio = document.querySelector('input[name="onboarding_run_mode"]:checked');
  const mode = radio ? radio.value : "local";
  const modeLabel = mode === "cloud" ? t("ob_sum_cloud") : mode === "search" ? t("ob_sum_search") : t("ob_sum_local");
  const themeMode = (workspaceConfig && workspaceConfig.theme_mode) || localStorage.getItem("color-scheme") || "system";
  const themeLabel = themeMode === "dark" ? t("theme_dark") : (themeMode === "light" ? t("theme_light") : t("theme_system"));
  box.innerHTML = [
    [t("sum_lang"), langNames[activeLanguage] || "English"],
    [t("sum_workspace"), titleVal],
    [t("sum_theme"), themeLabel],
    [t("sum_ai"), modeLabel]
  ].map(function (row) {
    return "<div class='flex items-center justify-between py-1.5 border-b border-[rgba(238,242,248,0.08)] last:border-0 text-xs'><span class='text-[#738196]'>" + escapeHtml(row[0]) + "</span><span class='text-[#EEF2F8] font-medium'>" + escapeHtml(row[1]) + "</span></div>";
  }).join("");
}
function showOnboardingStep(step) {
  onboardingStep = Math.max(1, Math.min(ONBOARDING_TOTAL, step));
  for (let i = 1; i <= ONBOARDING_TOTAL; i++) {
    const panel = document.getElementById("onboarding-step-" + i);
    if (panel) { panel.hidden = i !== onboardingStep; }
  }
  const badge = document.getElementById("onboarding-step-badge");
  if (badge) { badge.textContent = onboardingStep + " / " + ONBOARDING_TOTAL; }
  document.querySelectorAll("[data-onboarding-dot]").forEach(function (dot) {
    const idx = Number(dot.getAttribute("data-onboarding-dot"));
    dot.className = "h-2 rounded-full transition-all " + (idx === onboardingStep ? "w-6 bg-[#4BB8E8]" : "w-2 bg-[rgba(238,242,248,0.22)]");
  });
  const backBtn = document.getElementById("onboarding-back-btn");
  const nextBtn = document.getElementById("onboarding-next-btn");
  const finalActions = document.getElementById("onboarding-final-actions");
  if (backBtn) { backBtn.hidden = onboardingStep === 1; }
  if (nextBtn) { nextBtn.hidden = onboardingStep === ONBOARDING_TOTAL; }
  if (finalActions) { finalActions.hidden = onboardingStep !== ONBOARDING_TOTAL; }
  if (onboardingStep === ONBOARDING_TOTAL) { renderOnboardingSummary(); }
}
function openOnboardingWizard(step) {
  showOnboardingStep(step || 1);
  if (!onboardingModal.open) { onboardingModal.showModal(); }
}
function skipOnboardingWizard() {
  try { localStorage.setItem("onboarded", "1"); } catch (_e) {}
  if (onboardingModal.open) { onboardingModal.close(); }
}
function bindOnboardingTour() {
  const backBtn = document.getElementById("onboarding-back-btn");
  const nextBtn = document.getElementById("onboarding-next-btn");
  const skipBtn = document.getElementById("onboarding-skip-btn");
  if (backBtn) { backBtn.addEventListener("click", function () { showOnboardingStep(onboardingStep - 1); }); }
  if (nextBtn) { nextBtn.addEventListener("click", function () { showOnboardingStep(onboardingStep + 1); }); }
  if (skipBtn) { skipBtn.addEventListener("click", skipOnboardingWizard); }
  document.querySelectorAll("[data-onboarding-dot]").forEach(function (dot) {
    dot.addEventListener("click", function () { showOnboardingStep(Number(dot.getAttribute("data-onboarding-dot"))); });
  });
  showOnboardingStep(1);
}
"""
