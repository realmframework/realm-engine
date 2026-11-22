"""HTML template for Time Tracking (Arbeitszeiterfassung), Wirksamkeitsdokumentation, and ROI."""

IMPACT_VIEW_HTML: str = r"""<section id="impact-view" class="wb-view hidden" aria-label="Time Tracking, Impact Journal and ROI">
  <header class="wb-header">
    <div class="wb-title-row">
      <h1 data-i18n="imp_title" class="wb-title">Time &amp; Impact</h1>
      <div id="imp-stats" class="wb-stat-strip" aria-live="polite"></div>
    </div>
    <div class="wb-controls">
      <button id="imp-exp-pdf-btn" type="button" data-i18n="imp_exp_pdf" class="wb-btn">Report (.pdf)</button>
      <button id="imp-exp-pptx-btn" type="button" data-i18n="imp_exp_pptx" class="wb-btn">Slides (.pptx)</button>
      <button id="imp-add-entry-btn" type="button" data-i18n="imp_log_btn" class="wb-btn wb-btn-primary">+ Log Impact</button>
    </div>
  </header>

  <section class="timer-bar" aria-label="Live work timer">
    <input id="imp-timer-label" type="text" maxlength="180" aria-label="Current task or activity" data-i18n-aria-label="imp_timer_ph" placeholder="What are you working on right now?" data-i18n-placeholder="imp_timer_ph" class="wb-input" />
    <select id="imp-timer-project" aria-label="Timer project" data-i18n-aria-label="wb_project" class="wb-select"></select>
    <span id="imp-timer-clock" class="timer-clock" role="timer" aria-live="off">00:00:00</span>
    <div class="wb-controls">
      <button id="imp-timer-start-btn" type="button" data-i18n="imp_start" class="wb-btn wb-btn-primary">Start</button>
      <button id="imp-timer-pause-btn" type="button" hidden data-i18n="imp_pause" class="wb-btn">Pause</button>
      <button id="imp-timer-stop-btn" type="button" hidden data-i18n="imp_stop_log" class="wb-btn wb-btn-danger">Stop &amp; Save</button>
    </div>
  </section>

  <div id="imp-tablist" role="tablist" aria-label="Time and Impact views" class="wb-tabs">
    <button type="button" role="tab" id="imp-tab-roi" data-imp-tab="roi" aria-selected="true" data-i18n="imp_tab_roi">ROI &amp; Overview</button>
    <button type="button" role="tab" id="imp-tab-journal" data-imp-tab="journal" aria-selected="false" data-i18n="imp_tab_journal">Impact Journal</button>
    <button type="button" role="tab" id="imp-tab-time" data-imp-tab="time" aria-selected="false" data-i18n="imp_tab_time">Time Log</button>
  </div>

  <div id="imp-panel-roi" role="tabpanel" aria-labelledby="imp-tab-roi" style="display:flex;flex-direction:column;gap:1rem">
    <div id="imp-kpi-grid" class="kpi-grid"></div>
    <form id="imp-rate-form" style="display:flex;flex-wrap:wrap;align-items:flex-end;gap:0.65rem;padding:0.85rem 1rem;border-radius:0.9rem;background:var(--surface-raised);border:1px solid var(--border-subtle)">
      <div class="wb-field"><label for="imp-cfg-rate" data-i18n="imp_hourly_rate">Hourly Rate (optional, for ROI)</label><input id="imp-cfg-rate" type="number" min="0" max="10000" step="1" value="85" class="wb-input" style="width:9rem" /></div>
      <div class="wb-field"><label for="imp-cfg-cur" data-i18n="imp_currency">Currency</label><select id="imp-cfg-cur" class="wb-select"><option value="EUR">EUR (€)</option><option value="USD">USD ($)</option><option value="CHF">CHF</option><option value="GBP">GBP (£)</option></select></div>
      <button type="submit" data-i18n="save" class="wb-btn wb-btn-sm">Save</button>
    </form>
    <div id="imp-roi-table-wrap"></div>
  </div>

  <div id="imp-panel-journal" role="tabpanel" aria-labelledby="imp-tab-journal" hidden>
    <p data-i18n="imp_journal_sub" style="margin:0 0 0.85rem;color:var(--text-muted);font-size:calc(0.875rem * var(--ui-scale,1))">Document when you did what, what changed, and what effect it created — in your own plain words.</p>
    <div id="imp-journal-list"></div>
  </div>

  <div id="imp-panel-time" role="tabpanel" aria-labelledby="imp-tab-time" hidden>
    <form id="imp-manual-time-form" class="wb-task-quickbar">
      <input id="imp-mt-label" type="text" required maxlength="180" aria-label="Time entry label" data-i18n-aria-label="imp_timer_ph" placeholder="Add manual work entry..." data-i18n-placeholder="imp_manual_ph" class="wb-input" />
      <input id="imp-mt-mins" type="number" required min="1" max="1440" value="45" aria-label="Minutes" data-i18n-aria-label="imp_minutes" class="wb-input" style="width:6rem" />
      <input id="imp-mt-date" type="date" aria-label="Date" data-i18n-aria-label="wb_date" class="wb-input" />
      <select id="imp-mt-project" aria-label="Project" data-i18n-aria-label="wb_project" class="wb-select"></select>
      <button type="submit" data-i18n="wb_add_btn" class="wb-btn wb-btn-primary">Add</button>
    </form>
    <div class="wb-list-toolbar">
      <span id="imp-time-rollup" style="font-size:calc(0.875rem * var(--ui-scale,1));color:var(--text-muted)"></span>
      <button id="imp-export-csv-btn" type="button" data-i18n="imp_export_csv" class="wb-btn wb-btn-sm">Export CSV</button>
    </div>
    <div id="imp-time-list"></div>
  </div>
</section>"""

