"""Compose bounded area, governance, confirmation, and responsive sidebar drawer scripts."""

from features.ui.area_script import AREA_SCRIPT
from features.ui.confirm_script import CONFIRM_SCRIPT
from features.ui.redaction_script import REDACTION_SCRIPT

SIDEBAR_DRAWER_SCRIPT: str = r"""
let desktopSidebarCollapsed = false, mobileDrawerOpen = false;
const sidebarNarrowMq = window.matchMedia("(max-width: 900px)");
function syncSidebarDrawer(moveFocus) {
  const sb = document.getElementById("sidebar"), main = document.getElementById("main-shell");
  const openBtn = document.getElementById("sidebar-open-btn"), colBtn = document.getElementById("sidebar-collapse-btn"), bd = document.getElementById("sidebar-backdrop");
  if (!sb || !main || !openBtn) { return; }
  const narrow = sidebarNarrowMq.matches;
  const visible = narrow ? mobileDrawerOpen : !desktopSidebarCollapsed;
  sb.classList.toggle("-translate-x-full", !visible);
  sb.inert = !visible;
  openBtn.classList.toggle("hidden", visible);
  openBtn.classList.toggle("flex", !visible);
  openBtn.setAttribute("aria-expanded", String(visible));
  if (narrow) {
    main.classList.replace("pl-[250px]", "pl-0");
    if (visible) { sb.setAttribute("role", "dialog"); sb.setAttribute("aria-modal", "true"); }
    else { sb.removeAttribute("role"); sb.removeAttribute("aria-modal"); }
    main.inert = visible;
    if (bd) { bd.hidden = !visible; }
  } else {
    sb.removeAttribute("role"); sb.removeAttribute("aria-modal");
    main.inert = false;
    if (bd) { bd.hidden = true; }
    main.classList.toggle("pl-[250px]", visible);
    main.classList.toggle("pl-0", !visible);
  }
  if (moveFocus === "open" && colBtn && visible) { colBtn.focus({ preventScroll: true }); }
  if (moveFocus === "close" && !visible) { openBtn.focus({ preventScroll: true }); }
}
function closeMobileDrawerIfOpen(restoreFocus) {
  if (!sidebarNarrowMq.matches || !mobileDrawerOpen) { return; }
  mobileDrawerOpen = false;
  syncSidebarDrawer(restoreFocus ? "close" : "");
}
function bindSidebarDrawer() {
  const colBtn = document.getElementById("sidebar-collapse-btn"), openBtn = document.getElementById("sidebar-open-btn"), bd = document.getElementById("sidebar-backdrop"), sb = document.getElementById("sidebar");
  if (colBtn) {
    colBtn.addEventListener("click", function () {
      if (sidebarNarrowMq.matches) { mobileDrawerOpen = false; } else { desktopSidebarCollapsed = true; }
      syncSidebarDrawer("close");
    });
  }
  if (openBtn) {
    openBtn.addEventListener("click", function () {
      if (sidebarNarrowMq.matches) { mobileDrawerOpen = true; } else { desktopSidebarCollapsed = false; }
      syncSidebarDrawer("open");
    });
  }
  if (bd) { bd.addEventListener("click", function () { closeMobileDrawerIfOpen(true); }); }
  if (sb) {
    sb.addEventListener("click", function (e) {
      if (sidebarNarrowMq.matches && mobileDrawerOpen && e.target.closest("#new-chat-btn, #sidebar-cmd-btn, #sidebar-browse-btn, #sidebar-graph-btn, #sidebar-agents-btn, #sidebar-formats-btn, #open-settings-btn, #open-guide-btn, [data-open-chat]")) {
        closeMobileDrawerIfOpen(false);
      }
    });
  }
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && sidebarNarrowMq.matches && mobileDrawerOpen && !document.querySelector("dialog[open]")) {
      e.preventDefault(); closeMobileDrawerIfOpen(true); return;
    }
    if (e.key === "Escape") {
      const openMenu = document.querySelector("details.turn-more-menu[open], details.export-menu[open]");
      if (openMenu) {
        e.preventDefault(); openMenu.open = false;
        const sum = openMenu.querySelector("summary"); if (sum) { sum.focus({ preventScroll: true }); }
      }
    }
  });
  document.addEventListener("click", function (e) {
    document.querySelectorAll("details.turn-more-menu[open], details.export-menu[open]").forEach(function (d) {
      if (!d.contains(e.target)) { d.open = false; }
    });
  });
  sidebarNarrowMq.addEventListener("change", function () { if (!sidebarNarrowMq.matches) { mobileDrawerOpen = false; } syncSidebarDrawer(""); });
  syncSidebarDrawer("");
}
function bindRovingTablist(selector, onSelect) {
  const tabs = Array.from(document.querySelectorAll(selector));
  tabs.forEach(function (tab, idx) {
    tab.addEventListener("keydown", function (e) {
      let next = null;
      if (e.key === "ArrowRight") { next = tabs[(idx + 1) % tabs.length]; }
      else if (e.key === "ArrowLeft") { next = tabs[(idx + tabs.length - 1) % tabs.length]; }
      else if (e.key === "Home") { next = tabs[0]; }
      else if (e.key === "End") { next = tabs[tabs.length - 1]; }
      if (next) { e.preventDefault(); next.focus(); if (onSelect) { onSelect(next); } }
    });
  });
}
"""

INTERACTION_SCRIPT = AREA_SCRIPT + CONFIRM_SCRIPT + REDACTION_SCRIPT + SIDEBAR_DRAWER_SCRIPT
