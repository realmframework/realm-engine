"""Local evidence dashboard, explicit bulk scrub and honest Markdown report export."""

COMPLIANCE_SCRIPT: str = r"""
let lastAudit = null, auditOperation = 0, scrubPending = false, auditLoading = false;
function invalidateAudit() {
  ++auditOperation; lastAudit = null; auditLoading = false; document.getElementById("run-audit-btn").disabled = false;
  document.getElementById("export-compliance-btn").disabled = true;
  document.getElementById("vault-metrics").textContent = "Run a check to inspect this workspace.";
  document.getElementById("benchmark-metrics").textContent = "No current measurements.";
  document.getElementById("scrub-vault-btn").hidden = true;
}
function renderAudit(report) {
  const benchmark = report.benchmark;
  const counts = Object.entries(report.counts_by_type).map(([type, count]) =>
    "<span class='rounded-full border border-white/15 px-2 py-1 text-xs'>" + escapeHtml(type === "DOB" ? "DOB" : PII_CATEGORIES[type]?.[0] || type) + ": " + count + "</span>").join("");
  document.getElementById("vault-metrics").innerHTML = "<p class='text-lg text-[#EEF2F8]'>" + (report.clean_vault ? "No supported personal-information patterns found" : "Review required")
    + "</p><p class='my-3'>" + report.files_scanned + " documents · " + report.unredacted_warnings + " details to review · " + report.scan_errors + " unreadable files</p><p class='mb-2 text-xs'>Stored redactions by category</p><div class='flex flex-wrap gap-2'>" + counts
    + "</div><p class='mt-3'>" + report.total_redacted_tokens + " hidden details stored · " + report.audit_external_bytes_sent + " bytes sent to external AI services by this check</p>";
  const metric = (label, value) => "<div class='flex justify-between gap-4 border-b border-white/10 py-3'><dt>" + label + "</dt><dd class='font-mono text-[#EEF2F8] text-right'>" + escapeHtml(value) + "</dd></div>";
  document.getElementById("benchmark-metrics").innerHTML = "<dl>" + metric("Diagnostic result", benchmark.status)
    + metric("Retrieval latency", benchmark.latency_ms + " ms") + metric("Top chunk recall", benchmark.recall_at_1 === null ? "No data" : Math.round(benchmark.recall_at_1 * 100) + "% · self-query")
    + metric("Provenance coverage", benchmark.retrieved_sources ? benchmark.provenance_coverage + "%" : "No data")
    + metric("Hallucination Refusal Gate", benchmark.hallucination_refusal_gate ? "PASS · no-source guard" : "WARN")
    + metric("Active Retrieval Tier", benchmark.active_retrieval_tier) + "</dl><p class='mt-3 text-xs'>OOD probe: " + escapeHtml(benchmark.ood_mode) + ". Generation was not evaluated.</p>";
  document.getElementById("scrub-vault-btn").hidden = !report.unredacted_warnings;
  document.getElementById("export-compliance-btn").disabled = false;
  document.getElementById("compliance-status").textContent = "Audit completed for " + report.area + " at " + new Date(report.audited_at).toLocaleTimeString() + ".";
}
async function runComplianceAudit(scrub = false) {
  if (scrubPending || auditLoading) { return; }
  const version = areaVersion, operation = ++auditOperation, area = activeKnowledgeArea;
  const status = document.getElementById("compliance-status");
  lastAudit = null; auditLoading = true; document.getElementById("run-audit-btn").disabled = true; document.getElementById("export-compliance-btn").disabled = true;
  status.textContent = scrub ? "Scrubbing and re-indexing this area..." : "Checking your documents and source links on this computer...";
  if (scrub) { scrubPending = true; }
  document.getElementById("scrub-vault-btn").disabled = true;
  try {
    const response = await areaFetch(scrub ? "/api/compliance/scrub" : "/api/compliance/audit", { method: "POST", ...(scrub ? { headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirm: true }) } : {}) }, area), report = await response.json();
    if (version !== areaVersion || operation !== auditOperation) { return; }
    if (!response.ok) { throw new Error(report.detail || "Audit failed."); }
    if (scrub) { await loadWorkspace(); await loadGuidesCatalog(null); }
    if (version !== areaVersion || operation !== auditOperation) { return; }
    lastAudit = report; renderAudit(report);
  } catch (error) { if (version === areaVersion && operation === auditOperation) { status.textContent = error.message; } }
  finally { if (scrub) { scrubPending = false; } if (operation === auditOperation) { auditLoading = false; document.getElementById("run-audit-btn").disabled = false; document.getElementById("scrub-vault-btn").disabled = false; } }
}
async function scrubVault() {
  const version = areaVersion, area = activeKnowledgeArea;
  if (!await confirmDeletion("Scrub entire vault?", "Replace detected PII in every Markdown file inside “" + area + "” and re-index it? Original matched values are permanently removed. Review the redaction preview first.")) { return; }
  if (version === areaVersion) { await runComplianceAudit(true); }
}
function exportComplianceReport() {
  const report = lastAudit;
  if (!report || report.area !== activeKnowledgeArea) { return; }
  const benchmark = report.benchmark;
  const lines = ["# DSGVO & EU AI Act Technical Audit Report", "", "Area: " + report.area, "Audited at: " + report.audited_at,
    "", "> Technical evidence only. This is not a legal compliance certificate.", "", "## Data sovereignty and vault scan",
    "Strict local-only lock: " + report.strict_local_only, "External bytes sent by this audit: " + report.audit_external_bytes_sent,
    "Markdown files scanned: " + report.files_scanned, "Supported unredacted matches: " + report.unredacted_warnings,
    "Unreadable files: " + report.scan_errors, "No supported raw patterns detected: " + report.clean_vault,
    "", "| Category | Stored redaction tokens |", "| --- | --- |",
    ...Object.entries(report.counts_by_type).map(([type, count]) => "| " + type + " | " + count + " |"),
    "", "## Retrieval diagnostics", "Result: " + benchmark.status, "Latency (lexical + hybrid): " + benchmark.latency_ms + " ms",
    "Self-query recall@1: " + benchmark.recall_at_1, "Provenance coverage: " + benchmark.provenance_coverage + "% of " + benchmark.retrieved_sources + " retrieved sources",
    "OOD no-source guard: " + (benchmark.hallucination_refusal_gate ? "PASS" : "WARN"), "OOD query: " + benchmark.out_of_domain_query,
    "OOD mode: " + benchmark.ood_mode, "Active retrieval tier: " + benchmark.active_retrieval_tier,
    "", "## Scope and limitations", report.limitations,
    "The lock blocks this application's cloud provider, embedding and speech routes. UI assets are self-hosted. It is not an OS firewall and does not verify downstream Ollama service behavior. Provision models locally before offline use. Already-started requests cannot be recalled.",
    "The scan covers active-area Markdown only, including nested folders. Original binaries and saved chats are outside its scope. Filename-hint name detection, broad date patterns and regex addresses need human review. A clean scan is not proof of anonymization. Retrieval self-checks are not a labeled recall benchmark or a generative hallucination evaluation.",
    "", "## Governance references for reviewer assessment",
    "[GDPR / DSGVO, Articles 25 and 32](https://eur-lex.europa.eu/eli/reg/2016/679)",
    "[EU AI Act, Articles 10, 13 and 15](https://eur-lex.europa.eu/eli/reg/2024/1689)", ""];
  const url = URL.createObjectURL(new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" }));
  const link = document.createElement("a"); link.href = url; link.download = report.area + "-technical-audit.md";
  document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
document.getElementById("run-audit-btn").addEventListener("click", () => runComplianceAudit());
document.getElementById("export-compliance-btn").addEventListener("click", exportComplianceReport);
document.getElementById("scrub-vault-btn").addEventListener("click", scrubVault);
"""
