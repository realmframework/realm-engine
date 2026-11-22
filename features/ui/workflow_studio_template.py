"""HTML template for Native Local Workflow & Agent Pipeline Studio (Visual Canvas + Step View)."""

WORKFLOWS_VIEW_HTML: str = r"""<section id="workflows-view" class="wb-view hidden" aria-label="Workflow Pipelines">
  <header class="wb-header">
    <div class="wb-title-row">
      <h1 data-i18n="wf_title" class="wb-title">Workflows</h1>
      <select id="wf-select" aria-label="Active workflow" data-i18n-aria-label="wf_select_aria" class="wb-select" style="min-width:11rem;max-width:16rem"></select>
      <span id="wf-trigger-pill" class="wb-stat-pill">Manual</span>
    </div>
    <div class="wb-controls">
      <button id="wf-templates-btn" type="button" data-i18n="wf_templates_btn" class="wb-btn wb-btn-sm">Templates</button>
      <button id="wf-new-btn" type="button" data-i18n="wf_new_btn" class="wb-btn wb-btn-sm">+ New Pipeline</button>
      <button id="wf-run-btn" type="button" data-i18n="wf_run_btn" class="wb-btn wb-btn-primary">Run Pipeline</button>
      <button id="wf-stop-btn" type="button" hidden data-i18n="wf_stop_btn" class="wb-btn wb-btn-danger">Stop Run</button>
    </div>
  </header>

  <div id="wf-toolbar" role="toolbar" focusgroup="toolbar wrap" aria-label="Workflow studio controls" data-i18n-aria-label="wf_toolbar_aria" class="wf-toolbar">
    <div role="group" aria-label="View mode" class="wf-tb-group">
      <button id="wf-mode-canvas" type="button" data-wf-mode="canvas" aria-pressed="true" data-i18n="wf_view_canvas" class="wf-tb-btn">Visual Canvas</button>
      <button id="wf-mode-steps" type="button" data-wf-mode="steps" aria-pressed="false" data-i18n="wf_view_steps" class="wf-tb-btn">Step View</button>
    </div>
    <span role="separator" aria-orientation="vertical" class="wf-tb-sep"></span>
    <div role="group" aria-label="Add workflow step" class="wf-tb-group">
      <select id="wf-add-kind" aria-label="Node type to add" data-i18n-aria-label="wf_node_kind" class="wb-select" style="padding-block:0.32rem">
        <option value="vault_search" data-i18n="wf_k_vault_search">Vault Search</option>
        <option value="run_agent" data-i18n="wf_k_run_agent">Run Agent</option>
        <option value="condition" data-i18n="wf_k_condition">If / Condition</option>
        <option value="extract_tasks" data-i18n="wf_k_extract_tasks">Extract Tasks</option>
        <option value="generate_slides" data-i18n="wf_k_generate_slides">Generate Slides</option>
        <option value="save_guide" data-i18n="wf_k_save_guide">Save Guide</option>
        <option value="log_impact" data-i18n="wf_k_log_impact">Log Impact</option>
      </select>
      <button id="wf-add-node-btn" type="button" data-i18n="wf_add_step" class="wf-tb-btn">+ Add Step</button>
    </div>
    <span role="separator" aria-orientation="vertical" class="wf-tb-sep"></span>
    <div role="group" aria-label="Pipeline actions" class="wf-tb-group">
      <button id="wf-save-btn" type="button" data-i18n="save" class="wf-tb-btn">Save</button>
      <button id="wf-delete-btn" type="button" data-i18n="delete_btn" class="wf-tb-btn">Delete</button>
    </div>
  </div>
  <div id="wf-meta-bar" hidden class="wf-meta-bar">
    <div class="wb-field"><label for="wf-name-in" data-i18n="wf_name_lbl">Workflow Name</label><input id="wf-name-in" type="text" maxlength="140" class="wb-input" /></div>
    <div class="wb-field"><label for="wf-trig-sel" data-i18n="wf_trigger_lbl">Trigger</label><select id="wf-trig-sel" class="wb-select"><option value="manual" data-i18n="wf_trig_manual">Manual Run</option><option value="schedule" data-i18n="wf_trig_schedule">Local Schedule</option><option value="file_imported" data-i18n="wf_trig_file">On File Added</option><option value="task_done" data-i18n="wf_trig_task">On Task Done</option></select></div>
    <div id="wf-sched-wrap" hidden class="wb-field"><label for="wf-sched-mins" data-i18n="wf_sched_lbl">Interval (min)</label><input id="wf-sched-mins" type="number" min="5" max="10080" step="5" value="60" class="wb-input" style="width:7.5rem" /></div>
  </div>
  <p id="wf-live-status" role="status" aria-live="polite" class="visually-hidden"></p>

  <div id="wf-empty-banner" hidden class="wb-empty" style="display:flex;flex-direction:column;align-items:center;gap:0.75rem">
    <p data-i18n="wf_empty_msg" style="margin:0;max-width:34rem">Automate multi-step solo workflows right on your machine: chain your Agents, Vault Search, Slides, Kanban Tasks, and Impact Notes with zero cloud lock-in.</p>
    <div style="display:flex;gap:0.5rem;flex-wrap:wrap;justify-content:center">
      <button id="wf-empty-tpl-btn" type="button" data-i18n="wf_browse_templates" class="wb-btn wb-btn-primary">Browse 4 Starter Templates</button>
      <button id="wf-empty-new-btn" type="button" data-i18n="wf_new_btn" class="wb-btn">+ New Workflow</button>
    </div>
  </div>

  <div id="wf-workspace-grid" class="wf-workspace-grid">
    <div id="wf-canvas-viewport" class="wf-canvas-viewport" aria-label="Visual workflow node canvas">
      <div id="wf-canvas-stage" class="wf-canvas-stage">
        <svg id="wf-svg-layer" class="wf-svg-layer" aria-hidden="true"></svg>
        <div id="wf-nodes-layer"></div>
      </div>
      <div id="wf-steps-panel" hidden class="wf-step-list"></div>
    </div>

    <aside class="wf-side-panel" aria-label="Node inspector and run log">
      <div id="wf-side-tablist" role="tablist" aria-label="Inspector and Run Log" class="wb-tabs" style="margin:0">
        <button type="button" role="tab" id="wf-tab-inspect" data-wf-side="inspect" aria-selected="true" data-i18n="wf_tab_inspect">Step Inspector</button>
        <button type="button" role="tab" id="wf-tab-runs" data-wf-side="runs" aria-selected="false" data-i18n="wf_tab_runs">Live Run &amp; History</button>
      </div>
      <div id="wf-panel-inspect" role="tabpanel" aria-labelledby="wf-tab-inspect" style="display:flex;flex-direction:column;gap:0.7rem">
        <div id="wf-node-inspector"></div>
      </div>
      <div id="wf-panel-runs" role="tabpanel" aria-labelledby="wf-tab-runs" hidden style="display:flex;flex-direction:column;gap:0.65rem">
        <div id="wf-live-console" style="display:flex;flex-direction:column;gap:0.45rem"></div>
        <div id="wf-runs-history" style="display:flex;flex-direction:column;gap:0.45rem"></div>
      </div>
    </aside>
  </div>
</section>"""

