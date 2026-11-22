"""Compose bounded area, governance, confirmation, and unified responsive sidebar drawer scripts."""

from features.ui.area_script import AREA_SCRIPT
from features.ui.confirm_script import CONFIRM_SCRIPT
from features.ui.redaction_script import REDACTION_SCRIPT

SIDEBAR_DRAWER_SCRIPT: str = r"""
let desktopDrawerCollapsed = safeStorageGet("realm_drawer_collapsed") === "1";
let mobileDrawerOpen = false;
const sidebarNarrowMq = window.matchMedia("(max-width: 900px)");

function syncSidebarDrawer(moveFocus) {
  const sb = document.getElementById("sidebar"), main = document.getElementById("main-shell");
  const openBtn = document.getElementById("sidebar-open-btn"), bd = document.getElementById("sidebar-backdrop");
  const railTog = document.getElementById("rail-drawer-toggle");
  const mobClose = document.getElementById("mobile-drawer-close-btn");
  if (!sb || !main || !openBtn) { return; }
  const narrow = sidebarNarrowMq.matches;
  const visible = narrow ? mobileDrawerOpen : !desktopDrawerCollapsed;
  if (narrow) {
    document.body.classList.remove("drawer-collapsed");
    sb.classList.toggle("-translate-x-full", !visible);
    sb.inert = !visible;
    openBtn.classList.toggle("hidden", visible);
    openBtn.classList.toggle("flex", !visible);
    openBtn.setAttribute("aria-expanded", String(visible));
    if (visible) { sb.setAttribute("role", "dialog"); sb.setAttribute("aria-modal", "true"); }
    else { sb.removeAttribute("role"); sb.removeAttribute("aria-modal"); }
    main.inert = visible;
    if (bd) { bd.hidden = !visible; }
  } else {
    document.body.classList.toggle("drawer-collapsed", desktopDrawerCollapsed);
    sb.classList.remove("-translate-x-full");
    sb.inert = desktopDrawerCollapsed;
    sb.removeAttribute("role"); sb.removeAttribute("aria-modal");
    main.inert = false;
    if (bd) { bd.hidden = true; }
    openBtn.classList.add("hidden"); openBtn.classList.remove("flex");
    if (railTog) { railTog.setAttribute("aria-expanded", String(!desktopDrawerCollapsed)); }
  }
  if (moveFocus === "open" && narrow && mobClose && visible) { mobClose.focus({ preventScroll: true }); }
  if (moveFocus === "close" && narrow && !visible) { openBtn.focus({ preventScroll: true }); }
}

function toggleContextDrawer(forceOpen) {
  if (sidebarNarrowMq.matches) {
    mobileDrawerOpen = forceOpen !== undefined ? Boolean(forceOpen) : !mobileDrawerOpen;
    syncSidebarDrawer(mobileDrawerOpen ? "open" : "close");
    return;
  }
  desktopDrawerCollapsed = forceOpen !== undefined ? !Boolean(forceOpen) : !desktopDrawerCollapsed;
  safeStorageSet("realm_drawer_collapsed", desktopDrawerCollapsed ? "1" : "0");
  syncSidebarDrawer("");
}

function closeMobileDrawerIfOpen(restoreFocus) {
  if (!sidebarNarrowMq.matches || !mobileDrawerOpen) { return; }
  mobileDrawerOpen = false;
  syncSidebarDrawer(restoreFocus ? "close" : "");
}

function bindSidebarDrawer() {
  const openBtn = document.getElementById("sidebar-open-btn"), bd = document.getElementById("sidebar-backdrop"), sb = document.getElementById("sidebar");
  const mobClose = document.getElementById("mobile-drawer-close-btn");
  if (openBtn) { openBtn.addEventListener("click", function () { toggleContextDrawer(true); }); }
  if (mobClose) { mobClose.addEventListener("click", function () { closeMobileDrawerIfOpen(true); }); }
  if (bd) { bd.addEventListener("click", function () { closeMobileDrawerIfOpen(true); }); }
  if (sb) {
    sb.addEventListener("click", function (e) {
      if (sidebarNarrowMq.matches && mobileDrawerOpen && e.target.closest("#sidebar-cmd-btn, #sidebar-agents-btn, #sidebar-formats-btn, #sidebar-work-btn, #sidebar-focus-btn, #sidebar-impact-btn, [data-open-chat], [data-ft-doc], [data-shell-act], [data-drawer-wf], [data-drawer-agent]")) {
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
  const tabs = typeof selector === "string"
    ? Array.from(document.querySelectorAll(selector))
    : (selector && typeof selector.querySelectorAll === "function" ? Array.from(selector.querySelectorAll("[role='tab']")) : []);
  tabs.forEach(function (tab, idx) {
    tab.addEventListener("keydown", function (e) {
      const visible = tabs.filter(function (tEl) { return !tEl.hidden; });
      const curIdx = visible.indexOf(tab);
      if (curIdx < 0 || !visible.length) { return; }
      let next = null;
      if (e.key === "ArrowRight") { next = visible[(curIdx + 1) % visible.length]; }
      else if (e.key === "ArrowLeft") { next = visible[(curIdx + visible.length - 1) % visible.length]; }
      else if (e.key === "Home") { next = visible[0]; }
      else if (e.key === "End") { next = visible[visible.length - 1]; }
      if (next) { e.preventDefault(); next.focus(); if (onSelect) { onSelect(next); } }
    });
  });
}
"""

INTERACTION_SCRIPT = AREA_SCRIPT + CONFIRM_SCRIPT + REDACTION_SCRIPT + SIDEBAR_DRAWER_SCRIPT
