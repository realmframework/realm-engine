"""HTML template for Superfocus Engine (Goal Seasons, Deep Focus Modal, and AI Weekly Planner)."""

FOCUS_VIEW_HTML: str = r"""<section id="focus-view" class="wb-view hidden" aria-label="Focus and Goal Seasons">
  <header class="wb-header">
    <div class="wb-title-row">
      <h1 data-i18n="foc_title" class="wb-title">Focus &amp; Goals</h1>
      <div id="foc-stats" class="wb-stat-strip" aria-live="polite"></div>
    </div>
    <div class="wb-controls">
      <button id="foc-plan-btn" type="button" data-i18n="foc_weekly_plan" class="wb-btn">AI Weekly Plan</button>
      <button id="foc-new-goal-btn" type="button" data-i18n="foc_new_goal" class="wb-btn">+ Goal Season</button>
      <button id="foc-start-deep-btn" type="button" data-i18n="foc_start_deep" class="wb-btn wb-btn-primary">Start Deep Focus</button>
    </div>
  </header>

  <section id="foc-plan-box" hidden class="plan-card" aria-label="Proposed weekly focus plan">
    <div style="display:flex;align-items:center;justify-content:space-between;gap:0.5rem;flex-wrap:wrap">
      <strong data-i18n="foc_plan_head" style="font-size:calc(1rem * var(--ui-scale,1))">Suggested Deep Focus Week</strong>
      <div class="wb-controls">
        <button id="foc-plan-accept-btn" type="button" data-i18n="foc_plan_accept" class="wb-btn wb-btn-sm wb-btn-primary">Accept into Calendar</button>
        <button id="foc-plan-dismiss-btn" type="button" aria-label="Dismiss weekly plan" class="wb-icon-btn">✕</button>
      </div>
    </div>
    <div id="foc-plan-list" style="display:flex;flex-direction:column;gap:0.4rem"></div>
  </section>

  <div>
    <h2 data-i18n="foc_seasons_head" style="margin:0 0 0.7rem;font-size:calc(1.05rem * var(--ui-scale,1));font-weight:600">Goal Seasons</h2>
    <div id="foc-goals-grid" class="goal-grid"></div>
  </div>

  <div>
    <h2 data-i18n="foc_recent_head" style="margin:0 0 0.7rem;font-size:calc(1.05rem * var(--ui-scale,1));font-weight:600">Recent Deep Focus Sessions</h2>
    <div id="foc-sessions-list"></div>
  </div>
</section>"""

