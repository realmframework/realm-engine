"""The Settings privacy tab retains full audit controls and honest diagnostic limits."""

COMPLIANCE_HTML = """<div class="flex flex-col gap-5">
<p class="text-xs text-[#A0B0C8]">Active workspace: <span id="compliance-area" class="font-mono"></span> · local technical evidence</p>
<section class="rounded-xl border border-white/10 p-4" aria-labelledby="vault-heading">
<h3 id="vault-heading" class="text-sm font-medium">Data Sovereignty &amp; DSGVO Vault Status</h3>
<p class="text-xs text-[#738196] mt-2">GDPR Art. 25 &amp; 32 · pattern-based Markdown scan</p>
<form id="governance-lock-form" action="/api/workspace" method="post" aria-label="Local execution policy" class="my-4">
<div class="flex flex-wrap items-center gap-2"><input id="governance-local-only" name="strict_local_only" type="checkbox" checked aria-describedby="governance-lock-state"/>
<label for="governance-local-only" class="text-sm">Strict Local-Only Lock (DSGVO Safe Mode)</label>
<button type="submit" class="rounded-lg border border-white/15 px-3 py-1.5 text-xs">Save policy</button></div>
<p id="governance-lock-state" class="text-xs text-[#A0B0C8] mt-2"></p></form>
<div id="vault-metrics" class="text-sm text-[#A0B0C8]">Run Live Audit to inspect this workspace.</div>
<button id="scrub-vault-btn" hidden type="button" class="mt-4 rounded-lg border border-[#EF4444]/40 px-3 py-2 text-sm text-[#FCA5A5]">Scrub Entire Vault Now</button>
</section>
<section class="rounded-xl border border-white/10 p-4" aria-labelledby="benchmark-heading">
<h3 id="benchmark-heading" class="text-sm font-medium">EU AI Act Art. 15 · RAG Benchmark</h3>
<div id="benchmark-metrics" class="text-sm text-[#A0B0C8] mt-3">No current measurements.</div></section>
<section class="rounded-xl border border-white/10 p-4" aria-labelledby="audit-heading">
<h3 id="audit-heading" class="text-sm font-medium">Audit actions</h3>
<div class="flex flex-wrap gap-3 my-4"><button id="run-audit-btn" type="button" class="rounded-lg bg-[#4BB8E8] px-4 py-2 text-sm text-[#04060F]">↻ Run Live Audit</button>
<button id="export-compliance-btn" disabled type="button" class="rounded-lg border border-white/15 px-4 py-2 text-sm disabled:opacity-50">↓ Export DSGVO &amp; EU AI Act Report (.md)</button></div>
<p id="compliance-status" role="status" aria-live="polite" class="text-sm text-[#A0B0C8]"></p>
<p class="text-xs text-[#738196] leading-relaxed mt-4">These diagnostics support engineering and data protection review. They do not certify legal compliance, clinical safety or complete anonymization. The lock blocks app cloud routes; it is not a device-wide network firewall.</p>
</section></div>"""
