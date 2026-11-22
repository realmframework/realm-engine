"""App-Wide Unsaved Changes Guard: Shared Save/Discard/Keep-Editing Prompt for File Tabs, Modals & Editors."""

UNSAVED_GUARD_SCRIPT: str = r"""
const UG_DIALOGS = {
  "save-guide-modal": { form: "save-guide-form" },
  "work-task-modal": { form: "wb-task-form" },
  "work-project-modal": { form: "wb-project-form" },
  "work-event-modal": { form: "wb-event-form" },
  "work-extract-modal": { form: "wb-extract-form" },
  "goal-season-modal": { form: "gs-form" },
  "impact-entry-modal": { form: "ie-form" },
  "agent-studio-modal": { form: "agent-editor-form", requireVisible: true },
  "format-studio-modal": { form: "custom-format-form", requireVisible: true },
  "area-modal": { form: "new-area-form" },
};
let ugPromptBusy = false;

function confirmUnsavedChanges(opts) {
  const o = opts || {};
  const dialog = document.getElementById("unsaved-modal");
  if (!dialog || dialog.open || ugPromptBusy) { return Promise.resolve("cancel"); }
  ugPromptBusy = true;
  const titleEl = document.getElementById("unsaved-title");
  const msgEl = document.getElementById("unsaved-message");
  const saveBtn = document.getElementById("unsaved-save-btn");
  if (titleEl) { titleEl.textContent = o.title || t("unsaved_t"); }
  if (msgEl) { msgEl.textContent = o.message || (o.name ? t("unsaved_m", { name: o.name }) : t("unsaved_m_generic")); }
  if (saveBtn) { saveBtn.hidden = o.canSave === false; }
  dialog.returnValue = "";
  return new Promise(function (resolve) {
    dialog.addEventListener("close", function () {
      const rv = dialog.returnValue || "cancel";
      dialog.returnValue = "";
      ugPromptBusy = false;
      resolve(rv === "save" || rv === "discard" ? rv : "cancel");
    }, { once: true });
    dialog.showModal();
  });
}

function ugSerializeForm(form) {
  if (!form) { return ""; }
  const out = [];
  form.querySelectorAll("input, textarea, select").forEach(function (el) {
    if (el.type === "hidden" || el.type === "file") { return; }
    const key = el.id || el.name || "";
    const val = (el.type === "checkbox" || el.type === "radio") ? (el.checked ? "1" : "0") : String(el.value || "");
    out.push(key + "=" + val);
  });
  return out.join("\x1f");
}

function ugSnapshotDialog(dlg) {
  if (!dlg) { return; }
  const spec = UG_DIALOGS[dlg.id];
  const form = spec ? document.getElementById(spec.form) : null;
  dlg.dataset.ugDirty = "0";
  dlg.dataset.ugSnap = form ? ugSerializeForm(form) : "";
}

function ugDialogFormIfActive(dlg) {
  const spec = dlg && UG_DIALOGS[dlg.id];
  if (!spec) { return null; }
  const form = document.getElementById(spec.form);
  if (!form) { return null; }
  if (spec.requireVisible && form.hidden) { return null; }
  return form;
}

function ugIsDialogDirty(dlg) {
  if (!dlg || !dlg.open) { return false; }
  const form = ugDialogFormIfActive(dlg);
  if (!form) { return false; }
  if (dlg.dataset.ugDirty !== "1") { return false; }
  if (dlg.dataset.ugSnap !== undefined && ugSerializeForm(form) === dlg.dataset.ugSnap) {
    dlg.dataset.ugDirty = "0";
    return false;
  }
  return true;
}

async function requestSafeCloseDialog(dlg) {
  if (!dlg || !dlg.open) { return true; }
  if (!ugIsDialogDirty(dlg)) { dlg.close(); return true; }
  const form = ugDialogFormIfActive(dlg);
  const heading = dlg.querySelector("h2, h1");
  const choice = await confirmUnsavedChanges({
    name: heading ? (heading.textContent || "").trim() : "",
    canSave: Boolean(form && typeof form.requestSubmit === "function"),
  });
  if (choice === "discard") {
    dlg.dataset.ugDirty = "0";
    dlg.close();
    return true;
  }
  if (choice === "save" && form) {
    if (typeof form.requestSubmit === "function") { form.requestSubmit(); }
    else { form.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true })); }
  }
  return false;
}

function ugHasAnyUnsavedWork() {
  if (typeof centerChatTabs !== "undefined" && Array.isArray(centerChatTabs) && centerChatTabs.some(function (tb) { return tb.kind === "file" && tb.dirty; })) { return true; }
  if (typeof readerEditMode !== "undefined" && readerEditMode) {
    const ta = document.getElementById("guide-md-textarea");
    if (ta && typeof readerRawDraft === "string" && ta.value !== readerRawDraft) { return true; }
  }
  for (const id of Object.keys(UG_DIALOGS)) {
    const dlg = document.getElementById(id);
    if (ugIsDialogDirty(dlg)) { return true; }
  }
  return false;
}

function bindUnsavedGuardUX() {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) { return; }
  Object.keys(UG_DIALOGS).forEach(function (id) {
    const dlg = document.getElementById(id);
    const spec = UG_DIALOGS[id];
    const form = spec ? document.getElementById(spec.form) : null;
    if (!dlg || !form) { return; }
    const obs = new MutationObserver(function () {
      if (dlg.open) {
        dlg.dataset.ugDirty = "0";
        requestAnimationFrame(function () { if (dlg.open) { ugSnapshotDialog(dlg); } });
      } else {
        dlg.dataset.ugDirty = "0";
      }
    });
    obs.observe(dlg, { attributes: true, attributeFilter: ["open"] });
    const markEdited = function () {
      if (!dlg.open || (spec.requireVisible && form.hidden)) { return; }
      const cur = ugSerializeForm(form);
      dlg.dataset.ugDirty = (dlg.dataset.ugSnap !== undefined && cur === dlg.dataset.ugSnap) ? "0" : "1";
    };
    form.addEventListener("input", markEdited);
    form.addEventListener("change", markEdited);
    dlg.addEventListener("close", function () { dlg.dataset.ugDirty = "0"; });
    dlg.addEventListener("cancel", function (e) {
      if (ugIsDialogDirty(dlg)) { e.preventDefault(); requestSafeCloseDialog(dlg); }
    });
    dlg.querySelectorAll("button[formmethod='dialog'][value='cancel']").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        if (ugIsDialogDirty(dlg)) { e.preventDefault(); requestSafeCloseDialog(dlg); }
      });
    });
  });
  window.addEventListener("beforeunload", function (e) {
    if (ugHasAnyUnsavedWork()) { e.preventDefault(); e.returnValue = ""; }
  });
}
"""
