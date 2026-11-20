"""Native popover placement follows the fixed sidebar header without custom dismissal."""

WORKSPACE_MENU_SCRIPT: str = r"""
function closeWorkspaceMenu() {
  const menu = document.getElementById("workspace-menu"), trigger = document.getElementById("workspace-switcher-btn");
  if (menu.matches(":popover-open")) {
    const hadFocus = menu.contains(document.activeElement); menu.hidePopover();
    if (hadFocus) { trigger.focus({ preventScroll: true }); }
  }
}
function positionWorkspaceMenu() {
  const menu = document.getElementById("workspace-menu"), rect = document.getElementById("workspace-switcher-btn").getBoundingClientRect();
  menu.style.left = Math.max(8, rect.left) + "px"; menu.style.top = rect.bottom + 8 + "px";
  menu.style.setProperty("--workspace-menu-height", Math.max(120, innerHeight - rect.bottom - 24) + "px");
}
function bindWorkspaceMenu() {
  const menu = document.getElementById("workspace-menu");
  menu.addEventListener("beforetoggle", event => { if (event.newState === "open") { positionWorkspaceMenu(); } });
  menu.addEventListener("toggle", event => { document.getElementById("workspace-switcher-btn").setAttribute("aria-expanded", String(event.newState === "open")); if (event.newState === "open") {
    const nav = document.getElementById("knowledge-areas"), selected = nav.querySelector("[aria-current=page]");
    if (selected) { nav.scrollTop += selected.getBoundingClientRect().top - nav.getBoundingClientRect().top - Math.max(0, (nav.clientHeight - selected.clientHeight) / 2); }
  } });
  window.addEventListener("resize", positionWorkspaceMenu);
}
"""
