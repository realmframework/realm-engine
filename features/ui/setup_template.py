"""Shared beginner mode cards and the explicit cloud usage controls."""


def mode_cards(prefix: str) -> str:
    return f"""<form id="{prefix}-run-form" action="/api/workspace" method="post" aria-label="Choose how to run" class="flex flex-col gap-3">
  <fieldset class="flex flex-col gap-2"><legend class="text-sm font-medium text-[#EEF2F8] mb-3">How Do You Want to Run?</legend>
    <label for="{prefix}-mode-local" class="run-mode-card"><input id="{prefix}-mode-local" name="{prefix}_run_mode" type="radio" value="local" checked aria-describedby="{prefix}-local-description"/>
      <span><span class="block text-sm font-medium">100% Local AI Only (Strict Privacy)</span>
        <span data-ram-detected class="block text-xs text-[#4BB8E8] mt-1">Checking this computer’s RAM…</span>
        <span id="{prefix}-local-description" data-ram-advice class="block text-xs text-[#A0B0C8] leading-relaxed mt-1">Uses local Ollama only. All cloud providers stay locked so nothing leaves this computer.</span>
      </span></label>
    <p class="text-xs text-[#738196] px-3">Quick start: <a href="https://ollama.com/download" target="_blank" rel="noopener noreferrer" class="text-[#4BB8E8] hover:underline">install Ollama</a>, then use Download Recommended Local AI in the Setup Wizard. No terminal is needed.</p>
    <label for="{prefix}-mode-cloud" class="run-mode-card"><input id="{prefix}-mode-cloud" name="{prefix}_run_mode" type="radio" value="cloud" aria-describedby="{prefix}-cloud-description"/>
      <span><span class="block text-sm font-medium">Local + Cloud AI (Ollama &amp; API Keys)</span>
        <span id="{prefix}-cloud-description" class="block text-xs text-[#A0B0C8] leading-relaxed mt-1">Use free local Ollama AND paid cloud APIs (OpenAI, Gemini, Anthropic, Kimi, etc.) side-by-side. Save keys for multiple providers and switch models anytime; Daily Budget Cap protects cloud spend.</span>
      </span></label>
    <label for="{prefix}-mode-search" class="run-mode-card"><input id="{prefix}-mode-search" name="{prefix}_run_mode" type="radio" value="search" aria-describedby="{prefix}-search-description"/>
      <span><span class="block text-sm font-medium">Search &amp; Anonymize Only (Zero AI Setup)</span>
        <span id="{prefix}-search-description" class="block text-xs text-[#A0B0C8] leading-relaxed mt-1">Organize folders, use instant keyword search and preview DSGVO redaction now. No API key, model download or installation needed.</span>
      </span></label>
  </fieldset>
  <div class="flex items-center justify-between gap-3"><p id="{prefix}-mode-status" role="status" class="text-xs text-[#A0B0C8]"></p><button type="submit" class="shrink-0 rounded-lg border border-[#4BB8E8]/40 px-3 py-2 text-xs text-[#4BB8E8]">Use selected mode</button></div>
</form>"""


BUDGET_PANEL_HTML = """<section class="rounded-xl border border-white/10 bg-[#04060F] p-4" aria-labelledby="budget-heading">
  <h3 id="budget-heading" class="text-sm font-medium"><span data-everyday-only>Daily Cloud Spending Limit</span><span data-specialist-only>Daily Cloud Budget Guard</span></h3>
  <p id="budget-meter" role="status" class="text-sm text-[#4BB8E8] mt-2">Loading today’s usage…</p>
  <p id="budget-details" data-specialist-only class="text-xs text-[#A0B0C8] mt-1"></p>
  <form id="budget-limits-form" action="/api/workspace" method="post" aria-label="Cloud budget limits" class="mt-4 flex flex-col gap-3">
    <div class="grid grid-cols-2 gap-3"><div><label for="daily-cloud-request-limit" class="block text-xs text-[#A0B0C8] mb-1">Daily Cloud Request Limit</label>
      <input id="daily-cloud-request-limit" name="daily_cloud_request_limit" type="number" min="0" max="100000" step="1" value="50" required class="w-full rounded-lg bg-[#0B1020] border border-white/15 px-3 py-2 text-sm"/></div>
    <div><label for="daily-budget-usd-limit" class="block text-xs text-[#A0B0C8] mb-1">Daily USD Budget (estimate)</label>
      <input id="daily-budget-usd-limit" name="daily_budget_usd_limit" type="number" min="0" step="0.01" value="1.00" required class="w-full rounded-lg bg-[#0B1020] border border-white/15 px-3 py-2 text-sm"/></div></div>
    <button type="submit" class="self-end rounded-lg border border-white/15 px-3 py-2 text-xs">Save budget limits</button>
  </form>
  <p data-everyday-only class="text-xs text-[#738196] mt-3">Your daily limit covers paid AI answers, search helpers and voice. Costs are estimates; your provider’s bill can differ. Local AI is free. One question can use more than one request.</p>
  <p data-specialist-only class="text-[11px] text-[#738196] leading-relaxed mt-3">Includes cloud answers, embeddings and voice attempts. Usage is reserved before sending; estimates are not your provider’s bill and prices vary. Local Ollama is always $0 and unlimited. Daily counters roll over at midnight UTC; the 12/minute burst limit stays active after a reset.</p>
  <div class="flex flex-wrap gap-3 mt-3"><button id="reset-budget-btn" type="button" class="rounded-lg border border-white/15 px-3 py-2 text-xs">Reset Counter</button><button id="forget-api-key-btn" type="button" class="rounded-lg border border-white/15 px-3 py-2 text-xs">Forget Saved API Key</button></div>
  <p id="budget-action-status" role="status" class="text-xs text-[#A0B0C8] mt-2"></p>
</section>"""