WORKFLOWS_MODALS_HTML: str = r"""<dialog id="wf-templates-modal" closedby="any" aria-labelledby="wf-tpl-title" class="wb-dialog" style="max-width:48rem">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.9rem;border-bottom:1px solid var(--border-subtle);padding-bottom:0.65rem">
    <h2 id="wf-tpl-title" data-i18n="wf_tpl_modal_title" style="margin:0;font-size:calc(1.15rem * var(--ui-scale,1));font-weight:600">Starter Workflow Templates</h2>
    <button type="button" data-close-dialog="wf-templates-modal" aria-label="Close templates" class="wb-icon-btn">✕</button>
  </div>
  <div id="wf-tpl-grid" class="wf-tpl-grid"></div>
</dialog>

<dialog id="wf-run-modal" closedby="any" aria-labelledby="wf-run-title" class="wb-dialog" style="max-width:34rem">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.85rem;border-bottom:1px solid var(--border-subtle);padding-bottom:0.6rem">
    <h2 id="wf-run-title" data-i18n="wf_run_modal_title" style="margin:0;font-size:calc(1.1rem * var(--ui-scale,1));font-weight:600">Run Workflow Pipeline</h2>
    <button type="button" data-close-dialog="wf-run-modal" aria-label="Close run dialog" class="wb-icon-btn">✕</button>
  </div>
  <form id="wf-run-form" style="display:flex;flex-direction:column;gap:0.8rem">
    <div class="wb-field"><label for="wf-run-input" data-i18n="wf_run_input_lbl">Topic, Report, or Notes Input (used as {{input}})</label><textarea id="wf-run-input" rows="4" maxlength="8000" placeholder="e.g. Q4 Client Strategy Review..." class="wb-textarea"></textarea></div>
    <div style="display:flex;justify-content:flex-end;gap:0.5rem">
      <button type="button" data-close-dialog="wf-run-modal" data-i18n="cancel" class="wb-btn">Cancel</button>
      <button type="submit" data-i18n="wf_start_run" class="wb-btn wb-btn-primary">Start Pipeline</button>
    </div>
  </form>
</dialog>"""