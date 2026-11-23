"""Integrated Bottom Panel Terminal client: multi-shell SSE streaming, ANSI renderer & Send-to-Copilot."""

TERMINAL_SCRIPT: str = r"""
let termSessions = [];
let termActiveId = "";
let termStreamCtrl = null;
const termBuffers = new Map();
const termCmdHistory = [];
let termHistIdx = -1;
let termResizeTimer = null;
let termSyncTheme = safeStorageGet("realm_term_theme_sync") !== "0";

function setTerminalThemeSync(enabled, persist) {
  termSyncTheme = enabled !== false;
  const pane = document.getElementById("bottom-terminal-pane");
  if (pane) { pane.setAttribute("data-term-theme", termSyncTheme ? "sync" : "neutral"); }
  const btn = document.getElementById("term-theme-btn");
  if (btn) {
    btn.setAttribute("aria-pressed", String(termSyncTheme));
    const lbl = termSyncTheme ? t("term_theme_btn_on") : t("term_theme_btn_off");
    btn.title = lbl;
    btn.setAttribute("aria-label", lbl);
  }
  const chk = document.getElementById("theme-terminal-sync-toggle");
  if (chk) { chk.checked = termSyncTheme; }
  if (typeof workspaceConfig === "object" && workspaceConfig) { workspaceConfig.sync_terminal_theme = termSyncTheme; }
  if (persist !== false) {
    safeStorageSet("realm_term_theme_sync", termSyncTheme ? "1" : "0");
    if (typeof persistAppearancePatch === "function") { persistAppearancePatch({ sync_terminal_theme: termSyncTheme }); }
  }
}

function termCleanControlText(raw) {
  let out = String(raw || "");
  out = out.replace(/\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)/g, "");
  out = out.replace(/\x1b\[[0-9;?]*[A-HJKSTfhlmnprsu]/g, function (seq) {
    return seq.endsWith("m") ? seq : (seq === "\x1b[2J" || seq === "\x1b[3J" ? "\x0c" : "");
  });
  out = out.replace(/\x1b[()][AB012]/g, "");
  out = out.replace(/\r\n/g, "\n");
  return out;
}

function termAppendBuffer(sid, chunk) {
  const cleaned = termCleanControlText(chunk);
  let buf = termBuffers.get(sid) || "";
  if (cleaned.includes("\x0c")) {
    buf = cleaned.slice(cleaned.lastIndexOf("\x0c") + 1);
  } else {
    buf += cleaned;
  }
  const lines = buf.split("\n").map(function (ln) {
    if (!ln.includes("\r")) { return ln; }
    const segs = ln.split("\r");
    return segs[segs.length - 1];
  });
  buf = lines.join("\n");
  if (buf.length > 90000) { buf = buf.slice(-72000); }
  termBuffers.set(sid, buf);
}

function termStripAnsi(text) {
  return String(text || "").replace(/\x1b\[[0-9;]*m/g, "").replace(/[\x00-\x08\x0b\x0c\x0e-\x1f]/g, "");
}

function termAnsiToHtml(raw) {
  const esc = escapeHtml(String(raw || ""));
  const parts = esc.split(/(\x1b\[[0-9;]*m)/);
  let html = "", classes = new Set();
  for (const part of parts) {
    const m = part.match(/^\x1b\[([0-9;]*)m$/);
    if (m) {
      const codes = (m[1] || "0").split(";").map(Number);
      for (const c of codes) {
        if (c === 0) { classes.clear(); }
        else if (c === 1) { classes.add("ansi-b"); }
        else if (c === 2) { classes.add("ansi-d"); }
        else if (c === 3) { classes.add("ansi-i"); }
        else if (c === 4) { classes.add("ansi-u"); }
        else if ((c >= 30 && c <= 37) || (c >= 90 && c <= 97)) {
          Array.from(classes).forEach(function (k) { if (/^ansi-(3|9)\d$/.test(k)) { classes.delete(k); } });
          classes.add("ansi-" + c);
        } else if (c === 39) {
          Array.from(classes).forEach(function (k) { if (/^ansi-(3|9)\d$/.test(k)) { classes.delete(k); } });
        }
      }
      continue;
    }
    if (!part) { continue; }
    const clean = part.replace(/[\x00-\x08\x0b\x0c\x0e-\x1f]/g, "");
    if (!clean) { continue; }
    html += classes.size ? ("<span class='" + Array.from(classes).join(" ") + "'>" + clean + "</span>") : clean;
  }
  return html;
}

function renderTerminalOutput() {
  const out = document.getElementById("term-output");
  if (!out) { return; }
  const buf = termBuffers.get(termActiveId) || "";
  out.innerHTML = termAnsiToHtml(buf);
  out.scrollTop = out.scrollHeight;
}

function renderTerminalTabs() {
  const bar = document.getElementById("term-session-tabs"), cwdEl = document.getElementById("term-cwd-pill");
  if (!bar) { return; }
  bar.innerHTML = termSessions.map(function (s) {
    const sel = s.id === termActiveId;
    const dot = "<span class='term-pill-dot" + (s.running ? "" : " is-exited") + "' aria-hidden='true'></span>";
    return "<button type='button' role='tab' aria-selected='" + String(sel) + "' data-term-id='" + escapeHtml(s.id) + "' class='term-pill'>"
      + dot + "<span>" + escapeHtml(s.label) + "</span>"
      + "<span class='term-pill-x' data-term-close='" + escapeHtml(s.id) + "' role='button' aria-label='Close terminal'>✕</span></button>";
  }).join("");
  bar.querySelectorAll("[data-term-id]").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      const x = e.target.closest("[data-term-close]");
      if (x) { e.stopPropagation(); closeTerminalSession(x.getAttribute("data-term-close") || ""); return; }
      selectTerminalSession(btn.getAttribute("data-term-id") || "");
    });
  });
  const active = termSessions.find(function (s) { return s.id === termActiveId; });
  if (cwdEl) {
    const p = active ? String(active.cwd || "") : "";
    const shortP = p.split(/[\\/]/).filter(Boolean).slice(-2).join("/");
    cwdEl.textContent = shortP || p;
    cwdEl.title = p;
  }
}

function termMeasureDims() {
  const out = document.getElementById("term-output");
  if (!out || out.clientWidth < 120 || out.clientHeight < 60) { return { cols: 100, rows: 24 }; }
  return {
    cols: Math.max(40, Math.min(260, Math.floor((out.clientWidth - 28) / 7.8))),
    rows: Math.max(8, Math.min(90, Math.floor((out.clientHeight - 20) / 19.5))),
  };
}

function stopTerminalStream() {
  if (termStreamCtrl) { termStreamCtrl.abort(); termStreamCtrl = null; }
}

async function connectTerminalStream(sid) {
  stopTerminalStream();
  if (!sid) { return; }
  termBuffers.set(sid, "");
  renderTerminalOutput();
  const ctrl = new AbortController();
  termStreamCtrl = ctrl;
  try {
    const res = await fetch("/api/terminal/sessions/" + encodeURIComponent(sid) + "/stream?after=0", { signal: ctrl.signal });
    if (!res.ok) { return; }
    await readSseStream(res, function (ev, data) {
      if (sid !== termActiveId) { return; }
      if (ev === "chunk" && data && typeof data.data === "string") {
        termAppendBuffer(sid, data.data);
        renderTerminalOutput();
      } else if (ev === "exit") {
        const s = termSessions.find(function (x) { return x.id === sid; });
        if (s) { s.running = false; s.exit_code = data ? data.exit_code : 0; }
        termAppendBuffer(sid, "\n\x1b[2m[Process exited" + (data && data.exit_code !== null && data.exit_code !== undefined ? (" with code " + data.exit_code) : "") + "]\x1b[0m\n");
        renderTerminalTabs();
        renderTerminalOutput();
      }
    }, function () { return ctrl.signal.aborted; });
  } catch (_e) {}
}

function selectTerminalSession(sid) {
  if (!sid) { return; }
  termActiveId = sid;
  renderTerminalTabs();
  connectTerminalStream(sid);
  const inp = document.getElementById("term-input");
  if (inp) { inp.focus({ preventScroll: true }); }
}

async function createTerminalSession() {
  const dims = termMeasureDims();
  try {
    const res = await fetch("/api/terminal/sessions", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cols: dims.cols, rows: dims.rows }),
    });
    const data = await safeJson(res);
    if (!res.ok || !data || !data.session) { throw new Error((data && data.detail) || "Could not start terminal."); }
    termSessions.push(data.session);
    selectTerminalSession(data.session.id);
  } catch (err) {
    if (typeof showToast === "function") { showToast((err && err.message) || "Terminal unavailable.", 3200); }
  }
}

async function closeTerminalSession(sid) {
  if (!sid) { return; }
  try { await fetch("/api/terminal/sessions/" + encodeURIComponent(sid), { method: "DELETE" }); } catch (_e) {}
  termSessions = termSessions.filter(function (s) { return s.id !== sid; });
  termBuffers.delete(sid);
  if (termActiveId === sid) {
    stopTerminalStream();
    termActiveId = termSessions.length ? termSessions[termSessions.length - 1].id : "";
    if (termActiveId) { connectTerminalStream(termActiveId); }
    else { renderTerminalOutput(); }
  }
  renderTerminalTabs();
}

async function ensureTerminalReady() {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) { return; }
  if (!termSessions.length) {
    try {
      const res = await fetch("/api/terminal/sessions");
      const data = await safeJson(res);
      if (res.ok && data && Array.isArray(data.sessions) && data.sessions.length) {
        termSessions = data.sessions;
        selectTerminalSession(termSessions[0].id);
        return;
      }
    } catch (_e) {}
    await createTerminalSession();
  } else if (!termStreamCtrl && termActiveId) {
    connectTerminalStream(termActiveId);
  }
  const inp = document.getElementById("term-input");
  if (inp) { inp.focus({ preventScroll: true }); }
}

async function sendTerminalCommand(raw, appendNewline) {
  if (!termActiveId) { await createTerminalSession(); }
  if (!termActiveId) { return; }
  try {
    await fetch("/api/terminal/sessions/" + encodeURIComponent(termActiveId) + "/input", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data: appendNewline ? (raw + "\n") : raw }),
    });
  } catch (_e) {}
}

async function sendTerminalSignal(sig) {
  if (!termActiveId) { return; }
  try {
    await fetch("/api/terminal/sessions/" + encodeURIComponent(termActiveId) + "/signal", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ signal: sig || "interrupt" }),
    });
  } catch (_e) {}
}

function sendTerminalOutputToCopilot() {
  const out = document.getElementById("term-output");
  let snippet = "";
  const sel = window.getSelection();
  if (sel && !sel.isCollapsed && out && out.contains(sel.anchorNode)) {
    snippet = sel.toString().trim();
  }
  if (!snippet) {
    const plain = termStripAnsi(termBuffers.get(termActiveId) || "").trim();
    snippet = plain.split("\n").slice(-35).join("\n").trim();
  }
  if (!snippet) {
    if (typeof showToast === "function") { showToast(t("term_empty_copilot"), 2200); }
    return;
  }
  if (typeof cpSelection !== "undefined") { cpSelection = { docId: "", filename: "Terminal", text: snippet.slice(0, 5600) }; }
  if (typeof cpRenderChips === "function") { cpRenderChips(); }
  if (typeof openCopilotForCurrentContext === "function") { openCopilotForCurrentContext(); }
}

function bindTerminalUX() {
  if (typeof IS_EMBED !== "undefined" && IS_EMBED) { return; }
  const form = document.getElementById("term-form"), inp = document.getElementById("term-input"), out = document.getElementById("term-output");
  const newBtn = document.getElementById("term-new-btn"), intBtn = document.getElementById("term-int-btn"), clrBtn = document.getElementById("term-clear-btn"), cpBtn = document.getElementById("term-copilot-btn"), thBtn = document.getElementById("term-theme-btn"), thChk = document.getElementById("theme-terminal-sync-toggle");
  setTerminalThemeSync(termSyncTheme, false);
  if (thBtn) { thBtn.addEventListener("click", function () { setTerminalThemeSync(!termSyncTheme, true); }); }
  if (thChk) { thChk.addEventListener("change", function () { setTerminalThemeSync(Boolean(thChk.checked), true); }); }
  if (form && inp) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      const cmd = inp.value;
      if (cmd.trim() && termCmdHistory[termCmdHistory.length - 1] !== cmd) { termCmdHistory.push(cmd); if (termCmdHistory.length > 80) { termCmdHistory.shift(); } }
      termHistIdx = termCmdHistory.length;
      inp.value = "";
      sendTerminalCommand(cmd, true);
    });
    inp.addEventListener("keydown", function (e) {
      if (e.key === "ArrowUp") { e.preventDefault(); if (!termCmdHistory.length) { return; } termHistIdx = Math.max(0, termHistIdx - 1); inp.value = termCmdHistory[termHistIdx] || ""; }
      else if (e.key === "ArrowDown") { e.preventDefault(); if (!termCmdHistory.length) { return; } termHistIdx = Math.min(termCmdHistory.length, termHistIdx + 1); inp.value = termCmdHistory[termHistIdx] || ""; }
      else if (e.ctrlKey && !e.metaKey && e.key.toLowerCase() === "c" && inp.selectionStart === inp.selectionEnd) { e.preventDefault(); sendTerminalSignal("interrupt"); }
      else if (e.ctrlKey && !e.metaKey && e.key.toLowerCase() === "l") { e.preventDefault(); if (termActiveId) { termBuffers.set(termActiveId, ""); renderTerminalOutput(); } }
    });
  }
  if (out && inp) {
    out.addEventListener("click", function () { const sel = window.getSelection(); if (!sel || sel.isCollapsed) { inp.focus({ preventScroll: true }); } });
  }
  if (newBtn) { newBtn.addEventListener("click", createTerminalSession); }
  if (intBtn) { intBtn.addEventListener("click", function () { sendTerminalSignal("interrupt"); }); }
  if (clrBtn) { clrBtn.addEventListener("click", function () { if (termActiveId) { termBuffers.set(termActiveId, ""); renderTerminalOutput(); } }); }
  if (cpBtn) { cpBtn.addEventListener("click", sendTerminalOutputToCopilot); }
  if (out && typeof ResizeObserver !== "undefined") {
    new ResizeObserver(function () {
      if (!termActiveId) { return; }
      clearTimeout(termResizeTimer);
      termResizeTimer = setTimeout(function () {
        const d = termMeasureDims();
        fetch("/api/terminal/sessions/" + encodeURIComponent(termActiveId) + "/resize", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(d) }).catch(function () {});
      }, 220);
    }).observe(out);
  }
  document.addEventListener("keydown", function (e) {
    if (e.ctrlKey && !e.metaKey && !e.altKey && (e.key === "`" || e.code === "Backquote") && !document.querySelector("dialog[open]")) {
      e.preventDefault();
      if (typeof toggleBottomPanel === "function") { toggleBottomPanel("terminal"); }
    }
  });
}
"""
