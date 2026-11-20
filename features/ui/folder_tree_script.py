"""Recursive explorer nodes, accessible branch controls and row-local child forms."""

FOLDER_TREE_SCRIPT: str = r"""
const collapsedFolders = new Set();
function folderSvg(documentIcon = false, classes = "w-4 h-4 shrink-0") {
  const path = documentIcon
    ? "M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9ZM14 3v6h6M8 13h8m-8 4h5"
    : "M3 7h18v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 4";
  return "<svg aria-hidden='true' class='" + classes + "' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><path d='" + path + "'/></svg>";
}
function buildFolderTree() {
  const root = { name: selectedAreas().length > 1 ? "Selected areas" : activeKnowledgeArea || "knowledge_base", fullPath: "", children: [], fileCount: 0 }, nodes = new Map([["", root]]);
  for (const folder of workspaceFolders) {
    let parent = root, path = "";
    for (const name of folder.path.split("/").filter(Boolean)) {
      path = path ? path + "/" + name : name;
      if (!nodes.has(path)) {
        const child = { name, fullPath: path, children: [], fileCount: 0 };
        nodes.set(path, child); parent.children.push(child);
      }
      parent = nodes.get(path);
    }
    parent.fileCount = Number(folder.doc_count || 0);
  }
  function total(node) {
    node.children.sort((a, b) => a.name.localeCompare(b.name));
    node.fileCount += node.children.reduce((sum, child) => sum + total(child), 0);
    return node.fileCount;
  }
  total(root);
  return root;
}
function renderTreeNode(node, depth, index = { next: 0 }) {
  const path = node.fullPath, id = "folder-node-" + index.next++, selected = path === (selectedSubfolder || "");
  const expanded = !collapsedFolders.has(path), isRoot = depth === 0;
  const chevron = node.children.length
    ? `<button type='button' data-folder-toggle='${escapeHtml(path)}' aria-expanded='${expanded}' aria-controls='${id}-children'
        aria-label='Toggle subfolders of ${escapeHtml(path || node.name)}' class='folder-branch-toggle inline-flex items-center justify-center w-6 h-7 shrink-0 text-[#738196]'>
        <svg aria-hidden='true' width='14' height='14' viewBox='0 0 14 14' fill='none' stroke='currentColor' stroke-width='1.5'><path d='m4.5 2.5 4.5 4.5-4.5 4.5'/></svg></button>`
    : "<span aria-hidden='true' class='inline-flex items-center justify-center w-6 shrink-0'><span class='inline-block w-3.5 h-3.5 folder-chevron-spacer'></span></span>";
  const multi = selectedAreas().length > 1, areaRoot = multi && selectedAreas().includes(path);
  const area = knowledgeAreas.find(a => a.name === (areaRoot ? path : activeKnowledgeArea));
  const canDelete = isRoot ? !multi && Boolean(area && area.can_delete) : areaRoot ? Boolean(area && area.can_delete) : true;
  const label = escapeHtml(path || node.name);
  const actions = `<div class='folder-row-actions flex items-center gap-1 shrink-0'>
      <button type='button' data-create-child='${escapeHtml(path)}' ${isRoot && multi ? 'disabled' : ''} aria-label='Create subfolder in ${label}' title='+ Subfolder'
        aria-expanded='false' aria-controls='${id}-creator' class='folder-row-action'>+</button>
      ${folderChatButton(isRoot ? null : path)}
      <button type='button' data-delete-folder='${escapeHtml(path)}' aria-label='Delete ${isRoot ? "workspace" : "subfolder"} ${label}'
        title='${canDelete ? "Delete folder and its contents" : "This area root is protected"}' ${canDelete ? "" : "disabled"}
        class='folder-row-action hover:text-[#EF4444] disabled:opacity-30'>✕</button>
    </div>`;
  return `<li data-folder-node='${escapeHtml(path)}' ${isRoot ? "data-area-root" : ""}>
    <div class='folder-tree-row ${selected ? "is-selected" : ""}' style='--folder-depth: ${depth}'>${chevron}
      <button type='button' data-subfolder='${escapeHtml(path)}' aria-pressed='${selected}'
        class='folder-filter ${isRoot ? "folder-root" : ""}'>
        ${folderSvg(false, "w-4 h-4 shrink-0" + (selected ? " text-[#4BB8E8]" : ""))}<span class='truncate' title='${label}'>${escapeHtml(node.name)}</span>
        <span class='folder-file-count'>${node.fileCount}</span>
      </button>${actions}
    </div>
    <div id='${id}-creator' hidden class='folder-child-creator my-2' style='--folder-depth: ${depth + 1}'>
      <form data-child-form='${escapeHtml(path)}' action='/api/subfolders' method='post' aria-label='Create child in ${label}' class='flex flex-wrap items-end gap-2'>
        <div class='flex-1 min-w-0'><label for='${id}-name' class='block text-xs text-[#A0B0C8] mb-1'>New subfolder name</label>
          <input id='${id}-name' name='name' required maxlength='64' pattern='[\\p{L}\\p{N}_][\\p{L}\\p{N}_ .\\-]{0,63}'
            placeholder='patients' autocapitalize='none' spellcheck='false' aria-describedby='${id}-help'
            class='w-full rounded-lg border border-white/15 bg-[#04060F] px-3 py-2 text-sm'/>
          <p id='${id}-help' class='text-[11px] text-[#738196] mt-1'>Create inside ${label}</p>
        </div><button type='submit' class='rounded-lg border border-white/15 px-3 py-2 text-xs'>Create</button>
        <button type='button' data-cancel-child='${escapeHtml(path)}' class='text-xs text-[#A0B0C8] px-2 py-2'>Cancel</button>
        <p data-child-status role='status' class='w-full text-xs text-[#A0B0C8]'></p>
      </form>
    </div>
    ${node.children.length ? `<ul id='${id}-children' class='folder-branches' ${expanded ? "" : "hidden"}>${node.children.map(child => renderTreeNode(child, depth + 1, index)).join("")}</ul>` : ""}
  </li>`;
}
function subfolderLibraryHeader() {
  return `<section class='library-folders' aria-label='Workspace Folder Tree'>
    <nav aria-label='Library subfolders' class='folder-nav'><ul class='folder-tree'>${renderTreeNode(buildFolderTree(), 0)}</ul></nav>
  </section>`;
}
function bindFolderTree(root) {
  root.querySelectorAll("[data-folder-toggle]").forEach(function (button) {
    button.addEventListener("click", function () {
      const expanded = button.getAttribute("aria-expanded") !== "true";
      button.setAttribute("aria-expanded", String(expanded));
      document.getElementById(button.getAttribute("aria-controls")).hidden = !expanded;
      if (expanded) { collapsedFolders.delete(button.dataset.folderToggle); }
      else { collapsedFolders.add(button.dataset.folderToggle); }
    });
  });
  root.querySelectorAll("[data-subfolder]").forEach(function (button) {
    button.addEventListener("click", async function () {
      const path = button.dataset.subfolder, version = areaVersion;
      selectedSubfolder = path;
      await openLibraryCatalog(selectedTag);
      if (version !== areaVersion) { return; }
      const selected = Array.from(document.querySelectorAll("[data-subfolder]")).find(b => b.dataset.subfolder === path);
      if (selected) { selected.focus({ preventScroll: true }); }
    });
  });
}
"""