IMPACT_MODALS_HTML: str = r"""<dialog id="impact-entry-modal" closedby="any" aria-labelledby="ie-modal-title" class="wb-dialog">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.9rem;border-bottom:1px solid var(--border-subtle);padding-bottom:0.65rem">
    <h2 id="ie-modal-title" data-i18n="imp_modal_new" style="margin:0;font-size:calc(1.125rem * var(--ui-scale,1));font-weight:600">Log Impact</h2>
    <button type="button" data-close-dialog="impact-entry-modal" aria-label="Close impact dialog" class="wb-icon-btn">✕</button>
  </div>
  <form id="ie-form" style="display:flex;flex-direction:column;gap:0.75rem">
    <input id="ie-id" type="hidden" value="" />
    <div class="wb-form-grid">
      <div class="wb-field"><label for="ie-date" data-i18n="imp_when">When</label><input id="ie-date" type="date" required class="wb-input" /></div>
      <div class="wb-field"><label for="ie-project" data-i18n="wb_project">Project</label><select id="ie-project" class="wb-select"></select></div>
    </div>
    <div class="wb-field"><label for="ie-what" data-i18n="imp_what_done">What did you do?</label><textarea id="ie-what" rows="2" required maxlength="1000" class="wb-textarea"></textarea></div>
    <div class="wb-field"><label for="ie-effect" data-i18n="imp_effect">What effect or change did it create?</label><textarea id="ie-effect" rows="2" required maxlength="1500" class="wb-textarea"></textarea></div>
    <div class="wb-field"><label for="ie-notes" data-i18n="imp_evidence">Notes &amp; Evidence (optional)</label><textarea id="ie-notes" rows="2" maxlength="2000" class="wb-textarea"></textarea></div>
    <div class="wb-form-grid">
      <div class="wb-field"><label for="ie-hours" data-i18n="imp_hours_inv">Hours Invested</label><input id="ie-hours" type="number" min="0" max="5000" step="0.25" value="0" class="wb-input" /></div>
      <div class="wb-field"><label for="ie-saved" data-i18n="imp_time_saved">Time Saved (hours)</label><input id="ie-saved" type="number" min="0" max="5000" step="0.25" value="0" class="wb-input" /></div>
      <div class="wb-field"><label for="ie-cost" data-i18n="imp_direct_cost">Direct Cost</label><input id="ie-cost" type="number" min="0" max="10000000" step="10" value="0" class="wb-input" /></div>
      <div class="wb-field"><label for="ie-value" data-i18n="imp_est_value">Estimated Value</label><input id="ie-value" type="number" min="0" max="10000000" step="10" value="0" class="wb-input" /></div>
    </div>
    <div class="wb-field"><label for="ie-tag" data-i18n="imp_outcome_tag">Outcome Type</label><select id="ie-tag" class="wb-select"><option value="quality" data-i18n="imp_tag_quality">Quality &amp; Clarity</option><option value="time_saved" data-i18n="imp_tag_time_saved">Time Saved</option><option value="revenue" data-i18n="imp_tag_revenue">Financial / Value</option><option value="wellbeing" data-i18n="imp_tag_wellbeing">Team / Client Impact</option><option value="milestone" data-i18n="imp_tag_milestone">Key Milestone</option></select></div>
    <div style="display:flex;justify-content:space-between;align-items:center;gap:0.5rem;padding-top:0.65rem;border-top:1px solid var(--border-subtle);flex-wrap:wrap">
      <div style="display:flex;gap:0.4rem">
        <button id="ie-ai-draft-btn" type="button" data-i18n="imp_ai_draft" class="wb-btn wb-btn-sm">AI Polish Draft</button>
        <button id="ie-delete" type="button" hidden data-i18n="delete_btn" class="wb-btn wb-btn-sm wb-btn-danger">Delete</button>
      </div>
      <div style="display:flex;gap:0.5rem;margin-inline-start:auto">
        <button type="button" data-close-dialog="impact-entry-modal" data-i18n="cancel" class="wb-btn">Cancel</button>
        <button type="submit" data-i18n="save" class="wb-btn wb-btn-primary">Save</button>
      </div>
    </div>
  </form>
</dialog>"""
