"""Native destructive confirmations and document/chat delete handlers."""

CONFIRM_SCRIPT: str = r"""
function confirmDeletion(title, message, confirmLabel) {
  const dialog = document.getElementById("confirm-modal"); if (dialog.open) { return Promise.resolve(false); }
  document.getElementById("confirm-title").textContent = title; document.getElementById("confirm-message").textContent = message;
  const confirmBtn = document.getElementById("confirm-delete-btn"); if (confirmBtn) { confirmBtn.textContent = confirmLabel || t("delete_btn"); }
  dialog.returnValue = "";
  return new Promise(function (resolve) {
    dialog.addEventListener("close", function () { const confirmed = dialog.returnValue === "delete"; dialog.returnValue = ""; resolve(confirmed); }, { once: true });
    dialog.showModal();
  });
}
async function deleteSavedChat(id) {
  const chat = savedChats.find(function (c) { return c.chat_id === id; }), version = areaVersion, area = activeKnowledgeArea;
  if (!await confirmDeletion(t("cf_del_chat_t"), t("cf_del_chat_m", { title: chat ? chat.title : "this conversation" }))) { return; }
  if (version !== areaVersion) { return; }
  try {
    const response = await areaFetch("/api/chats/" + encodeURIComponent(id) + (typeof freeChatMode !== "undefined" && freeChatMode ? "?free_chat=true" : ""), { method: "DELETE" }, area);
    if (!response.ok) { throw new Error(t("st_switch_err")); }
    if (version !== areaVersion) { return; }
    if (currentChatId === id) { resetHome(); } await loadRecentChats(); areaStatus(t("st_chat_deleted"));
  } catch (error) { areaStatus(error.message); }
}
async function deleteLibraryGuide(guide, previousTag) {
  const version = areaVersion, area = activeKnowledgeArea;
  if (!await confirmDeletion(t("cf_del_doc_t"), t("cf_del_doc_m", { title: guide.title, area: areaLabel(area) }))) { return; }
  if (version !== areaVersion) { return; }
  try {
    const response = await areaFetch("/api/guides/" + encodeURIComponent(guide.doc_id), { method: "DELETE" }, area);
    if (!response.ok) { throw new Error(t("st_switch_err")); }
    if (version !== areaVersion) { return; }
    await loadWorkspace(); await openLibraryCatalog(previousTag); const heading = document.getElementById("catalog-heading"); if (heading) { heading.focus({ preventScroll: true }); } areaStatus(t("st_doc_deleted"));
  } catch (error) { areaStatus(error.message); }
}
function bindDialogFallbacks() {
  const outside = function (e, d) { const r = d.getBoundingClientRect(); return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom; };
  for (const d of document.querySelectorAll('dialog[closedby="any"]')) {
    let pressedOutside = false;
    d.addEventListener("pointerdown", function (e) { pressedOutside = e.target === d && outside(e, d); });
    d.addEventListener("pointerup", function (e) { if (pressedOutside && e.target === d && outside(e, d) && d.open) { d.close(); } pressedOutside = false; });
  }
  document.getElementById("new-area-form").addEventListener("submit", createKnowledgeArea);
  document.getElementById("new-area-btn").addEventListener("click", openNewAreaDialog);
}
"""
