"""Accessibility & Reading Comfort controller: fonts, scale, measure, high-contrast focus, reduced motion."""

COMFORT_SCRIPT: str = r"""
const ROOT_FONT_SCALES = { sm: "14.5px", md: "16px", lg: "18px", xl: "20px" };
const READING_SCALES = { sm: "0.95rem", md: "1rem", lg: "1.05rem", xl: "1.1rem" };
const READING_WIDTHS = { narrow: "40rem", standard: "48rem", wide: "62rem" };
let readingComfort = { reading_font: "default", reading_scale: "md", reading_width: "standard", high_contrast_focus: false, reduce_motion: false };
let activeSlashRecipe = null;
const SUPPORTS_FIELD_SIZING = typeof CSS !== "undefined" && typeof CSS.supports === "function" && CSS.supports("field-sizing", "content");

function setActiveSlashRecipe(cmd) {
  activeSlashRecipe = cmd ? { slug: cmd.slug, chip: cmd.chip || cmd.label, prefix: cmd.prefix || "" } : null;
  const chip = document.getElementById("recipe-chip"), lbl = document.getElementById("recipe-chip-label");
  if (!chip || !lbl) { return; }
  if (activeSlashRecipe) {
    lbl.textContent = activeSlashRecipe.chip;
    chip.hidden = false;
  } else {
    lbl.textContent = "";
    chip.hidden = true;
  }
}

function clearActiveSlashRecipe() { setActiveSlashRecipe(null); }

function consumeActiveSlashRecipe() {
  const rec = activeSlashRecipe;
  clearActiveSlashRecipe();
  return rec;
}

const ATTACH_CLIP_SVG = "<svg aria-hidden='true' class='w-3.5 h-3.5 shrink-0 text-[#4BB8E8]' fill='none' stroke='currentColor' stroke-width='1.5' viewBox='0 0 24 24'><path stroke-linecap='round' stroke-linejoin='round' d='m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48'/></svg>";
const CHIP_X_SVG = "<svg aria-hidden='true' width='11' height='11' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.5' stroke-linecap='round'><path d='m6 6 12 12M18 6 6 18'/></svg>";

function renderAttachedChips() {
  const host = document.getElementById("attached-chips");
  if (!host) { return; }
  const notes = (typeof activeAttachedNotes !== "undefined" && Array.isArray(activeAttachedNotes)) ? activeAttachedNotes : [];
  if (!notes.length) {
    host.innerHTML = "";
    host.hidden = true;
    autoResizeQuery();
    return;
  }
  host.innerHTML = notes.map(function (n, idx) {
    const label = String((n && n.name) || "Attachment");
    return "<span class='attached-pill' title='" + escapeHtml(label) + "'>" + ATTACH_CLIP_SVG
      + "<span class='attached-pill-name'>" + escapeHtml(label) + "</span>"
      + "<button type='button' data-pill-detach='" + idx + "' class='attached-pill-del' aria-label='" + escapeHtml(t("attach_remove_aria", { name: label })) + "'>" + CHIP_X_SVG + "</button></span>";
  }).join("");
  host.hidden = false;
  host.querySelectorAll("[data-pill-detach]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const idx = Number(btn.getAttribute("data-pill-detach") || 0);
      if (typeof detachChatNote === "function") { detachChatNote(idx); }
    });
  });
  autoResizeQuery();
}

function openGuideModal() {
  const modal = document.getElementById("guide-modal");
  if (!modal) { return; }
  if (modal.open) { modal.close(); return; }
  if (typeof setGuideTab === "function") { setGuideTab("chat"); }
  modal.showModal();
}

function autoResizeQuery() {
  const ta = document.getElementById("query"), box = document.getElementById("prompt-container");
  if (!ta) { return; }
  if (!SUPPORTS_FIELD_SIZING) {
    ta.style.height = "auto";
    ta.style.height = Math.min(Math.max(ta.scrollHeight, 28), 168) + "px";
  }
  const multi = Boolean(ta.value.includes("\n") || ta.scrollHeight > 44);
  if (box) { box.classList.toggle("is-multiline", multi); }
}

function prefersReducedMotion() {
  return Boolean(readingComfort.reduce_motion)
    || document.documentElement.classList.contains("realm-reduce-motion")
    || window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function applyReadingComfort(cfg, persistLocal) {
  const font = ["default", "legible", "dyslexic"].includes(cfg && cfg.reading_font) ? cfg.reading_font : "default";
  const scale = ["sm", "md", "lg", "xl"].includes(cfg && cfg.reading_scale) ? cfg.reading_scale : "md";
  const width = ["narrow", "standard", "wide"].includes(cfg && cfg.reading_width) ? cfg.reading_width : "standard";
  const hc = Boolean(cfg && cfg.high_contrast_focus);
  const rm = Boolean(cfg && cfg.reduce_motion);
  readingComfort = { reading_font: font, reading_scale: scale, reading_width: width, high_contrast_focus: hc, reduce_motion: rm };
  const root = document.documentElement;
  root.classList.toggle("realm-legible", font === "legible");
  root.classList.toggle("realm-dyslexic", font === "dyslexic");
  root.classList.toggle("realm-hc-focus", hc);
  root.classList.toggle("realm-reduce-motion", rm);
  root.style.fontSize = ROOT_FONT_SCALES[scale] || "16px";
  root.style.setProperty("--reading-size", READING_SCALES[scale] || "1rem");
  root.style.setProperty("--reading-width", READING_WIDTHS[width] || "48rem");
  if (persistLocal !== false) {
    safeStorageSet("realm_reading_font", font);
    safeStorageSet("realm_reading_size", scale);
    safeStorageSet("realm_reading_width", width);
    safeStorageSet("realm_hc_focus", hc ? "1" : "0");
    safeStorageSet("realm_reduce_motion", rm ? "1" : "0");
  }
  syncComfortControlsUI();
  if (typeof syncAmbientMotion === "function") { syncAmbientMotion(); }
  else if (typeof setAmbientEffects === "function") {
    setAmbientEffects(!rm && (workspaceConfig.ambient_effects !== false), false);
  }
  if (typeof window.syncGraphMotion === "function") { window.syncGraphMotion(); }
}

function syncComfortControlsUI() {
  document.querySelectorAll("[data-reading-font]").forEach(function (btn) {
    const on = btn.getAttribute("data-reading-font") === readingComfort.reading_font;
    btn.setAttribute("aria-pressed", String(on));
    btn.className = "py-1.5 px-2 rounded-lg text-xs font-medium transition " + (on ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]");
  });
  document.querySelectorAll("[data-reading-scale]").forEach(function (btn) {
    const on = btn.getAttribute("data-reading-scale") === readingComfort.reading_scale;
    btn.setAttribute("aria-pressed", String(on));
    btn.className = "py-1.5 rounded-lg text-xs font-medium transition " + (on ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]");
  });
  document.querySelectorAll("[data-reading-width]").forEach(function (btn) {
    const on = btn.getAttribute("data-reading-width") === readingComfort.reading_width;
    btn.setAttribute("aria-pressed", String(on));
    btn.className = "py-1.5 px-1.5 rounded-lg text-xs font-medium transition " + (on ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]");
  });
  const hcEl = document.getElementById("a11y-hc-focus-toggle");
  if (hcEl) { hcEl.checked = readingComfort.high_contrast_focus; }
  const rmEl = document.getElementById("a11y-reduce-motion-toggle");
  if (rmEl) { rmEl.checked = readingComfort.reduce_motion; }
}

function updateReadingComfort(patch) {
  const next = Object.assign({}, readingComfort, patch);
  applyReadingComfort(next, true);
  if (typeof workspaceConfig === "object" && workspaceConfig) { Object.assign(workspaceConfig, patch); }
  if (typeof persistAppearancePatch === "function") { persistAppearancePatch(patch); }
}

function resetReadingComfortLocal() {
  for (const k of ["realm_reading_font", "realm_reading_size", "realm_reading_width", "realm_hc_focus", "realm_reduce_motion"]) { safeStorageRemove(k); }
  applyReadingComfort({ reading_font: "default", reading_scale: "md", reading_width: "standard", high_contrast_focus: false, reduce_motion: false }, false);
}

function bindComfortControls() {
  applyReadingComfort({
    reading_font: safeStorageGet("realm_reading_font") || "default",
    reading_scale: safeStorageGet("realm_reading_size") || "md",
    reading_width: safeStorageGet("realm_reading_width") || "standard",
    high_contrast_focus: safeStorageGet("realm_hc_focus") === "1",
    reduce_motion: safeStorageGet("realm_reduce_motion") === "1",
  }, false);
  document.querySelectorAll("[data-reading-font]").forEach(function (btn) {
    btn.addEventListener("click", function () { updateReadingComfort({ reading_font: btn.getAttribute("data-reading-font") || "default" }); });
  });
  document.querySelectorAll("[data-reading-scale]").forEach(function (btn) {
    btn.addEventListener("click", function () { updateReadingComfort({ reading_scale: btn.getAttribute("data-reading-scale") || "md" }); });
  });
  document.querySelectorAll("[data-reading-width]").forEach(function (btn) {
    btn.addEventListener("click", function () { updateReadingComfort({ reading_width: btn.getAttribute("data-reading-width") || "standard" }); });
  });
  const hcEl = document.getElementById("a11y-hc-focus-toggle");
  if (hcEl) { hcEl.addEventListener("change", function () { updateReadingComfort({ high_contrast_focus: Boolean(hcEl.checked) }); }); }
  const rmEl = document.getElementById("a11y-reduce-motion-toggle");
  if (rmEl) { rmEl.addEventListener("change", function () { updateReadingComfort({ reduce_motion: Boolean(rmEl.checked) }); }); }
  const gOpen = document.getElementById("open-guide-btn"), gClose = document.getElementById("close-guide-modal"), gModal = document.getElementById("guide-modal");
  if (gOpen) { gOpen.addEventListener("click", openGuideModal); }
  if (gClose && gModal) { gClose.addEventListener("click", function () { gModal.close(); }); }
}
"""
