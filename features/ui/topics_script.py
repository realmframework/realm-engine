"""Topic pills belong to Library, with counts for its currently selected folder subtree."""

TOPICS_SCRIPT: str = r"""
function renderLibraryTopics() {
  const nav = document.getElementById("library-topics"); if (!nav) { return; }
  const guides = allGuides.filter(matchesSubfolder), counts = new Map();
  guides.forEach(guide => new Set(guide.tags || []).forEach(tag => counts.set(tag, (counts.get(tag) || 0) + 1)));
  if (selectedTag && !counts.has(selectedTag)) { counts.set(selectedTag, 0); }
  const topics = Array.from(counts, ([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
  nav.innerHTML = [{ name: "", count: guides.length }, ...topics].map(topic => {
    const selected = (selectedTag || "") === topic.name;
    return "<button type='button' data-library-tag='" + escapeHtml(topic.name) + "' aria-pressed='" + selected + "'>" + escapeHtml(topic.name || "All") + " (" + topic.count + ")</button>";
  }).join("");
  nav.querySelectorAll("[data-library-tag]").forEach(button => button.addEventListener("click", async () => {
    const tag = button.dataset.libraryTag || null, version = areaVersion;
    setActiveTag(tag); await openLibraryCatalog(tag);
    if (version !== areaVersion) { return; }
    const selected = Array.from(document.querySelectorAll("[data-library-tag]")).find(b => b.dataset.libraryTag === (tag || ""));
    if (selected) { selected.focus({ preventScroll: true }); }
  }));
}
"""
