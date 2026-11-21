"""Inline @agent mention autocomplete and per-turn routing with shared conversation context."""

MENTION_SCRIPT: str = r"""
let mentionFiltered = [], mentionActiveIdx = 0, mentionMenuOpen = false, mentionRange = null;

function closeMentionMenu() {
  if (!mentionMenuOpen) { return; }
  mentionMenuOpen = false;
  mentionFiltered = [];
  mentionRange = null;
  const menu = document.getElementById("slash-cmd-menu");
  if (menu && !slashMenuOpen) { menu.hidden = true; menu.innerHTML = ""; }
  if (queryEl && !slashMenuOpen) {
    queryEl.removeAttribute("role");
    queryEl.removeAttribute("aria-autocomplete");
    queryEl.removeAttribute("aria-expanded");
    queryEl.removeAttribute("aria-controls");
    queryEl.removeAttribute("aria-activedescendant");
  }
}

function syncMentionSelection() {
  const menu = document.getElementById("slash-cmd-menu");
  if (!menu) { return; }
  menu.querySelectorAll("[data-mention-idx]").forEach(function (btn) {
    const on = Number(btn.getAttribute("data-mention-idx")) === mentionActiveIdx;
    btn.setAttribute("aria-selected", String(on));
    if (on) { btn.scrollIntoView({ block: "nearest" }); }
  });
  if (queryEl && mentionFiltered[mentionActiveIdx]) {
    queryEl.setAttribute("aria-activedescendant", "mention-opt-" + mentionActiveIdx);
  }
}

function applyMentionChoice(agent) {
  if (!agent || !queryEl || !mentionRange) { closeMentionMenu(); return; }
  const slug = String(agent.id || agent.name || "").toLowerCase().replace(/[^a-z0-9_-]+/g, "");
  const val = queryEl.value;
  const before = val.slice(0, mentionRange.start);
  const after = val.slice(mentionRange.end);
  const insert = "@" + slug + (after.startsWith(" ") ? "" : " ");
  queryEl.value = before + insert + after;
  const nextPos = before.length + insert.length;
  closeMentionMenu();
  if (typeof autoResizeQuery === "function") { autoResizeQuery(); }
  queryEl.focus();
  if (queryEl.setSelectionRange) { queryEl.setSelectionRange(nextPos, nextPos); }
}

function updateMentionMenu() {
  const menu = document.getElementById("slash-cmd-menu");
  if (!menu || !queryEl || slashMenuOpen) { closeMentionMenu(); return; }
  const pos = typeof queryEl.selectionStart === "number" ? queryEl.selectionStart : queryEl.value.length;
  const prefix = queryEl.value.slice(0, pos);
  const match = prefix.match(/(^|[\s(])@([a-z0-9_-]*)$/i);
  if (!match) { closeMentionMenu(); return; }
  const needle = (match[2] || "").toLowerCase();
  const atStart = pos - needle.length - 1;
  const team = (typeof agentTeam !== "undefined" && Array.isArray(agentTeam)) ? agentTeam : [];
  if (!team.length) { closeMentionMenu(); return; }
  const scored = [];
  for (const ag of team) {
    const idScore = typeof cmdScore === "function" ? cmdScore(needle, ag.id) : 1;
    const nameScore = typeof cmdScore === "function" ? cmdScore(needle, ag.name) : 1;
    const roleScore = typeof cmdScore === "function" ? Math.floor(cmdScore(needle, ag.role || "") * 0.6) : 0;
    const s = Math.max(idScore, nameScore, roleScore);
    if (!needle || s > 0) { scored.push({ ag, s }); }
  }
  if (needle) { scored.sort((a, b) => b.s - a.s); }
  mentionFiltered = scored.slice(0, 10).map(x => x.ag);
  if (!mentionFiltered.length) { closeMentionMenu(); return; }
  mentionRange = { start: atStart, end: pos };
  mentionActiveIdx = Math.min(mentionActiveIdx, mentionFiltered.length - 1);
  let html = "<div role='presentation' class='px-2.5 pt-2 pb-1 text-2xs font-mono uppercase tracking-wider text-[#738196]'>" + escapeHtml(t("mention_grp_agents")) + "</div>";
  mentionFiltered.forEach(function (ag, idx) {
    const col = typeof paletteColorsFor === "function" ? paletteColorsFor(ag.palette).accent : "#4BB8E8";
    const modelTag = ag.model_name ? "<span class='ml-auto text-xs font-mono text-[#738196] truncate' style='max-width:9rem'>" + escapeHtml(ag.model_name) + "</span>" : "";
    html += "<button type='button' id='mention-opt-" + idx + "' role='option' aria-selected='" + (idx === mentionActiveIdx ? "true" : "false") + "' data-mention-idx='" + idx + "' class='slash-item'>"
      + "<span aria-hidden='true' class='w-2 h-2 rounded-full shrink-0' style='background:" + col + "'></span>"
      + "<span class='font-mono text-xs text-[#4BB8E8] shrink-0'>@" + escapeHtml(ag.id) + "</span>"
      + "<span class='text-xs text-[#A0B0C8] truncate'>" + escapeHtml(ag.name + (ag.role ? " — " + ag.role : "")) + "</span>"
      + modelTag + "</button>";
  });
  menu.innerHTML = html;
  menu.hidden = false;
  mentionMenuOpen = true;
  queryEl.setAttribute("role", "combobox");
  queryEl.setAttribute("aria-autocomplete", "list");
  queryEl.setAttribute("aria-expanded", "true");
  queryEl.setAttribute("aria-controls", "slash-cmd-menu");
  syncMentionSelection();
  menu.querySelectorAll("[data-mention-idx]").forEach(function (btn) {
    btn.addEventListener("mouseenter", function () { mentionActiveIdx = Number(btn.getAttribute("data-mention-idx") || 0); syncMentionSelection(); });
    btn.addEventListener("mousedown", function (e) { e.preventDefault(); applyMentionChoice(mentionFiltered[Number(btn.getAttribute("data-mention-idx") || 0)]); });
  });
}

function handleMentionKeydown(e) {
  if (!mentionMenuOpen || !mentionFiltered.length) { return false; }
  if (e.key === "ArrowDown") { e.preventDefault(); mentionActiveIdx = (mentionActiveIdx + 1) % mentionFiltered.length; syncMentionSelection(); return true; }
  if (e.key === "ArrowUp") { e.preventDefault(); mentionActiveIdx = (mentionActiveIdx - 1 + mentionFiltered.length) % mentionFiltered.length; syncMentionSelection(); return true; }
  if (e.key === "Tab" || e.key === "Enter") {
    e.preventDefault();
    if (e.key === "Enter" && (e.isComposing || e.keyCode === 229)) { return true; }
    applyMentionChoice(mentionFiltered[mentionActiveIdx]);
    return true;
  }
  if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); closeMentionMenu(); return true; }
  return false;
}

function resolveMentionedAgent(text) {
  const raw = String(text || "");
  if (!raw.includes("@") || typeof agentTeam === "undefined" || !Array.isArray(agentTeam) || !agentTeam.length) { return null; }
  const re = /(?:^|[\s(])@([a-z0-9_-]+)\b/gi;
  let m;
  while ((m = re.exec(raw)) !== null) {
    const token = m[1].toLowerCase();
    const hit = agentTeam.find(function (ag) {
      const cleanName = String(ag.name || "").toLowerCase().replace(/[^a-z0-9_-]+/g, "");
      return String(ag.id || "").toLowerCase() === token || cleanName === token;
    });
    if (hit) { return hit.id; }
  }
  return null;
}

function bindMentionUX() {
  document.addEventListener("click", function (e) {
    const menu = document.getElementById("slash-cmd-menu");
    if (mentionMenuOpen && menu && !menu.contains(e.target) && e.target !== queryEl) { closeMentionMenu(); }
  });
}
"""
