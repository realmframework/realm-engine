"""Card folder pills and a shared, guarded move request for cards and readers."""

MOVE_SCRIPT: str = r"""
let cardMoveContext = null, cardMovePending = false;
function cardFolderPill(guide, index) {
  return "<button type='button' data-move-guide='" + index + "' aria-haspopup='dialog' aria-controls='move-guide-modal' aria-label='"
    + escapeHtml("Move " + guide.title + " from /" + (guide.subfolder || ""))
    + "' class='self-start inline-flex items-center gap-1.5 max-w-full rounded-full border border-white/10 px-2.5 py-1 text-xs text-[#A0B0C8] hover:text-[#EEF2F8] hover:border-white/25'>"
    + folderSvg() + "<span class='truncate'>" + escapeHtml(guide.subfolder || "/") + "</span></button>";
}
function bindCardFolderPills(root, guides, tag) {
  root.querySelectorAll("[data-move-guide]").forEach(function (button) {
    button.addEventListener("click", function (event) {
      event.stopPropagation();
      if (cardMovePending) { return; }
      const guide = guides[Number(button.dataset.moveGuide)], dialog = document.getElementById("move-guide-modal");
      cardMoveContext = { guide, tag, version: areaVersion, operation: currentScrollId };
      document.getElementById("move-guide-description").textContent = "Move “" + guide.title + "” from /" + (guide.subfolder || "") + " within this knowledge area.";
      document.getElementById("move-guide-fields").innerHTML = destinationControls("card-move", guide.subfolder || "");
      document.getElementById("card-move-subfolder").autofocus = true;
      document.getElementById("card-move-status").textContent = "";
      document.getElementById("card-move-form").action = "/api/guides/" + encodeURIComponent(guide.doc_id) + "/move";
      dialog.returnValue = ""; bindDestination("card-move"); dialog.showModal();
    });
  });
}
async function requestGuideMove(guide, subfolder, version) {
  const response = await areaFetch("/api/guides/" + encodeURIComponent(guide.doc_id) + "/move", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ subfolder })
  });
  const data = await response.json();
  if (version !== areaVersion) { return null; }
  if (!response.ok) { throw new Error(data.detail || "Guide could not be moved."); }
  applyWorkspacePayload(data); await loadGuidesCatalog(null);
  return version === areaVersion ? data : null;
}
function bindCardMoveDialog() {
  const dialog = document.getElementById("move-guide-modal"), form = document.getElementById("card-move-form");
  dialog.addEventListener("close", function () {
    if (!dialog.open) { cardMoveContext = null; dialog.returnValue = ""; }
  });
  form.addEventListener("submit", async function (event) {
    if (event.submitter && event.submitter.value === "cancel") { return; }
    event.preventDefault();
    const context = cardMoveContext;
    if (!context || cardMovePending || context.version !== areaVersion) { return; }
    const subfolder = destinationValue("card-move");
    if (subfolder === null) { return; }
    const button = document.getElementById("card-move-submit"), status = document.getElementById("card-move-status");
    cardMovePending = true; button.disabled = true; status.textContent = "Moving guide...";
    try {
      const data = await requestGuideMove(context.guide, subfolder, context.version);
      if (!data) { return; }
      dialog.close();
      if (context.operation !== currentScrollId) { return; }
      await openLibraryCatalog(context.tag);
      if (context.version === areaVersion && document.getElementById("catalog-heading")) {
        document.getElementById("subfolder-status").textContent = "Moved “" + data.guide.title + "” to /" + subfolder + ".";
        document.getElementById("catalog-heading").focus({ preventScroll: true });
      }
    } catch (error) {
      if (context.version === areaVersion) { if (dialog.open) { status.textContent = error.message; } else { areaStatus(error.message); } }
    } finally { cardMovePending = false; button.disabled = false; }
  });
}
"""
