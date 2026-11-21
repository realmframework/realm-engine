"""Native destructive confirmations and document/chat delete handlers."""

CONFIRM_SCRIPT: str = r"""
function confirmDeletion(title, message, confirmLabel) {
  const dialog = document.getElementById("confirm-modal"); if (dialog.open) { return Promise.resolve(false); }
  document.getElementById("confirm-title").textContent = title; document.getElementById("confirm-message").textContent = message;
  const confirmBtn = document.getElementById("confirm-delete-btn"); if (confirmBtn) { confirmBtn.textContent = confirmLabel || "Delete"; }
  dialog.returnValue = "";
  return new Promise(function (resolve) {
    dialog.addEventListener("close", function () { const confirmed = dialog.returnValue === "delete"; dialog.returnValue = ""; resolve(confirmed); }, { once: true });
    dialog.showModal();
  });
}
async function deleteSavedChat(id) {
  const chat = savedChats.find(function (c) { return c.chat_id === id; }), version = areaVersion, area = activeKnowledgeArea;
  if (!await confirmDeletion("Delete conversation?", "Permanently delete “" + (chat ? chat.title : "this conversation") + "” and every question, answer and citation in this area? This cannot be undone.")) { return; }
  if (version !== areaVersion) { return; }
  try {
    const response = await areaFetch("/api/chats/" + encodeURIComponent(id) + (typeof freeChatMode !== "undefined" && freeChatMode ? "?free_chat=true" : ""), { method: "DELETE" }, area);
    if (!response.ok) { throw new Error("Chat could not be deleted. Select the area again and retry."); }
    if (version !== areaVersion) { return; }
    if (currentChatId === id) { resetHome(); } await loadRecentChats(); areaStatus("Conversation deleted.");
  } catch (error) { areaStatus(error.message); }
}
async function deleteLibraryGuide(guide, previousTag) {
  const version = areaVersion, area = activeKnowledgeArea;
  if (!await confirmDeletion("Delete guide?", "Permanently delete “" + guide.title + "” from “" + areaLabel(area) + "”, including its indexed passages? This cannot be undone.")) { return; }
  if (version !== areaVersion) { return; }
  try {
    const response = await areaFetch("/api/guides/" + encodeURIComponent(guide.doc_id), { method: "DELETE" }, area);
    if (!response.ok) { throw new Error("Guide could not be deleted. Select the area again and retry."); }
    if (version !== areaVersion) { return; }
    await loadWorkspace(); await openLibraryCatalog(previousTag); document.getElementById("catalog-heading").focus({ preventScroll: true }); areaStatus("Guide deleted.");
  } catch (error) { areaStatus(error.message); }
}
function bindDialogFallbacks() {
  if (!("closedBy" in HTMLDialogElement.prototype)) {
    const outside = function (e, d) { const r = d.getBoundingClientRect(); return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom; };
    for (const d of document.querySelectorAll('dialog[closedby="any"]')) {
      let pressedOutside = false; d.addEventListener("pointerdown", function (e) { pressedOutside = outside(e, d); }); d.addEventListener("pointerup", function (e) { if (pressedOutside && outside(e, d)) { d.close(); } });
    }
  }
  document.getElementById("new-area-form").addEventListener("submit", createKnowledgeArea);
  document.getElementById("new-area-btn").addEventListener("click", openNewAreaDialog);
}
"""
