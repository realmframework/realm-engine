"""Phase 6 modal: Offline Audio Briefing player with explicit WebKit-safe layout CSS."""

POWER_STYLES_CSS: str = r"""<style>
#briefing-modal { inline-size: min(40rem, calc(100vw - 2rem)); max-block-size: 86vh; overflow: hidden; }
#briefing-modal[open] { display: flex; flex-direction: column; }
#br-output-wrap { flex: 1 1 auto; min-block-size: 12rem; max-block-size: 52vh; overflow-y: auto; display: flex; flex-direction: column; gap: 0.75rem; }
#br-output-wrap[hidden], #br-audio-box[hidden] { display: none !important; }
</style>"""

POWER_MODAL_HTML: str = r"""<dialog id="briefing-modal" closedby="any" aria-labelledby="briefing-modal-title" class="m-auto rounded-2xl bg-[#0B1020] text-[#EEF2F8] border border-white/15 p-6 shadow-2xl gap-4">
  <div class="flex items-center justify-between gap-3 border-b border-white/10 pb-3 shrink-0">
    <div>
      <h2 id="briefing-modal-title" data-i18n="br_title" class="text-lg font-semibold text-[#EEF2F8]">Offline Audio Briefing</h2>
      <p data-i18n="br_sub" class="text-xs text-[#738196] mt-0.5">Generate a private spoken briefing locally using Phonon TTS — zero cloud uploads.</p>
    </div>
    <button id="close-briefing-modal" type="button" aria-label="Close briefing dialog" class="h-8 w-8 rounded-full text-[#738196] hover:text-[#EEF2F8] hover:bg-white/[0.06] flex items-center justify-center text-sm shrink-0">✕</button>
  </div>
  <div class="comfort-two-col bg-[#04060F] p-1 rounded-xl border border-white/10 shrink-0" role="group" aria-label="Briefing style">
    <button id="br-mode-solo" type="button" aria-pressed="true" data-br-mode="solo" data-i18n="br_mode_solo" class="py-1.5 px-3 rounded-lg text-xs font-medium bg-[#4BB8E8] text-[#04060F] transition">Solo (Active Agent)</button>
    <button id="br-mode-duo" type="button" aria-pressed="false" data-br-mode="duo" data-i18n="br_mode_duo" class="py-1.5 px-3 rounded-lg text-xs font-medium text-[#A0B0C8] hover:text-[#EEF2F8] transition">Two-Voice Duo (Blomkvist &amp; Lisbeth)</button>
  </div>
  <div class="flex items-center justify-between gap-2 flex-wrap shrink-0">
    <p id="br-status" role="status" class="text-xs text-[#A0B0C8]"></p>
    <button id="br-generate-btn" type="button" data-i18n="br_gen_btn" class="px-4 py-2 rounded-xl bg-[#4BB8E8] text-[#04060F] text-xs font-semibold hover:brightness-110 transition">Generate Offline Briefing</button>
  </div>
  <div id="br-output-wrap" hidden>
    <div id="br-audio-box" hidden class="rounded-xl bg-[#04060F] border border-white/10 p-3 flex flex-col gap-2">
      <audio id="br-audio-player" controls aria-details="briefing-transcript" class="w-full"></audio>
      <div class="flex items-center justify-end gap-2">
        <button id="br-download-wav" type="button" data-i18n="br_dl_wav" class="px-3 py-1 rounded-lg border border-white/15 hover:border-[#4BB8E8] text-xs text-[#EEF2F8]">↓ Download Audio (.wav)</button>
        <button id="br-download-md" type="button" data-i18n="br_dl_md" class="px-3 py-1 rounded-lg border border-white/15 hover:border-[#4BB8E8] text-xs text-[#A0B0C8] hover:text-[#EEF2F8]">↓ Transcript (.md)</button>
      </div>
    </div>
    <details id="briefing-transcript" open class="rounded-xl bg-[#04060F] border border-white/10 p-4">
      <summary data-i18n="br_transcript" class="cursor-pointer text-xs font-mono uppercase tracking-wider text-[#4BB8E8]">View Transcript</summary>
      <div id="br-transcript-body" class="mt-3 md-body text-sm text-[#C8D4E6] leading-relaxed flex flex-col gap-2.5"></div>
    </details>
  </div>
</dialog>"""
