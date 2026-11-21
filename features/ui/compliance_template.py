"""The Settings privacy tab retains full audit controls and honest diagnostic limits."""

from core.version import APP_VERSION

COMPLIANCE_HTML = f"""<div class="flex flex-col gap-5">
<p class="text-xs text-[#A0B0C8]"><span data-i18n="priv_active_ws">Active workspace:</span> <span id="compliance-area" class="font-mono"></span> · <span data-i18n="priv_local_ev">local technical evidence</span></p>
<section class="rounded-xl border border-white/10 p-4" aria-labelledby="vault-heading">
<h3 id="vault-heading" data-i18n="priv_vault_title" class="text-sm font-medium">Data Sovereignty &amp; GDPR Workspace Status</h3>
<p data-i18n="priv_vault_sub" class="text-xs text-[#738196] mt-2">GDPR Art. 25 &amp; 32 · pattern-based Markdown scan</p>
<form id="governance-lock-form" action="/api/workspace" method="post" aria-label="Local execution policy" class="my-4">
<div class="flex flex-wrap items-center gap-3"><input id="governance-local-only" name="strict_local_only" type="checkbox" switch role="switch" checked aria-describedby="governance-lock-state"/>
<label for="governance-local-only" data-i18n="priv_strict_lock" class="text-sm">Strict Local-Only Lock (GDPR Safe Mode)</label>
<button type="submit" data-i18n="priv_save_policy" class="rounded-lg border border-white/15 px-3 py-1.5 text-xs">Save policy</button></div>
<p id="governance-lock-state" class="text-xs text-[#A0B0C8] mt-2"></p></form>
<div id="vault-metrics" data-i18n="priv_run_hint" class="text-sm text-[#A0B0C8]">Run Live Audit to inspect this workspace.</div>
<button id="scrub-vault-btn" hidden type="button" data-i18n="priv_scrub_btn" class="mt-4 rounded-lg border border-[#EF4444]/40 px-3 py-2 text-sm text-[#FCA5A5]">Scrub Entire Workspace Now</button>
</section>
<section class="rounded-xl border border-white/10 p-4" aria-labelledby="benchmark-heading">
<h3 id="benchmark-heading" data-i18n="priv_bench_title" class="text-sm font-medium">EU AI Act Art. 15 · RAG Benchmark</h3>
<div id="benchmark-metrics" data-i18n="priv_bench_empty" class="text-sm text-[#A0B0C8] mt-3">No current measurements.</div></section>
<section class="rounded-xl border border-white/10 p-4" aria-labelledby="audit-heading">
<h3 id="audit-heading" data-i18n="priv_actions_title" class="text-sm font-medium">Audit actions</h3>
<div class="flex flex-wrap gap-3 my-4"><button id="run-audit-btn" type="button" data-i18n="priv_run_btn" class="rounded-lg bg-[#4BB8E8] px-4 py-2 text-sm text-[#04060F]">↻ Run Live Audit</button>
<button id="export-compliance-btn" disabled type="button" data-i18n="priv_export_btn" class="rounded-lg border border-white/15 px-4 py-2 text-sm disabled:opacity-50">↓ Export GDPR &amp; EU AI Act Report (.md)</button></div>
<p id="compliance-status" role="status" aria-live="polite" class="text-sm text-[#A0B0C8]"></p>
<p data-i18n="priv_disclaimer" class="text-xs text-[#738196] leading-relaxed mt-4">These diagnostics support engineering and data protection review. They do not certify legal compliance, clinical safety or complete anonymization. The lock blocks app cloud routes; it is not a device-wide network firewall.</p>
</section>
<details id="system-diagnostics-details" class="rounded-xl border border-white/10 p-4">
<summary class="cursor-pointer text-sm font-medium flex items-center justify-between gap-2"><span data-i18n="diag_title">System &amp; Diagnostics</span><span id="app-version-badge" class="text-xs font-mono text-[#738196]">v{APP_VERSION}</span></summary>
<div class="mt-3 flex flex-col gap-3">
<div id="diagnostics-summary" class="text-xs font-mono text-[#A0B0C8] leading-relaxed"></div>
<div class="flex flex-wrap gap-2"><button id="refresh-diagnostics-btn" type="button" data-i18n="diag_refresh" class="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:border-[#4BB8E8]">↻ Refresh</button><button id="copy-diagnostics-btn" type="button" data-i18n="diag_copy" class="rounded-lg border border-white/15 px-3 py-1.5 text-xs hover:border-[#4BB8E8]">Copy Sanitized Report</button></div>
</div></details></div>"""
