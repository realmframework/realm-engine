"""HTML markup for the integrated Bottom Panel Terminal pane."""

TERMINAL_PANE_HTML: str = (
    '<div id="bottom-terminal-pane" hidden class="term-pane" role="region" aria-label="Integrated Terminal" data-i18n-aria-label="term_tab">'
    '<div class="term-bar">'
    '<div class="term-sessions">'
    '<div id="term-session-tabs" role="tablist" aria-label="Terminal sessions" class="term-sessions"></div>'
    '<button id="term-new-btn" type="button" class="wb-icon-btn ft-act-btn" title="New terminal" aria-label="New terminal" data-i18n-title="term_new" data-i18n-aria-label="term_new">+</button>'
    "</div>"
    '<div class="term-bar-right">'
    '<span id="term-cwd-pill" class="term-cwd" title="Working directory"></span>'
    '<button id="term-int-btn" type="button" class="wb-btn wb-btn-sm" title="Send Ctrl+C interrupt" data-i18n="term_stop">Ctrl+C</button>'
    '<button id="term-clear-btn" type="button" class="wb-btn wb-btn-sm" data-i18n="term_clear">Clear</button>'
    '<button id="term-copilot-btn" type="button" class="wb-btn wb-btn-sm" data-i18n-title="term_copilot_t" title="Send terminal output to Copilot">✦ <span data-i18n="md_copilot_btn">Copilot</span></button>'
    "</div></div>"
    '<pre id="term-output" class="term-out" tabindex="0" aria-live="off"></pre>'
    '<form id="term-form" class="term-input-row">'
    '<span class="term-prompt" aria-hidden="true">❯</span>'
    '<input id="term-input" type="text" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" placeholder="Run a command (Enter to send, ↑/↓ history, Ctrl+C interrupt)…" data-i18n-placeholder="term_ph" aria-label="Terminal command input" class="term-input"/>'
    "</form>"
    "</div>"
)
