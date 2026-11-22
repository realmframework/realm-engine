"""Appearance controls: System/Dark/Light scheme, dual-tone palettes, custom logo."""

THEME_SCRIPT: str = r"""
const THEME_PRESETS = [
  { id: "realm", name: "Realm", accent: "#4BB8E8", glow: "#6366F1" },
  { id: "lisbeth", name: "Lisbeth", accent: "#A855F7", glow: "#22D3EE" },
  { id: "salander", name: "Salander", accent: "#F43F5E", glow: "#9333EA" },
  { id: "wasp", name: "Wasp", accent: "#F59E0B", glow: "#FACC15" },
  { id: "plague", name: "Plague", accent: "#10B981", glow: "#06B6D4" },
  { id: "blomkvist", name: "Blomkvist", accent: "#3B82F6", glow: "#2DD4BF" },
  { id: "millennium", name: "Millennium", accent: "#F97316", glow: "#EC4899" },
  { id: "erika", name: "Erika", accent: "#EC4899", glow: "#818CF8" },
  { id: "harriet", name: "Harriet", accent: "#38BDF8", glow: "#34D399" },
  { id: "milton", name: "Milton", accent: "#60A5FA", glow: "#0EA5E9" },
  { id: "dragon", name: "Dragon", accent: "#EF4444", glow: "#F97316" },
  { id: "hacker", name: "Hacker", accent: "#84CC16", glow: "#10B981" },
  { id: "stieg", name: "Stieg", accent: "#818CF8", glow: "#4F46E5" },
  { id: "annika", name: "Annika", accent: "#D946EF", glow: "#F43F5E" },
  { id: "palmgren", name: "Palmgren", accent: "#14B8A6", glow: "#EAB308" }
];
const systemDarkQuery = window.matchMedia("(prefers-color-scheme: dark)");
let activeLogoUrl = "/static/logo-512.png";
let activeAgentLabel = "Saga";
let themeSaveTimer = null, pendingAppearancePatch = {}, appearanceSaveSeq = 0;

function activeLogoSrc() { return activeLogoUrl || "/static/logo-512.png"; }
function activeAgentName() {
  if (typeof activeAgentObj === "function") {
    const ag = activeAgentObj();
    if (ag && ag.name) { return ag.name; }
  }
  return (activeAgentLabel || "").trim() || "Saga";
}
function syncAgentNameUI(name) {
  activeAgentLabel = String(name || "").trim().slice(0, 40) || "Saga";
}
function hexToHsl(hex) {
  const clean = /^#[0-9a-f]{6}$/i.test(hex || "") ? hex : "#4BB8E8";
  const r = parseInt(clean.slice(1, 3), 16) / 255, g = parseInt(clean.slice(3, 5), 16) / 255, b = parseInt(clean.slice(5, 7), 16) / 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b), l = (max + min) / 2;
  let h = 0, s = 0;
  if (max !== min) {
    const d = max - min; s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    h = max === r ? ((g - b) / d + (g < b ? 6 : 0)) : max === g ? ((b - r) / d + 2) : ((r - g) / d + 4);
    h *= 60;
  }
  return [h, s, l];
}
function hslToHex(h, s, l) {
  const hue = ((h % 360) + 360) % 360, c = (1 - Math.abs(2 * l - 1)) * s, x = c * (1 - Math.abs((hue / 60) % 2 - 1)), m = l - c / 2;
  const [r, g, b] = hue < 60 ? [c, x, 0] : hue < 120 ? [x, c, 0] : hue < 180 ? [0, c, x] : hue < 240 ? [0, x, c] : hue < 300 ? [x, 0, c] : [c, 0, x];
  return "#" + [r + m, g + m, b + m].map(v => Math.round(Math.max(0, Math.min(1, v)) * 255).toString(16).padStart(2, "0")).join("").toUpperCase();
}
function computeHarmonicGlow(accentHex) {
  const [h, s, l] = hexToHsl(accentHex);
  return hslToHex(h + 48, Math.max(0.55, Math.min(0.92, s || 0.75)), Math.max(0.48, Math.min(0.68, l || 0.58)));
}
function applyTextOnAccentFallback(mode, accentHex) {
  if (typeof CSS !== "undefined" && CSS.supports && (CSS.supports("color", "contrast-color(red)") || CSS.supports("color", "color(from red xyz-d65 0 0 0)"))) {
    document.documentElement.style.removeProperty("--text-on-accent");
    return;
  }
  const isDark = mode === "dark" || (mode === "system" && systemDarkQuery.matches);
  const c = /^#[0-9a-f]{6}$/i.test(accentHex || "") ? accentHex : "#4BB8E8";
  const rgb = [1, 3, 5].map(function (i) { const v = parseInt(c.slice(i, i + 2), 16) / 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
  const lum = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
  const approx = isDark ? (lum * 0.88 + 0.12) : (lum * 0.25);
  document.documentElement.style.setProperty("--text-on-accent", approx > 0.179 ? "#04060F" : "#FFFFFF");
}
function applyThemeTokens(mode, accent, glow, persistLocal) {
  const safeMode = mode === "dark" || mode === "light" ? mode : "system";
  const safeAccent = /^#[0-9a-f]{6}$/i.test(accent || "") ? accent.toUpperCase() : "#4BB8E8";
  const safeGlow = /^#[0-9a-f]{6}$/i.test(glow || "") ? glow.toUpperCase() : "#6366F1";
  const meta = document.querySelector('meta[name="color-scheme"]');
  if (meta) { meta.setAttribute("content", safeMode === "system" ? "light dark" : safeMode); }
  document.documentElement.style.setProperty("--accent-seed", safeAccent);
  document.documentElement.style.setProperty("--accent-glow", safeGlow);
  applyTextOnAccentFallback(safeMode, safeAccent);
  if (persistLocal !== false) {
    if (safeMode === "system") { safeStorageRemove("color-scheme"); } else { safeStorageSet("color-scheme", safeMode); }
    safeStorageSet("realm_theme_accent", safeAccent);
    safeStorageSet("realm_theme_glow", safeGlow);
  }
  syncThemeControlsUI(safeMode, safeAccent, safeGlow);
  if (typeof refreshAmbientPalette === "function") { refreshAmbientPalette(); }
  if (typeof broadcastToEmbedFrames === "function") { broadcastToEmbedFrames({ type: "realm:sync-theme", mode: safeMode, accent: safeAccent, glow: safeGlow }); }
}
function syncThemeControlsUI(mode, accent, glow) {
  const sysNow = systemDarkQuery.matches ? t("theme_dark") : t("theme_light");
  document.querySelectorAll('[data-theme-mode="system"]').forEach(function (sysBtn) {
    sysBtn.textContent = t("theme_system") + " (" + sysNow + ")";
  });
  document.querySelectorAll("[data-theme-mode]").forEach(function (btn) {
    const active = btn.getAttribute("data-theme-mode") === mode;
    btn.setAttribute("aria-pressed", String(active));
    btn.className = "py-1.5 px-2.5 rounded-lg text-xs font-medium transition " + (active ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]");
  });
  const accIn = document.getElementById("theme-accent-picker"), glowIn = document.getElementById("theme-glow-picker");
  if (accIn && accIn.value.toUpperCase() !== accent) { accIn.value = accent; }
  if (glowIn && glowIn.value.toUpperCase() !== glow) { glowIn.value = glow; }
  const accHex = document.getElementById("theme-accent-hex"), glowHex = document.getElementById("theme-glow-hex");
  if (accHex) { accHex.textContent = accent; }
  if (glowHex) { glowHex.textContent = glow; }
  document.querySelectorAll("[data-theme-preset]").forEach(function (btn) {
    const active = (btn.dataset.accent || "").toUpperCase() === accent && (btn.dataset.glow || "").toUpperCase() === glow;
    btn.setAttribute("aria-pressed", String(active));
    btn.classList.toggle("border-[#4BB8E8]", active);
  });
}
function persistAppearancePatch(patch) {
  pendingAppearancePatch = Object.assign({}, pendingAppearancePatch, patch || {});
  clearTimeout(themeSaveTimer);
  themeSaveTimer = setTimeout(async function () {
    const body = pendingAppearancePatch;
    pendingAppearancePatch = {};
    const version = areaVersion, seq = ++appearanceSaveSeq;
    try {
      const res = await areaFetch("/api/workspace/appearance", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      if (res.ok && version === areaVersion && seq === appearanceSaveSeq) { const data = await safeJson(res); if (data && data.config) { workspaceConfig = data.config; } }
    } catch (_e) {}
  }, 150);
}
function persistThemeWorkspace(mode, accent, glow) {
  persistAppearancePatch({ theme_mode: mode, theme_accent: accent, theme_glow: glow });
}
function applyLogoUrl(url, isCustom) {
  activeLogoUrl = url || "/static/logo-512.png";
  for (const id of ["hero-logo", "onboarding-logo", "settings-logo-preview", "onboarding-logo-preview"]) {
    const img = document.getElementById(id); if (img) { img.src = activeLogoUrl; }
  }
  const resetBtn = document.getElementById("reset-logo-btn");
  if (resetBtn) { resetBtn.hidden = !isCustom; }
  const iconLink = document.querySelector('link[rel="icon"][sizes="32x32"]');
  if (iconLink) { iconLink.href = isCustom ? activeLogoUrl : "/static/favicon-32.png"; }
}
async function loadWorkspaceLogo() {
  try {
    const res = await areaFetch("/api/workspace/logo/status");
    if (res.ok) { const data = await safeJson(res); applyLogoUrl(data.url, Boolean(data.custom)); }
  } catch (_e) {}
}
async function uploadCustomLogo(file) {
  const status = document.getElementById("logo-upload-status");
  if (!file) { return; }
  if (status) { status.textContent = "Uploading logo…"; }
  const form = new FormData(); form.append("file", file);
  try {
    const res = await areaFetch("/api/workspace/logo", { method: "POST", body: form });
    const data = await safeJson(res);
    if (!res.ok) { throw new Error(data.detail || "Could not upload logo."); }
    applyLogoUrl(data.url, true);
    if (status) { status.textContent = "Custom logo saved."; }
  } catch (err) { if (status) { status.textContent = err.message || "Could not upload logo."; } }
}
async function resetCustomLogo() {
  const status = document.getElementById("logo-upload-status");
  try {
    const res = await areaFetch("/api/workspace/logo", { method: "DELETE" });
    const data = await safeJson(res);
    if (res.ok) { applyLogoUrl(data.url, false); if (status) { status.textContent = "Restored default REALM logo."; } }
  } catch (_e) {}
}
function syncThemeFromWorkspace(cfg) {
  const mode = (cfg && cfg.theme_mode) || safeStorageGet("color-scheme") || "system";
  const accent = (cfg && cfg.theme_accent) || safeStorageGet("realm_theme_accent") || "#4BB8E8";
  const glow = (cfg && cfg.theme_glow) || safeStorageGet("realm_theme_glow") || "#6366F1";
  applyThemeTokens(mode, accent, glow, true);
  if (typeof setAmbientEffects === "function" && cfg && typeof cfg.ambient_effects === "boolean") {
    setAmbientEffects(cfg.ambient_effects, true);
  }
  if (typeof applyLanguage === "function" && cfg && cfg.language) {
    applyLanguage(cfg.language, true);
  }
  syncAgentNameUI((cfg && cfg.agent_name) || "Saga");
  if (typeof defaultAgentId !== "undefined" && cfg && cfg.active_agent) {
    defaultAgentId = cfg.active_agent;
    if (!currentChatId) { activeAgentId = defaultAgentId; }
    if (typeof syncAgentPalette !== "undefined") { syncAgentPalette = cfg.sync_agent_palette !== false; }
    if (typeof syncActiveAgentBadge === "function") { syncActiveAgentBadge(); }
    if (currentChatId && typeof applyPaletteForAgent === "function" && typeof activeAgentObj === "function") { applyPaletteForAgent(activeAgentObj(), false); }
  }
  if (typeof syncWebSearchUI === "function") { syncWebSearchUI(cfg || {}); }
}
function renderPresetBars() {
  const markup = THEME_PRESETS.map(function (p) {
    return "<button type='button' data-theme-preset='" + p.id + "' data-accent='" + p.accent + "' data-glow='" + p.glow
      + "' aria-pressed='false' class='flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[#04060F] border border-[rgba(238,242,248,0.12)] hover:border-[#4BB8E8] text-xs text-[#EEF2F8] transition'>"
      + "<span aria-hidden='true' class='theme-swatch w-3.5 h-3.5 rounded-full shrink-0' style='background:linear-gradient(135deg," + p.accent + "," + p.glow + ")'></span>"
      + "<span>" + escapeHtml(p.name) + "</span></button>";
  }).join("");
  for (const barId of ["theme-presets-bar", "onboarding-presets-bar"]) {
    const bar = document.getElementById(barId); if (!bar) { continue; }
    bar.innerHTML = markup;
    bar.querySelectorAll("[data-theme-preset]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const mode = (workspaceConfig && workspaceConfig.theme_mode) || safeStorageGet("color-scheme") || "system";
        applyThemeTokens(mode, btn.dataset.accent, btn.dataset.glow, true);
        persistThemeWorkspace(mode, btn.dataset.accent, btn.dataset.glow);
      });
    });
  }
}
function bindAppearanceControls() {
  renderPresetBars();
  document.querySelectorAll("[data-theme-mode]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const mode = btn.getAttribute("data-theme-mode") || "system";
      const accent = document.getElementById("theme-accent-picker").value.toUpperCase();
      const glow = document.getElementById("theme-glow-picker").value.toUpperCase();
      applyThemeTokens(mode, accent, glow, true);
      persistThemeWorkspace(mode, accent, glow);
    });
  });
  const accIn = document.getElementById("theme-accent-picker"), glowIn = document.getElementById("theme-glow-picker");
  if (accIn) {
    accIn.addEventListener("input", function () {
      const mode = (workspaceConfig && workspaceConfig.theme_mode) || safeStorageGet("color-scheme") || "system";
      const accent = accIn.value.toUpperCase(), glow = computeHarmonicGlow(accent);
      applyThemeTokens(mode, accent, glow, true);
      persistThemeWorkspace(mode, accent, glow);
    });
  }
  if (glowIn) {
    glowIn.addEventListener("input", function () {
      const mode = (workspaceConfig && workspaceConfig.theme_mode) || safeStorageGet("color-scheme") || "system";
      const accent = accIn ? accIn.value.toUpperCase() : "#4BB8E8", glow = glowIn.value.toUpperCase();
      applyThemeTokens(mode, accent, glow, true);
      persistThemeWorkspace(mode, accent, glow);
    });
  }
  for (const toggleId of ["theme-ambient-toggle", "onboarding-ambient-toggle"]) {
    const chk = document.getElementById(toggleId);
    if (chk) {
      chk.addEventListener("change", function () {
        if (typeof setAmbientEffects === "function") { setAmbientEffects(chk.checked, true); }
        persistAppearancePatch({ ambient_effects: Boolean(chk.checked) });
      });
    }
  }
  const resetThemeBtn = document.getElementById("reset-theme-btn");
  if (resetThemeBtn) {
    resetThemeBtn.addEventListener("click", function () {
      applyThemeTokens("system", "#4BB8E8", "#6366F1", true);
      if (typeof setAmbientEffects === "function") { setAmbientEffects(true, true); }
      persistAppearancePatch({ theme_mode: "system", theme_accent: "#4BB8E8", theme_glow: "#6366F1", ambient_effects: true });
    });
  }
  const resetAppearanceBtn = document.getElementById("reset-appearance-btn");
  if (resetAppearanceBtn) {
    resetAppearanceBtn.addEventListener("click", async function () {
      applyThemeTokens("system", "#4BB8E8", "#6366F1", true);
      syncAgentNameUI("Saga");
      if (typeof currentTurns !== "undefined" && currentTurns.length && typeof renderChatStream === "function") { renderChatStream(); }
      if (typeof setAmbientEffects === "function") { setAmbientEffects(true, true); }
      if (typeof applyReadingComfort === "function") { applyReadingComfort({ reading_font: "default", reading_scale: "md", reading_width: "standard", high_contrast_focus: false, reduce_motion: false }, true); }
      persistAppearancePatch({ theme_mode: "system", theme_accent: "#4BB8E8", theme_glow: "#6366F1", ambient_effects: true, agent_name: "Saga", reading_font: "default", reading_scale: "md", reading_width: "standard", high_contrast_focus: false, reduce_motion: false });
      await resetCustomLogo();
    });
  }
  const resetAllBtn = document.getElementById("reset-all-settings-btn");
  if (resetAllBtn) {
    resetAllBtn.addEventListener("click", async function () {
      const ok = await confirmDeletion(t("cf_reset_all_t"), t("cf_reset_all_m"), t("cf_reset_all_btn"));
      if (!ok) { return; }
      const status = document.getElementById("reset-all-status");
      resetAllBtn.disabled = true;
      try {
        const res = await areaFetch("/api/workspace/reset-defaults", { method: "POST" });
        const data = await safeJson(res);
        if (!res.ok) { throw new Error(data.detail || "Could not reset settings."); }
        for (const k of ["color-scheme", "realm_theme_accent", "realm_theme_glow", "realm_ambient_effects", "realm_lang", "preferred_local_model"]) { safeStorageRemove(k); }
        if (typeof resetReadingComfortLocal === "function") { resetReadingComfortLocal(); }
        ragConfig = { retrieval_mode: "hybrid", top_k: 5, rrf_k: 60, temperature: 0.2 }; syncRagStudioUI();
        applyLogoUrl(data.logo_url || "/static/logo-512.png", false);
        await loadWorkspace(); await loadModels(); await refreshBudget();
        if (status) { status.textContent = "All settings restored to REALM defaults. Documents and chats were not touched."; }
      } catch (err) { if (status) { status.textContent = err.message || "Could not reset settings."; } }
      finally { resetAllBtn.disabled = false; }
    });
  }
  for (const inputId of ["workspace-logo-input", "onboarding-logo-input"]) {
    const logoInput = document.getElementById(inputId);
    if (logoInput) {
      logoInput.addEventListener("change", function () {
        if (logoInput.files && logoInput.files[0]) { uploadCustomLogo(logoInput.files[0]); logoInput.value = ""; }
      });
    }
  }
  const resetLogoBtn = document.getElementById("reset-logo-btn");
  if (resetLogoBtn) { resetLogoBtn.addEventListener("click", resetCustomLogo); }
  systemDarkQuery.addEventListener("change", function () {
    const mode = (workspaceConfig && workspaceConfig.theme_mode) || safeStorageGet("color-scheme") || "system";
    const accent = document.getElementById("theme-accent-picker") ? document.getElementById("theme-accent-picker").value.toUpperCase() : "#4BB8E8";
    const glow = document.getElementById("theme-glow-picker") ? document.getElementById("theme-glow-picker").value.toUpperCase() : "#6366F1";
    applyTextOnAccentFallback(mode, accent);
    syncThemeControlsUI(mode, accent, glow);
    if (typeof refreshAmbientPalette === "function") { refreshAmbientPalette(); }
  });
  window.addEventListener("storage", function (e) {
    if (e.key === "color-scheme" || e.key === "realm_theme_accent" || e.key === "realm_theme_glow") {
      applyThemeTokens(safeStorageGet("color-scheme") || "system", safeStorageGet("realm_theme_accent") || "#4BB8E8", safeStorageGet("realm_theme_glow") || "#6366F1", false);
    }
    if (e.key === "realm_lang" && typeof applyLanguage === "function") { applyLanguage(safeStorageGet("realm_lang") || "en", false); }
  });
  loadWorkspaceLogo();
}
"""
