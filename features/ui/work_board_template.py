"""HTML shell for the Work Board (Projects, Kanban, Task List, and Local Calendar)."""

WORK_BOARD_HTML: str = r"""<section id="work-board-view" class="wb-view hidden" aria-label="Projects, Kanban and Calendar">
  <header class="wb-header">
    <div class="wb-title-row">
      <h1 id="wb-heading" data-i18n="wb_title" class="wb-title">Board &amp; Calendar</h1>
      <div id="wb-stats" class="wb-stat-strip" aria-live="polite"></div>
    </div>
    <div class="wb-controls">
      <select id="wb-project-filter" aria-label="Filter by project" data-i18n-aria-label="wb_filter_project" class="wb-select">
        <option value="" data-i18n="wb_all_projects">All Projects</option>
      </select>
      <button id="wb-more-btn" type="button" popovertarget="wb-more-menu" aria-expanded="false" aria-label="More actions" title="More actions" data-i18n-aria-label="wb_more_actions" data-i18n-title="wb_more_actions" class="wb-btn">···</button>
      <div id="wb-more-menu" popover="auto" class="rail-popover" aria-label="Board actions">
        <button id="wb-extract-open-btn" type="button" data-i18n="wb_extract_btn" class="shell-pop-item">Extract Tasks</button>
        <button id="wb-sync-vault-btn" type="button" data-i18n="wb_sync_btn" class="shell-pop-item">Sync to Library</button>
      </div>
      <button id="wb-add-task-btn" type="button" data-i18n="wb_new_task" class="wb-btn wb-btn-primary">+ New Task</button>
    </div>
  </header>

  <div id="wb-tablist" role="tablist" aria-label="Work Board views" class="wb-tabs">
    <button type="button" role="tab" id="wb-tab-kanban" data-wb-tab="kanban" aria-selected="true" data-i18n="wb_tab_kanban">Kanban</button>
    <button type="button" role="tab" id="wb-tab-tasks" data-wb-tab="tasks" aria-selected="false" data-i18n="wb_tab_tasks">Tasks</button>
    <button type="button" role="tab" id="wb-tab-calendar" data-wb-tab="calendar" aria-selected="false" data-i18n="wb_tab_calendar">Calendar</button>
    <button type="button" role="tab" id="wb-tab-projects" data-wb-tab="projects" aria-selected="false" data-i18n="wb_tab_projects">Projects</button>
  </div>

  <div id="wb-panel-kanban" role="tabpanel" aria-labelledby="wb-tab-kanban">
    <div id="wb-kanban-columns" class="wb-kanban-wrap"></div>
  </div>

  <div id="wb-panel-tasks" role="tabpanel" aria-labelledby="wb-tab-tasks" hidden>
    <form id="wb-quick-task-form" class="wb-task-quickbar">
      <input id="wb-quick-title" type="text" required maxlength="200" aria-label="New task title" data-i18n-aria-label="wb_task_title" placeholder="Add a task..." data-i18n-placeholder="wb_quick_ph" class="wb-input" />
      <select id="wb-quick-priority" aria-label="Priority" data-i18n-aria-label="wb_priority" class="wb-select">
        <option value="medium" data-i18n="wb_prio_medium">Medium</option>
        <option value="low" data-i18n="wb_prio_low">Low</option>
        <option value="high" data-i18n="wb_prio_high">High</option>
        <option value="urgent" data-i18n="wb_prio_urgent">Urgent</option>
      </select>
      <input id="wb-quick-due" type="date" aria-label="Due date" data-i18n-aria-label="wb_due_date" class="wb-input" />
      <select id="wb-quick-project" aria-label="Project" data-i18n-aria-label="wb_project" class="wb-select">
        <option value="" data-i18n="wb_no_project">No Project</option>
      </select>
      <button type="submit" data-i18n="wb_add_btn" class="wb-btn wb-btn-primary">Add</button>
    </form>
    <div class="wb-list-toolbar">
      <div id="wb-task-filters" role="group" aria-label="Task filters" class="wb-filter-pills">
        <button type="button" data-wb-filter="open" aria-pressed="true" data-i18n="wb_f_open" class="wb-pill-btn">All Open</button>
        <button type="button" data-wb-filter="today" aria-pressed="false" data-i18n="wb_f_today" class="wb-pill-btn">Today</button>
        <button type="button" data-wb-filter="overdue" aria-pressed="false" data-i18n="wb_f_overdue" class="wb-pill-btn">Overdue</button>
        <button type="button" data-wb-filter="upcoming" aria-pressed="false" data-i18n="wb_f_upcoming" class="wb-pill-btn">Upcoming</button>
        <button type="button" data-wb-filter="done" aria-pressed="false" data-i18n="wb_f_done" class="wb-pill-btn">Completed</button>
      </div>
      <div class="wb-controls">
        <input id="wb-task-search" type="search" aria-label="Search tasks" data-i18n-aria-label="wb_search_tasks" placeholder="Filter tasks..." data-i18n-placeholder="wb_search_tasks" class="wb-input" />
      </div>
    </div>
    <div id="wb-task-list"></div>
  </div>

  <div id="wb-panel-calendar" role="tabpanel" aria-labelledby="wb-tab-calendar" hidden>
    <div class="wb-cal-toolbar">
      <div class="wb-controls">
        <button id="wb-cal-prev" type="button" aria-label="Previous period" class="wb-btn wb-btn-sm">‹</button>
        <button id="wb-cal-today" type="button" data-i18n="wb_today" class="wb-btn wb-btn-sm">Today</button>
        <button id="wb-cal-next" type="button" aria-label="Next period" class="wb-btn wb-btn-sm">›</button>
        <strong id="wb-cal-label" style="font-size:calc(1.05rem * var(--ui-scale, 1));margin-inline-start:0.35rem"></strong>
      </div>
      <div class="wb-controls">
        <div role="group" aria-label="Calendar view mode" class="wb-filter-pills">
          <button type="button" data-cal-mode="month" aria-pressed="true" data-i18n="wb_cal_month" class="wb-pill-btn">Month</button>
          <button type="button" data-cal-mode="week" aria-pressed="false" data-i18n="wb_cal_week" class="wb-pill-btn">Week</button>
          <button type="button" data-cal-mode="day" aria-pressed="false" data-i18n="wb_cal_day" class="wb-pill-btn">Day</button>
        </div>
        <button id="wb-cal-new-ev-btn" type="button" data-i18n="wb_new_event" class="wb-btn wb-btn-sm wb-btn-primary">+ Event</button>
        <button id="wb-cal-export-ics" type="button" data-i18n="wb_export_ics" class="wb-btn wb-btn-sm">Export .ics</button>
        <button id="wb-cal-import-ics-btn" type="button" data-i18n="wb_import_ics" class="wb-btn wb-btn-sm">Import .ics</button>
        <input id="wb-cal-import-ics-file" type="file" accept=".ics,text/calendar" hidden tabindex="-1" aria-hidden="true" />
      </div>
    </div>
    <div id="wb-cal-canvas"></div>
  </div>

  <div id="wb-panel-projects" role="tabpanel" aria-labelledby="wb-tab-projects" hidden>
    <div class="wb-list-toolbar">
      <p data-i18n="wb_projects_sub" style="margin:0;color:var(--text-muted);font-size:calc(0.875rem * var(--ui-scale, 1))">Organize goals, milestones, linked documents, and Kanban cards by project.</p>
      <button id="wb-new-project-btn" type="button" data-i18n="wb_new_project" class="wb-btn wb-btn-primary">+ New Project</button>
    </div>
    <div id="wb-projects-grid" class="wb-projects-grid"></div>
  </div>
</section>"""
