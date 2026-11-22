"""Native <dialog> modals for editing Work Board tasks, projects, events, and task extraction."""

WORK_BOARD_MODALS_HTML: str = r"""<dialog id="work-task-modal" closedby="any" aria-labelledby="wb-task-modal-title" class="wb-dialog">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;border-bottom:1px solid var(--border-subtle);padding-bottom:0.7rem">
    <h2 id="wb-task-modal-title" data-i18n="wb_task_modal_new" style="margin:0;font-size:calc(1.125rem * var(--ui-scale, 1));font-weight:600">New Task</h2>
    <button type="button" data-close-dialog="work-task-modal" aria-label="Close task dialog" class="wb-icon-btn">✕</button>
  </div>
  <form id="wb-task-form" style="display:flex;flex-direction:column;gap:0.8rem">
    <input id="wb-tf-id" type="hidden" value="" />
    <div class="wb-field"><label for="wb-tf-title" data-i18n="wb_task_title">Title</label><input id="wb-tf-title" type="text" required maxlength="200" class="wb-input" /></div>
    <div class="wb-field"><label for="wb-tf-desc" data-i18n="wb_notes">Description &amp; Notes</label><textarea id="wb-tf-desc" rows="3" maxlength="4000" class="wb-textarea"></textarea></div>
    <div class="wb-form-grid">
      <div class="wb-field"><label for="wb-tf-col" data-i18n="wb_column">Column</label><select id="wb-tf-col" class="wb-select"></select></div>
      <div class="wb-field"><label for="wb-tf-project" data-i18n="wb_project">Project</label><select id="wb-tf-project" class="wb-select"></select></div>
      <div class="wb-field"><label for="wb-tf-priority" data-i18n="wb_priority">Priority</label><select id="wb-tf-priority" class="wb-select"><option value="low" data-i18n="wb_prio_low">Low</option><option value="medium" data-i18n="wb_prio_medium">Medium</option><option value="high" data-i18n="wb_prio_high">High</option><option value="urgent" data-i18n="wb_prio_urgent">Urgent</option></select></div>
      <div class="wb-field"><label for="wb-tf-recur" data-i18n="wb_recurrence">Recurrence</label><select id="wb-tf-recur" class="wb-select"><option value="none" data-i18n="wb_rec_none">One-time</option><option value="daily" data-i18n="wb_rec_daily">Daily</option><option value="weekly" data-i18n="wb_rec_weekly">Weekly</option><option value="monthly" data-i18n="wb_rec_monthly">Monthly</option></select></div>
      <div class="wb-field"><label for="wb-tf-due" data-i18n="wb_due_date">Due Date</label><input id="wb-tf-due" type="date" class="wb-input" /></div>
      <div class="wb-field"><label for="wb-tf-tags" data-i18n="wb_tags">Tags (comma-separated)</label><input id="wb-tf-tags" type="text" maxlength="180" placeholder="report, review" class="wb-input" /></div>
      <div class="wb-field"><label for="wb-tf-start" data-i18n="wb_start_time">Start Time (optional)</label><input id="wb-tf-start" type="time" class="wb-input" /></div>
      <div class="wb-field"><label for="wb-tf-end" data-i18n="wb_end_time">End Time (optional)</label><input id="wb-tf-end" type="time" class="wb-input" /></div>
    </div>
    <div class="wb-field">
      <label for="wb-tf-sub-input" data-i18n="wb_subtasks">Checklist / Subtasks</label>
      <div id="wb-tf-subtasks" style="display:flex;flex-direction:column;gap:0.35rem"></div>
      <div style="display:flex;gap:0.4rem;margin-top:0.25rem">
        <input id="wb-tf-sub-input" type="text" maxlength="180" placeholder="Add subtask..." data-i18n-placeholder="wb_add_sub_ph" class="wb-input" style="flex:1" />
        <button id="wb-tf-sub-add" type="button" data-i18n="wb_add_btn" class="wb-btn wb-btn-sm">Add</button>
      </div>
    </div>
    <div id="wb-tf-links" hidden style="display:flex;flex-wrap:wrap;gap:0.45rem;font-size:calc(0.8125rem * var(--ui-scale, 1));color:var(--text-muted)"></div>
    <div style="display:flex;justify-content:space-between;align-items:center;gap:0.5rem;padding-top:0.65rem;border-top:1px solid var(--border-subtle);flex-wrap:wrap">
      <div style="display:flex;gap:0.45rem">
        <button id="wb-tf-delete" type="button" hidden data-i18n="delete_btn" class="wb-btn wb-btn-danger">Delete</button>
        <button id="wb-tf-ask-chat" type="button" hidden data-i18n="sp_ask_in_chat" class="wb-btn">Ask in Split Chat</button>
      </div>
      <div style="display:flex;gap:0.5rem;margin-inline-start:auto">
        <button type="button" data-close-dialog="work-task-modal" data-i18n="cancel" class="wb-btn">Cancel</button>
        <button type="submit" data-i18n="save" class="wb-btn wb-btn-primary">Save</button>
      </div>
    </div>
  </form>
</dialog>

<dialog id="work-project-modal" closedby="any" aria-labelledby="wb-proj-modal-title" class="wb-dialog">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;border-bottom:1px solid var(--border-subtle);padding-bottom:0.7rem">
    <h2 id="wb-proj-modal-title" data-i18n="wb_proj_modal_new" style="margin:0;font-size:calc(1.125rem * var(--ui-scale, 1));font-weight:600">New Project</h2>
    <button type="button" data-close-dialog="work-project-modal" aria-label="Close project dialog" class="wb-icon-btn">✕</button>
  </div>
  <form id="wb-project-form" style="display:flex;flex-direction:column;gap:0.8rem">
    <input id="wb-pf-id" type="hidden" value="" />
    <div class="wb-field"><label for="wb-pf-title" data-i18n="wb_proj_name">Project Name</label><input id="wb-pf-title" type="text" required maxlength="100" class="wb-input" /></div>
    <div class="wb-field"><label for="wb-pf-desc" data-i18n="wb_proj_goal">Goal / Summary</label><textarea id="wb-pf-desc" rows="3" maxlength="1000" class="wb-textarea"></textarea></div>
    <div class="wb-form-grid">
      <div class="wb-field"><label for="wb-pf-status" data-i18n="wb_status">Status</label><select id="wb-pf-status" class="wb-select"><option value="active" data-i18n="wb_st_active">Active</option><option value="on_hold" data-i18n="wb_st_hold">On Hold</option><option value="completed" data-i18n="wb_st_done">Completed</option></select></div>
      <div class="wb-field"><label for="wb-pf-color" data-i18n="wb_color">Color</label><input id="wb-pf-color" type="color" value="#4BB8E8" class="wb-input" style="height:2.4rem;padding:0.2rem" /></div>
      <div class="wb-field"><label for="wb-pf-target" data-i18n="wb_target_date">Target Date</label><input id="wb-pf-target" type="date" class="wb-input" /></div>
      <div class="wb-field"><label for="wb-pf-hours" data-i18n="wb_target_hours">Planned Hours</label><input id="wb-pf-hours" type="number" min="0" max="10000" step="0.5" value="0" class="wb-input" /></div>
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center;gap:0.5rem;padding-top:0.65rem;border-top:1px solid var(--border-subtle)">
      <button id="wb-pf-delete" type="button" hidden data-i18n="delete_btn" class="wb-btn wb-btn-danger">Delete</button>
      <div style="display:flex;gap:0.5rem;margin-inline-start:auto">
        <button type="button" data-close-dialog="work-project-modal" data-i18n="cancel" class="wb-btn">Cancel</button>
        <button type="submit" data-i18n="save" class="wb-btn wb-btn-primary">Save</button>
      </div>
    </div>
  </form>
</dialog>

<dialog id="work-event-modal" closedby="any" aria-labelledby="wb-ev-modal-title" class="wb-dialog">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;border-bottom:1px solid var(--border-subtle);padding-bottom:0.7rem">
    <h2 id="wb-ev-modal-title" data-i18n="wb_ev_modal_new" style="margin:0;font-size:calc(1.125rem * var(--ui-scale, 1));font-weight:600">New Calendar Event</h2>
    <button type="button" data-close-dialog="work-event-modal" aria-label="Close event dialog" class="wb-icon-btn">✕</button>
  </div>
  <form id="wb-event-form" style="display:flex;flex-direction:column;gap:0.8rem">
    <input id="wb-ef-id" type="hidden" value="" />
    <div class="wb-field"><label for="wb-ef-title" data-i18n="wb_task_title">Title</label><input id="wb-ef-title" type="text" required maxlength="200" class="wb-input" /></div>
    <div class="wb-form-grid">
      <div class="wb-field"><label for="wb-ef-date" data-i18n="wb_date">Date</label><input id="wb-ef-date" type="date" required class="wb-input" /></div>
      <div class="wb-field"><label for="wb-ef-kind" data-i18n="wb_ev_kind">Type</label><select id="wb-ef-kind" class="wb-select"><option value="event" data-i18n="wb_kind_event">Event</option><option value="focus" data-i18n="wb_kind_focus">Focus Block</option><option value="milestone" data-i18n="wb_kind_milestone">Milestone</option><option value="deadline" data-i18n="wb_kind_deadline">Deadline</option></select></div>
      <div class="wb-field"><label for="wb-ef-start" data-i18n="wb_start_time">Start Time (optional)</label><input id="wb-ef-start" type="time" class="wb-input" /></div>
      <div class="wb-field"><label for="wb-ef-end" data-i18n="wb_end_time">End Time (optional)</label><input id="wb-ef-end" type="time" class="wb-input" /></div>
    </div>
    <div class="wb-field"><label for="wb-ef-project" data-i18n="wb_project">Project</label><select id="wb-ef-project" class="wb-select"></select></div>
    <div class="wb-field"><label for="wb-ef-notes" data-i18n="wb_notes">Notes</label><textarea id="wb-ef-notes" rows="3" maxlength="2000" class="wb-textarea"></textarea></div>
    <div style="display:flex;justify-content:space-between;align-items:center;gap:0.5rem;padding-top:0.65rem;border-top:1px solid var(--border-subtle)">
      <button id="wb-ef-delete" type="button" hidden data-i18n="delete_btn" class="wb-btn wb-btn-danger">Delete</button>
      <div style="display:flex;gap:0.5rem;margin-inline-start:auto">
        <button type="button" data-close-dialog="work-event-modal" data-i18n="cancel" class="wb-btn">Cancel</button>
        <button type="submit" data-i18n="save" class="wb-btn wb-btn-primary">Save</button>
      </div>
    </div>
  </form>
</dialog>

<dialog id="work-extract-modal" closedby="any" aria-labelledby="wb-ext-modal-title" class="wb-dialog">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;border-bottom:1px solid var(--border-subtle);padding-bottom:0.7rem">
    <h2 id="wb-ext-modal-title" data-i18n="wb_extract_title" style="margin:0;font-size:calc(1.125rem * var(--ui-scale, 1));font-weight:600">Extract Tasks to Board</h2>
    <button type="button" data-close-dialog="work-extract-modal" aria-label="Close extract dialog" class="wb-icon-btn">✕</button>
  </div>
  <form id="wb-extract-form" style="display:flex;flex-direction:column;gap:0.8rem">
    <div class="wb-field"><label for="wb-ext-text" data-i18n="wb_ext_text_lbl">Meeting Notes, Report, or Action Items</label><textarea id="wb-ext-text" rows="6" required maxlength="40000" placeholder="- [ ] Review Q2 report&#10;- [ ] Prepare presentation slides by 2026-06-01" class="wb-textarea"></textarea></div>
    <div class="wb-form-grid">
      <div class="wb-field"><label for="wb-ext-project" data-i18n="wb_project">Project</label><select id="wb-ext-project" class="wb-select"></select></div>
      <div class="wb-field"><label for="wb-ext-col" data-i18n="wb_column">Target Column</label><select id="wb-ext-col" class="wb-select"></select></div>
    </div>
    <label for="wb-ext-use-ai" style="display:flex;align-items:center;justify-content:space-between;gap:0.75rem;padding:0.65rem 0.85rem;border-radius:0.75rem;background:var(--surface-soft);cursor:pointer">
      <span data-i18n="wb_ext_ai_lbl" style="font-size:calc(0.875rem * var(--ui-scale, 1))">Use AI to detect tasks &amp; priorities (auto-falls back offline)</span>
      <input id="wb-ext-use-ai" type="checkbox" switch role="switch" checked />
    </label>
    <div style="display:flex;justify-content:flex-end;gap:0.5rem;padding-top:0.65rem;border-top:1px solid var(--border-subtle)">
      <button type="button" data-close-dialog="work-extract-modal" data-i18n="cancel" class="wb-btn">Cancel</button>
      <button id="wb-ext-submit" type="submit" data-i18n="wb_extract_btn" class="wb-btn wb-btn-primary">Extract Tasks</button>
    </div>
  </form>
</dialog>"""
