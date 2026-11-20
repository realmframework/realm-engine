"""A removable in-pill scope chip; Library actions own scope selection."""

SCOPE_SCRIPT: str = r"""
let activeScope = { subfolder: null, doc_id: null }, scopeArea = null;
function renderScopeChoices() {
  const chip = document.getElementById("scope-chip"), scoped = activeScope.doc_id !== null || activeScope.subfolder !== null;
  chip.hidden = !scoped;
  const label = document.getElementById("scope-chip-label"), icon = document.getElementById("scope-chip-icon");
  if (!scoped) { label.textContent = ""; icon.innerHTML = ""; chip.removeAttribute("title"); document.getElementById("scope-status").textContent = ""; return; }
  const isDocument = activeScope.doc_id !== null, guide = isDocument ? allGuides.find(g => g.doc_id === activeScope.doc_id) : null;
  const name = guide ? guide.title : isDocument ? activeScope.doc_id.split("/").pop() : activeScope.subfolder || "Root files";
  label.textContent = String(name).replace(/\[REDACTED_[^\]]*(?:\]|$)/gi, "").replace(/[_\s]+/g, " ").trim() || (isDocument ? "Selected document" : "Selected folder");
  icon.innerHTML = folderSvg(isDocument, "w-3.5 h-3.5 shrink-0");
  chip.title = (isDocument ? "Document: " : "Folder: ") + (activeScope.doc_id ?? activeScope.subfolder);
}
function applyScopeWorkspace() {
  if (scopeArea !== activeKnowledgeArea) { activeScope = { subfolder: null, doc_id: null }; scopeArea = activeKnowledgeArea; }
  renderScopeChoices();
}
function adoptChatScope(session) {
  activeScope = { subfolder: session.subfolder ?? null, doc_id: session.doc_id ?? null };
  scopeArea = activeKnowledgeArea;
  renderScopeChoices();
}
function startScopedChat(scope) {
  resetHome();
  activeScope = scope;
  renderScopeChoices();
  setViewMode(true).then(() => queryEl.focus());
  document.getElementById("scope-status").textContent = activeScope.doc_id !== null || activeScope.subfolder !== null
    ? "New chat scoped to " + document.getElementById("scope-chip-label").textContent
    : "New chat across the entire area";
}
function scopedChatButton(docId) {
  return "<button type='button' data-chat-doc='" + escapeHtml(docId)
    + "' class='self-start rounded-lg border border-white/15 px-3 py-1.5 text-xs text-[#A0B0C8] hover:text-[#EEF2F8]'>Chat with this Document</button>";
}
function folderChatButton(path) {
  return "<button type='button' data-chat-folder='" + escapeHtml(path === null ? ":area:" : path)
    + "' title='Chat with this Folder' aria-label='Chat with this Folder: " + escapeHtml(path === null ? "Entire Area" : path || "Root files")
    + "' class='shrink-0 rounded-lg px-2 py-2 text-xs text-[#738196] hover:text-[#EEF2F8]'>Chat ↗</button>";
}
function bindScopedChatButtons(root) {
  root.querySelectorAll("[data-chat-doc], [data-chat-folder]").forEach(function (button) {
    button.addEventListener("click", function (event) {
      event.stopPropagation();
      startScopedChat(button.hasAttribute("data-chat-doc")
        ? { doc_id: button.dataset.chatDoc, subfolder: null }
        : { doc_id: null, subfolder: button.dataset.chatFolder === ":area:" ? null : button.dataset.chatFolder });
    });
  });
}
document.getElementById("scope-reset-btn").addEventListener("click", () => startScopedChat({ doc_id: null, subfolder: null }));
"""
