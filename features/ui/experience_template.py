"""Plain-language interface choices, workspace backups and local AI downloads."""

BACKUP_PANEL = """<section class="rounded-xl border border-white/10 p-4" aria-labelledby="backup-heading">
<h3 id="backup-heading" data-i18n="backup_title" class="text-sm font-medium">Backup &amp; Restore</h3>
<p id="backup-scope-note" class="text-xs text-[#A0B0C8] mt-2"></p>
<p data-i18n="backup_desc" class="text-xs text-[#A0B0C8] mt-2">Save this workspace’s guides, folders, settings and chats in one file. Keep your backup private: it contains your document and chat text.</p>
<div class="flex flex-wrap gap-3 mt-3"><button id="download-backup-btn" type="button" data-i18n="backup_download" class="rounded-lg border border-white/15 px-3 py-2 text-xs">↓ Download Backup (.zip)</button>
<button id="restore-backup-btn" type="button" data-i18n="backup_restore" class="rounded-lg border border-white/15 px-3 py-2 text-xs">↑ Restore from Backup (.zip)</button></div>
<label for="backup-restore-file" class="visually-hidden">Choose a ZIP workspace backup</label><input id="backup-restore-file" name="backup" type="file" accept=".zip,application/zip" hidden tabindex="-1" aria-hidden="true"/>
<p data-i18n="backup_restore_note" class="text-xs text-[#738196] mt-3">Restore adds missing guides and chats to this workspace. For a different version of an existing file or chat, create a new workspace first. Your privacy lock and tighter budget caps are kept.</p>
<p id="backup-status" role="status" class="text-xs text-[#A0B0C8] mt-2"></p>
</section>"""

INSTALLER_PANEL = """<section class="rounded-xl border border-white/10 p-4" aria-labelledby="local-install-heading">
<h3 id="local-install-heading" data-i18n="ob_install_head" class="text-sm font-medium">Ollama Search Helper (Optional)</h3>
<p id="local-install-help" data-i18n="ob_install_help" class="text-xs text-[#A0B0C8] mt-2">If you use Ollama, install the local search helper (~274 MB) for semantic hybrid search. Your chat models are discovered live from Ollama.</p>
<p id="local-model-recommendation" class="text-xs text-[#A0B0C8] mt-2"></p>
<button id="download-local-model-btn" type="button" data-i18n="ob_install_btn" aria-describedby="local-install-help" class="mt-3 rounded-lg border border-[#4BB8E8]/40 px-3 py-2 text-xs text-[#4BB8E8]">Install Ollama Search Helper</button>
<p id="local-install-status" role="status" class="text-xs text-[#A0B0C8] mt-2"></p>
</section>"""

AREA_TEMPLATE_SELECT = """<label for="area-template" data-i18n="area_start_with" class="text-xs text-[#A0B0C8]">Start with</label>
<select id="area-template" name="template" aria-describedby="area-template-help" class="rounded-lg bg-[#04060F] border border-white/15 px-3 py-2 text-sm">
<option value="blank" data-i18n="area_tpl_blank">Blank Folder</option><option value="starter" data-i18n="area_tpl_starter">REALM Starter Guide</option><option value="care" data-i18n="area_tpl_care">Care &amp; Medical Docs</option><option value="finance" data-i18n="area_tpl_finance">Personal &amp; Finance</option><option value="study" data-i18n="area_tpl_study">Study &amp; Homework</option></select>
<p id="area-template-help" data-i18n="area_tpl_help" class="text-xs text-[#738196]">Templates create a few empty folders. Care and Finance also keep AI on this computer for privacy.</p>"""
