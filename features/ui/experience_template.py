"""Plain-language interface choices, workspace backups and local AI downloads."""

BACKUP_PANEL = """<section class="rounded-xl border border-white/10 p-4" aria-labelledby="backup-heading">
<h3 id="backup-heading" class="text-sm font-medium">Backup &amp; Restore</h3>
<p id="backup-scope-note" class="text-xs text-[#A0B0C8] mt-2"></p>
<p class="text-xs text-[#A0B0C8] mt-2">Save this workspace’s guides, folders, settings and chats in one file. Keep your backup private: it contains your document and chat text.</p>
<div class="flex flex-wrap gap-3 mt-3"><button id="download-backup-btn" type="button" class="rounded-lg border border-white/15 px-3 py-2 text-xs">↓ Download Backup (.zip)</button>
<button id="restore-backup-btn" type="button" class="rounded-lg border border-white/15 px-3 py-2 text-xs">↑ Restore from Backup (.zip)</button></div>
<label for="backup-restore-file" class="visually-hidden">Choose a ZIP workspace backup</label><input id="backup-restore-file" name="backup" type="file" accept=".zip,application/zip" class="visually-hidden"/>
<p class="text-xs text-[#738196] mt-3">Restore adds missing guides and chats to this workspace. For a different version of an existing file or chat, create a new workspace first. Your privacy lock and tighter budget caps are kept.</p>
<p id="backup-status" role="status" class="text-xs text-[#A0B0C8] mt-2"></p>
</section>"""

INSTALLER_PANEL = """<section class="rounded-xl border border-white/10 p-4" aria-labelledby="local-install-heading">
<h3 id="local-install-heading" class="text-sm font-medium">Set up AI on this computer</h3>
<p id="local-install-help" class="text-xs text-[#A0B0C8] mt-2">Open Ollama, then download the recommended AI. This downloads several GB from Ollama’s catalog and can take several minutes. Your documents stay on your computer.</p>
<p id="local-model-recommendation" class="text-xs text-[#A0B0C8] mt-2"></p>
<button id="download-local-model-btn" type="button" aria-describedby="local-install-help" class="mt-3 rounded-lg border border-[#4BB8E8]/40 px-3 py-2 text-xs text-[#4BB8E8]">Download Recommended Local AI</button>
<p id="local-install-status" role="status" class="text-xs text-[#A0B0C8] mt-2"></p>
</section>"""

AREA_TEMPLATE_SELECT = """<label for="area-template" class="text-xs text-[#A0B0C8]">Start with</label>
<select id="area-template" name="template" aria-describedby="area-template-help" class="rounded-lg bg-[#04060F] border border-white/15 px-3 py-2 text-sm">
<option value="blank">Blank Folder</option><option value="care">Care &amp; Medical Docs</option><option value="finance">Personal &amp; Finance</option><option value="study">Study &amp; Homework</option></select>
<p id="area-template-help" class="text-xs text-[#738196]">Templates create a few empty folders. Care and Finance also keep AI on this computer for privacy.</p>"""
