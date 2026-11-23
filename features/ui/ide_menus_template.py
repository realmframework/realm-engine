"""IDE workbench context popovers (File, Folder, Tab), reusable Name Prompt dialog, and Highlight-to-Copilot pill."""

IDE_MENUS_HTML: str = (
    '<div id="ft-file-menu" popover="auto" class="rail-popover" aria-label="File actions"><div focusgroup="menu nomemory" class="bp-menu-group">'
    '<button type="button" data-fm-act="open-pin" class="shell-pop-item"><span data-i18n="ft_act_open_tab">Open in new tab</span></button>'
    '<button type="button" data-fm-act="copilot" class="shell-pop-item"><span data-i18n="ft_act_copilot">Open &amp; ask Copilot</span></button>'
    '<div class="ft-pop-sep"></div>'
    '<button type="button" data-fm-act="rename" data-fm-writable="1" class="shell-pop-item"><span data-i18n="ft_act_rename">Rename…</span></button>'
    '<button type="button" data-fm-act="duplicate" data-fm-writable="1" class="shell-pop-item"><span data-i18n="ft_act_duplicate">Duplicate</span></button>'
    '<button type="button" data-fm-act="move" data-fm-writable="1" class="shell-pop-item"><span data-i18n="ft_act_move">Move to folder…</span></button>'
    '<button type="button" data-fm-act="copy-path" class="shell-pop-item"><span data-i18n="ft_act_copy">Copy path</span></button>'
    '<button type="button" data-fm-act="anonymize" data-fm-writable="1" class="shell-pop-item"><span data-i18n="ft_act_anon">Anonymize (GDPR)</span></button>'
    '<div data-fm-writable="1" class="shell-pop-sep"><button type="button" data-fm-act="delete" class="shell-pop-item ft-pop-danger"><span data-i18n="delete_btn">Delete</span></button></div>'
    "</div></div>"
    '<div id="ft-folder-menu" popover="auto" class="rail-popover" aria-label="Folder actions"><div focusgroup="menu nomemory" class="bp-menu-group">'
    '<button type="button" data-folder-act="new-file" data-fm-writable="1" class="shell-pop-item"><span data-i18n="ft_new_file">New file…</span></button>'
    '<button type="button" data-folder-act="new-note" data-fm-writable="1" class="shell-pop-item"><span data-i18n="ft_fld_new_note">New note here</span></button>'
    '<button type="button" data-folder-act="new-subfolder" data-fm-writable="1" class="shell-pop-item"><span data-i18n="ft_fld_new_sub">New subfolder…</span></button>'
    '<button type="button" data-folder-act="rename" data-fm-writable="1" class="shell-pop-item"><span data-i18n="ft_fld_rename">Rename folder…</span></button>'
    '<button type="button" data-folder-act="copy-path" class="shell-pop-item"><span data-i18n="ft_act_copy">Copy path</span></button>'
    '<div data-fm-writable="1" class="shell-pop-sep"><button type="button" data-folder-act="delete" class="shell-pop-item ft-pop-danger"><span data-i18n="ft_fld_delete">Delete folder</span></button></div>'
    "</div></div>"
    '<div id="tab-context-menu" popover="auto" class="rail-popover" aria-label="Tab actions"><div focusgroup="menu nomemory" class="bp-menu-group">'
    '<button id="tcm-pin-btn" type="button" data-tcm-act="pin" class="shell-pop-item"><span data-i18n="tcm_pin">Pin tab</span></button>'
    '<div class="ft-pop-sep"></div>'
    '<button id="tcm-close-btn" type="button" data-tcm-act="close" class="shell-pop-item"><span data-i18n="tcm_close">Close</span></button>'
    '<button type="button" data-tcm-act="close-others" class="shell-pop-item"><span data-i18n="tcm_close_others">Close others</span></button>'
    '<button type="button" data-tcm-act="close-right" class="shell-pop-item"><span data-i18n="tcm_close_right">Close to the right</span></button>'
    '<button type="button" data-tcm-act="close-saved" class="shell-pop-item"><span data-i18n="tcm_close_saved">Close saved</span></button>'
    '<div class="shell-pop-sep"><button type="button" data-tcm-act="close-all" class="shell-pop-item ft-pop-danger"><span data-i18n="tcm_close_all">Close all</span></button></div>'
    "</div></div>"
    '<dialog id="name-prompt-modal" closedby="any" aria-labelledby="np-title" class="m-auto w-[calc(100%_-_2rem)] max-w-md rounded-2xl bg-[#0B1020] text-[#EEF2F8] border border-white/15 p-6 shadow-2xl">'
    '<h2 id="np-title" class="text-lg font-semibold mb-3">Rename</h2>'
    '<form id="name-prompt-form" class="flex flex-col gap-3">'
    '<label id="np-label" for="np-input" class="text-xs text-[#A0B0C8]">New name</label>'
    '<input id="np-input" type="text" required maxlength="100" autocomplete="off" spellcheck="false" class="rounded-lg bg-[#04060F] border border-white/15 px-3 py-2 text-sm text-[#EEF2F8] outline-none focus:border-[#4BB8E8]"/>'
    '<p id="np-error" role="status" class="text-xs text-[#FCA5A5] min-h-[1rem]"></p>'
    '<div class="flex justify-end gap-2.5">'
    '<button id="np-cancel-btn" type="button" data-i18n="cancel" class="rounded-xl border border-white/15 px-4 py-2 text-sm">Cancel</button>'
    '<button id="np-submit-btn" type="submit" class="rounded-xl bg-[#4BB8E8] text-[#04060F] px-4 py-2 text-sm font-semibold">Confirm</button>'
    "</div></form></dialog>"
    '<div id="cf-sel-pill" hidden role="toolbar" aria-label="Selection Copilot actions" class="cf-sel-pill">'
    '<button id="cf-sel-ask-btn" type="button" class="cf-sel-btn">✦ <span data-i18n="cp_sel_ask">Ask Copilot</span></button>'
    '<button id="cf-sel-edit-btn" type="button" class="cf-sel-btn cf-sel-btn-primary">✦ <span data-i18n="cp_sel_edit">Edit Selection</span></button>'
    "</div>"
)