FOCUS_MODALS_HTML: str = r"""<dialog id="deep-focus-modal" closedby="any" aria-labelledby="df-modal-title" class="focus-dialog">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.85rem;border-bottom:1px solid var(--border-subtle);padding-bottom:0.65rem">
    <h2 id="df-modal-title" data-i18n="foc_deep_title" style="margin:0;font-size:calc(1.15rem * var(--ui-scale,1));font-weight:600">Deep Focus Session</h2>
    <button id="df-close-btn" type="button" aria-label="Close Deep Focus" class="wb-icon-btn">✕</button>
  </div>
  <div style="display:flex;flex-direction:column;gap:0.9rem">
    <div class="wb-form-grid">
      <div class="wb-field"><label for="df-label" data-i18n="foc_what_focus">What are you focusing on?</label><input id="df-label" type="text" maxlength="180" value="Deep Work Sprint" class="wb-input" /></div>
      <div class="wb-field"><label for="df-goal-select" data-i18n="foc_goal_link">Linked Goal Season</label><select id="df-goal-select" class="wb-select"></select></div>
    </div>
    <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:0.4rem" role="group" aria-label="Focus duration presets">
      <button type="button" data-df-mins="25" aria-pressed="false" class="wb-pill-btn">25 min</button>
      <button type="button" data-df-mins="45" aria-pressed="true" class="wb-pill-btn">45 min</button>
      <button type="button" data-df-mins="60" aria-pressed="false" class="wb-pill-btn">60 min</button>
      <button type="button" data-df-mins="90" aria-pressed="false" class="wb-pill-btn">90 min</button>
    </div>
    <div class="focus-ring-wrapper">
      <progress id="df-progress" class="focus-ring" value="0" max="100" aria-label="Deep Focus session progress" aria-valuetext="45:00 remaining"></progress>
      <div class="focus-ring-content" aria-hidden="true">
        <span id="df-clock" class="focus-ring-time">45:00</span>
        <span id="df-state-lbl" data-i18n="foc_ready" class="focus-ring-sub">Ready</span>
      </div>
    </div>
    <div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:0.65rem;padding:0.7rem 0.9rem;border-radius:0.85rem;background:var(--surface-soft)">
      <div style="display:flex;align-items:center;gap:0.35rem;flex-wrap:wrap" role="group" aria-label="Ambient soundscape">
        <button type="button" data-df-sound="off" aria-pressed="true" data-i18n="foc_snd_off" class="wb-pill-btn">Silent</button>
        <button type="button" data-df-sound="brown" aria-pressed="false" data-i18n="foc_snd_brown" class="wb-pill-btn">Brown Noise</button>
        <button type="button" data-df-sound="rain" aria-pressed="false" data-i18n="foc_snd_rain" class="wb-pill-btn">Soft Rain</button>
        <button type="button" data-df-sound="drone" aria-pressed="false" data-i18n="foc_snd_drone" class="wb-pill-btn">Warm Drone</button>
      </div>
      <div style="display:flex;align-items:center;gap:0.4rem">
        <label for="df-vol" data-i18n="foc_vol" style="font-size:0.78rem;color:var(--text-muted)">Vol</label>
        <input id="df-vol" type="range" min="0" max="100" value="35" style="width:5.5rem" />
      </div>
    </div>
    <div id="df-controls-row" style="display:flex;justify-content:center;gap:0.6rem;flex-wrap:wrap">
      <button id="df-start-pause-btn" type="button" data-i18n="foc_begin" class="wb-btn wb-btn-primary">Begin Focus</button>
      <button id="df-finish-btn" type="button" data-i18n="foc_finish_log" class="wb-btn">Finish &amp; Log</button>
    </div>
    <form id="df-checkin-form" hidden style="display:flex;flex-direction:column;gap:0.75rem;padding-top:0.75rem;border-top:1px solid var(--border-subtle)">
      <div style="text-align:center;font-weight:600" data-i18n="foc_quality_prompt">How focused was this session? (1–5)</div>
      <div class="quality-row" role="group" aria-label="Focus quality rating">
        <button type="button" data-df-q="1" aria-pressed="false" class="quality-btn">1</button>
        <button type="button" data-df-q="2" aria-pressed="false" class="quality-btn">2</button>
        <button type="button" data-df-q="3" aria-pressed="false" class="quality-btn">3</button>
        <button type="button" data-df-q="4" aria-pressed="true" class="quality-btn">4</button>
        <button type="button" data-df-q="5" aria-pressed="false" class="quality-btn">5</button>
      </div>
      <div class="wb-field"><label for="df-reflection" data-i18n="foc_reflection">Quick note (auto-saved to Time Log)</label><input id="df-reflection" type="text" maxlength="600" placeholder="Key progress or takeaway..." class="wb-input" /></div>
      <div style="display:flex;justify-content:flex-end;gap:0.5rem">
        <button id="df-cancel-checkin" type="button" data-i18n="cancel" class="wb-btn">Cancel</button>
        <button type="submit" data-i18n="foc_save_session" class="wb-btn wb-btn-primary">Save Session &amp; Log Time</button>
      </div>
    </form>
  </div>
</dialog>

<dialog id="goal-season-modal" closedby="any" aria-labelledby="gs-modal-title" class="wb-dialog">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;border-bottom:1px solid var(--border-subtle);padding-bottom:0.7rem">
    <h2 id="gs-modal-title" data-i18n="foc_new_goal" style="margin:0;font-size:calc(1.125rem * var(--ui-scale,1));font-weight:600">New Goal Season</h2>
    <button type="button" data-m4-close="goal-season-modal" aria-label="Close goal dialog" class="wb-icon-btn">✕</button>
  </div>
  <form id="gs-form" style="display:flex;flex-direction:column;gap:0.8rem">
    <input id="gs-id" type="hidden" value="" />
    <div class="wb-field"><label for="gs-title" data-i18n="foc_goal_title">Goal Season Title</label><input id="gs-title" type="text" required maxlength="140" placeholder="e.g. Q4 Impact Program Delivery" class="wb-input" /></div>
    <div class="wb-field"><label for="gs-why" data-i18n="foc_goal_why">Why it matters</label><textarea id="gs-why" rows="2" maxlength="800" class="wb-textarea"></textarea></div>
    <div class="wb-form-grid">
      <div class="wb-field"><label for="gs-start" data-i18n="foc_start_date">Start Date</label><input id="gs-start" type="date" required class="wb-input" /></div>
      <div class="wb-field"><label for="gs-end" data-i18n="foc_end_date">End Date</label><input id="gs-end" type="date" required class="wb-input" /></div>
      <div class="wb-field"><label for="gs-hours" data-i18n="foc_target_hours">Target Focus Hours</label><input id="gs-hours" type="number" min="1" max="2000" step="1" value="24" class="wb-input" /></div>
      <div class="wb-field"><label for="gs-project" data-i18n="wb_project">Project</label><select id="gs-project" class="wb-select"></select></div>
    </div>
    <div class="wb-field"><label for="gs-milestones" data-i18n="foc_milestones">Weekly Milestones (one per line)</label><textarea id="gs-milestones" rows="3" maxlength="1500" class="wb-textarea"></textarea></div>
    <div style="display:flex;justify-content:space-between;align-items:center;gap:0.5rem;padding-top:0.65rem;border-top:1px solid var(--border-subtle)">
      <button id="gs-delete" type="button" hidden data-i18n="delete_btn" class="wb-btn wb-btn-danger">Delete</button>
      <div style="display:flex;gap:0.5rem;margin-inline-start:auto">
        <button type="button" data-m4-close="goal-season-modal" data-i18n="cancel" class="wb-btn">Cancel</button>
        <button type="submit" data-i18n="save" class="wb-btn wb-btn-primary">Save</button>
      </div>
    </div>
  </form>
</dialog>"""
