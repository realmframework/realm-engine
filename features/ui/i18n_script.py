"""Client-side multi-language dictionary and live UI translator (English, Deutsch, Español)."""

from features.ui.i18n_extra_script import I18N_EXTRA_SCRIPT
from features.ui.i18n_feedback_script import I18N_FEEDBACK_SCRIPT
from features.ui.i18n_guide_script import I18N_GUIDE_SCRIPT
from features.ui.i18n_settings_script import I18N_SETTINGS_SCRIPT
from features.ui.i18n_views_script import I18N_VIEWS_SCRIPT

I18N_SCRIPT: str = (
    r"""
let activeLanguage = "en";
const I18N = {
  en: {
    new_chat: "+ New Chat", library: "Library", graph_view: "Graph View", recent_chats: "Recent Chats", settings: "Settings",
    hero_greeting: "Where should we start?", ask_placeholder: "Ask anything...", more_ideas: "↻ More ideas",
    browse_guides_pre: "Browse all ", browse_guides_post: " documents →",
    seed_1: "Summarize the key points across my documents", seed_2: "Extract key action items and important details", seed_3: "What should I focus on next?",
    tab_workspace: "Workspace", tab_appearance: "Appearance", tab_ai: "AI & Voice", tab_rag: "RAG & Search", tab_privacy: "Privacy & GDPR Audit",
    setup_wizard: "Setup Wizard", language_label: "Interface Language", workspace_title: "Workspace Title", knowledge_folder: "Knowledge Folder",
    save: "Save", new_folder: "+ New Folder",
    appearance_logo_title: "Workspace Logo", appearance_logo_sub: "Personalize Your Icon", change_logo: "Change Logo", reset_logo: "Reset Logo",
    appearance_theme_title: "Theme & Colors", reset_colors: "Reset Colors", theme_mode: "Theme Mode",
    theme_dark: "Dark", theme_light: "Light (Clear)", starter_palettes: "Color Palettes",
    primary_accent: "Primary Accent", ambient_glow: "Ambient Glow", ambient_toggle: "Ambient Background",
    ambient_desc: "Subtle animated light gradient and interactive dot grid.",
    reset_appearance: "Reset All Appearance", reset_defaults_title: "Reset All Settings to REALM Defaults", reset_defaults_btn: "Reset Defaults",
    allow_cloud: "Allow Cloud APIs", lock_local: "Lock to Local Only", save_key: "Save Key", active_model: "Active Model (switch between local & saved cloud models anytime)",
    ob_title: "Welcome to REALM Engine", ob_skip: "Skip for now", ob_back: "← Back", ob_next: "Next →",
    ob_s1_head: "Your Private, Local-First Knowledge Engine", ob_s1_sub: "Choose your language and see what REALM Engine can do for you.",
    ob_f1_t: "Private Document Vault", ob_f1_d: "Drop PDFs, Word files, Markdown, or notes — everything stays cleanly on your computer.",
    ob_f2_t: "Local or Cloud AI", ob_f2_d: "Ask grounded questions with citations using free offline Ollama or your own paid API keys.",
    ob_f3_t: "2D Graph & Privacy Shield", ob_f3_d: "Explore connections visually and detect or redact personal data (GDPR) before sharing.",
    ob_s2_head: "Make This Workspace Yours", ob_s2_sub: "Name your workspace, upload your own logo, and preview a color theme live behind this window.",
    ob_s3_head: "Choose How AI Runs", ob_s3_sub: "Run 100% offline with Ollama, combine Ollama with paid cloud API keys, or start with instant search only.",
    ob_s4_head: "You're All Set!", ob_s4_sub: "You can customize anything anytime in Settings. Ready to explore your workspace?",
    ob_upload_btn: "Upload First PDF / Word / MD Files", ob_start_btn: "Start Exploring →",
    sum_lang: "Language", sum_workspace: "Workspace", sum_theme: "Theme", sum_ai: "AI Mode",
    submit_query: "Submit query", stop_generating: "Stop generating", stop_btn: "Stop", stopped_msg: "Generation stopped.",
    copy_btn: "Copy", copied_btn: "Copied", drop_overlay_title: "Drop files or whole folders to add to your Library",
    drop_overlay_sub: "PDF, Word, Excel, PowerPoint, CSV, Markdown, or nested folders · Private & local",
    browse_files: "Browse Files", import_folder: "Import Folder (with Subfolders)", open_vault: "Link Local Folder…",
    reveal_finder: "Show in Finder", reveal_explorer: "Open in Explorer", reveal_folder: "Open Folder", sync_folder: "↻ Sync Folder",
    web_search_title: "Opt-In Web Search", web_search_enable: "Allow Web Search Toggle in Chat",
    web_search_note: "Shows the Globe toggle in the prompt bar so you can include live web results per message. Blocked while Local-Only Lock is ON.",
    web_search_provider_label: "Search Engine", web_btn_off: "Web search OFF for this message (click to enable)", web_btn_on: "Web search ON for this message (click to disable)",
    free_chat: "Free Chat (No Workspace)", free_chat_short: "Free Chat", agents_nav: "Agents", formats_nav: "Answer Formats",
    agent_name_title: "Name Your Agent", agent_name_label: "Agent Display Name", agent_name_desc: "Display name shown on AI replies and exported notes (default: Saga).", reset_agent_name: "Reset to Saga",
    sync_agent_palette_title: "Sync Theme Palette with Active Agent", sync_agent_palette_desc: "Automatically adapt colors when switching between Saga, Lisbeth, Milton, and other agents (change anytime in Agents)."
  },
  de: {
    new_chat: "+ Neuer Chat", library: "Bibliothek", graph_view: "Wissensgraph", recent_chats: "Letzte Chats", settings: "Einstellungen",
    hero_greeting: "Womit sollen wir starten?", ask_placeholder: "Frag irgendetwas...", more_ideas: "↻ Mehr Ideen",
    browse_guides_pre: "Alle ", browse_guides_post: " Dokumente durchsuchen →",
    seed_1: "Fasse die wichtigsten Punkte meiner Dokumente zusammen", seed_2: "Extrahiere wichtige Aufgaben und Details", seed_3: "Worauf sollte ich mich als Nächstes konzentrieren?",
    tab_workspace: "Arbeitsbereich", tab_appearance: "Erscheinungsbild", tab_ai: "KI & Stimme", tab_rag: "Suche & RAG", tab_privacy: "Datenschutz & DSGVO",
    setup_wizard: "Einrichtung", language_label: "Sprache der Oberfläche", workspace_title: "Titel des Arbeitsbereichs", knowledge_folder: "Wissensordner",
    save: "Speichern", new_folder: "+ Neuer Ordner",
    appearance_logo_title: "Arbeitsbereich-Logo", appearance_logo_sub: "Eigenes Symbol verwenden", change_logo: "Logo ändern", reset_logo: "Logo zurücksetzen",
    appearance_theme_title: "Design & Farben", reset_colors: "Farben zurücksetzen", theme_mode: "Farbmodus",
    theme_dark: "Dunkel", theme_light: "Hell (Klar)", starter_palettes: "Farbpaletten",
    primary_accent: "Hauptakzent", ambient_glow: "Umgebungsleuchten", ambient_toggle: "Hintergrund-Effekte",
    ambient_desc: "Dezenter animierter Lichtverlauf und interaktives Punkteraster.",
    reset_appearance: "Design zurücksetzen", reset_defaults_title: "Alle Einstellungen auf REALM-Standard zurücksetzen", reset_defaults_btn: "Standard wiederherstellen",
    allow_cloud: "Cloud-APIs erlauben", lock_local: "Nur lokal sperren", save_key: "Schlüssel speichern", active_model: "Aktives Modell (jederzeit zwischen lokal & Cloud wechseln)",
    ob_title: "Willkommen bei REALM Engine", ob_skip: "Überspringen", ob_back: "← Zurück", ob_next: "Weiter →",
    ob_s1_head: "Deine private, lokale Wissens-Engine", ob_s1_sub: "Wähle deine Sprache und entdecke, was du mit REALM Engine machen kannst.",
    ob_f1_t: "Privater Dokumenten-Tresor", ob_f1_d: "PDFs, Word-Dateien, Markdown oder Notizen ablegen — alles bleibt sicher auf deinem Computer.",
    ob_f2_t: "Lokale oder Cloud-KI", ob_f2_d: "Stelle Fragen mit Quellenangaben — kostenlos offline mit Ollama oder mit deinen eigenen API-Schlüsseln.",
    ob_f3_t: "2D-Graph & Datenschutz", ob_f3_d: "Verbindungen visuell erkunden und persönliche Daten (DSGVO) automatisch erkennen oder schwärzen.",
    ob_s2_head: "Gestalte deinen Arbeitsbereich", ob_s2_sub: "Vergib einen Namen, lade dein eigenes Logo hoch und teste ein Farbthema live im Hintergrund.",
    ob_s3_head: "Wähle deine KI-Option", ob_s3_sub: "100 % offline mit Ollama, lokal + Cloud-API-Schlüssel kombiniert oder direkt mit reiner Suche starten.",
    ob_s4_head: "Alles bereit!", ob_s4_sub: "Du kannst alles jederzeit in den Einstellungen anpassen. Bereit loszulegen?",
    ob_upload_btn: "Erste PDF / Word / MD Dateien hochladen", ob_start_btn: "Jetzt starten →",
    sum_lang: "Sprache", sum_workspace: "Arbeitsbereich", sum_theme: "Design", sum_ai: "KI-Modus",
    submit_query: "Frage senden", stop_generating: "Erzeugung stoppen", stop_btn: "Stopp", stopped_msg: "Erzeugung gestoppt.",
    copy_btn: "Kopieren", copied_btn: "Kopiert", drop_overlay_title: "Dateien oder ganze Ordner hier ablegen",
    drop_overlay_sub: "PDF, Word, Excel, PowerPoint, CSV, Markdown oder Unterordner · Privat & lokal",
    browse_files: "Dateien wählen", import_folder: "Ordner importieren (mit Unterordnern)", open_vault: "Lokalen Ordner verknüpfen…",
    reveal_finder: "Im Finder zeigen", reveal_explorer: "Im Explorer öffnen", reveal_folder: "Ordner öffnen", sync_folder: "↻ Ordner synchronisieren",
    web_search_title: "Optionale Websuche", web_search_enable: "Websuche-Schalter im Chat erlauben",
    web_search_note: "Zeigt das Globus-Symbol im Eingabefeld, um pro Nachricht Web-Ergebnisse einzubeziehen. Im lokalen Modus gesperrt.",
    web_search_provider_label: "Suchmaschine", web_btn_off: "Websuche für diese Nachricht AUS (zum Aktivieren klicken)", web_btn_on: "Websuche für diese Nachricht AN (zum Deaktivieren klicken)",
    free_chat: "Freier Chat (Ohne Arbeitsbereich)", free_chat_short: "Freier Chat", agents_nav: "Agenten", formats_nav: "Antwortformate",
    agent_name_title: "Benenne deinen Agenten", agent_name_label: "Anzeigename des Agenten", agent_name_desc: "Wird bei jeder KI-Antwort und in Exporten angezeigt (Standard: Saga).", reset_agent_name: "Auf Saga zurücksetzen",
    sync_agent_palette_title: "Farbpalette an aktiven Agenten anpassen", sync_agent_palette_desc: "Wechselt die Farben automatisch mit Saga, Lisbeth, Milton & Co. (jederzeit unter Agenten änderbar)."
  },
  es: {
    new_chat: "+ Nuevo Chat", library: "Biblioteca", graph_view: "Grafo 2D", recent_chats: "Chats recientes", settings: "Ajustes",
    hero_greeting: "¿Por dónde empezamos?", ask_placeholder: "Pregunta lo que quieras...", more_ideas: "↻ Más ideas",
    browse_guides_pre: "Explorar los ", browse_guides_post: " documentos →",
    seed_1: "Resume los puntos clave de mis documentos", seed_2: "Extrae las tareas pendientes y detalles importantes", seed_3: "¿En qué debería enfocarme ahora?",
    tab_workspace: "Espacio", tab_appearance: "Apariencia", tab_ai: "IA y Voz", tab_rag: "Búsqueda y RAG", tab_privacy: "Privacidad y RGPD",
    setup_wizard: "Asistente inicial", language_label: "Idioma de la interfaz", workspace_title: "Nombre del espacio", knowledge_folder: "Carpeta de conocimiento",
    save: "Guardar", new_folder: "+ Nueva carpeta",
    appearance_logo_title: "Logo del espacio", appearance_logo_sub: "Personaliza tu ícono", change_logo: "Cambiar logo", reset_logo: "Restaurar logo",
    appearance_theme_title: "Tema y Colores", reset_colors: "Restaurar colores", theme_mode: "Modo de tema",
    theme_dark: "Oscuro", theme_light: "Claro", starter_palettes: "Paletas de color",
    primary_accent: "Color principal", ambient_glow: "Resplandor ambiental", ambient_toggle: "Fondo ambiental",
    ambient_desc: "Degradado de luz sutil y cuadrícula interactiva de puntos.",
    reset_appearance: "Restaurar apariencia", reset_defaults_title: "Restaurar todos los ajustes de REALM", reset_defaults_btn: "Restaurar ajustes",
    allow_cloud: "Permitir APIs en la nube", lock_local: "Bloquear a solo local", save_key: "Guardar clave", active_model: "Modelo activo (cambia entre local y nube en cualquier momento)",
    ob_title: "Bienvenido a REALM Engine", ob_skip: "Omitir por ahora", ob_back: "← Atrás", ob_next: "Siguiente →",
    ob_s1_head: "Tu motor de conocimiento privado y local", ob_s1_sub: "Elige tu idioma y descubre todo lo que puedes personalizar en REALM Engine.",
    ob_f1_t: "Bóveda privada de documentos", ob_f1_d: "Arrastra PDFs, Word, Markdown o notas — todo se guarda de forma segura en tu computadora.",
    ob_f2_t: "IA local o en la nube", ob_f2_d: "Haz preguntas con citas usando Ollama gratis sin internet o tus propias claves API.",
    ob_f3_t: "Grafo 2D y escudo de privacidad", ob_f3_d: "Explora conexiones visualmente y detecta o anonimiza datos personales automáticamente.",
    ob_s2_head: "Hazlo tuyo", ob_s2_sub: "Ponle nombre a tu espacio, sube tu propio logo y prueba un tema de color en vivo detrás de esta ventana.",
    ob_s3_head: "Elige cómo usar la IA", ob_s3_sub: "100 % offline con Ollama, combina Ollama con APIs en la nube o empieza solo con búsqueda rápida.",
    ob_s4_head: "¡Todo listo!", ob_s4_sub: "Siempre puedes cambiar cualquier detalle en Ajustes. ¿Listo para explorar?",
    ob_upload_btn: "Subir primeros archivos PDF / Word / MD", ob_start_btn: "Empezar a explorar →",
    sum_lang: "Idioma", sum_workspace: "Espacio", sum_theme: "Tema", sum_ai: "Modo de IA",
    submit_query: "Enviar pregunta", stop_generating: "Detener generación", stop_btn: "Detener", stopped_msg: "Generación detenida.",
    copy_btn: "Copiar", copied_btn: "Copiado", drop_overlay_title: "Suelta archivos o carpetas enteras para tu Biblioteca",
    drop_overlay_sub: "PDF, Word, Excel, PowerPoint, CSV, Markdown o subcarpetas · Privado y local",
    browse_files: "Elegir archivos", import_folder: "Importar carpeta (con subcarpetas)", open_vault: "Vincular carpeta local…",
    reveal_finder: "Mostrar en Finder", reveal_explorer: "Abrir en Explorador", reveal_folder: "Abrir carpeta", sync_folder: "↻ Sincronizar carpeta",
    web_search_title: "Búsqueda Web Opcional", web_search_enable: "Permitir botón de búsqueda web en el chat",
    web_search_note: "Muestra el ícono de globo en la barra de chat para activar resultados web en mensajes puntuales. Bloqueada en modo local.",
    web_search_provider_label: "Buscador", web_btn_off: "Búsqueda web DESACTIVADA en este mensaje (clic para activar)", web_btn_on: "Búsqueda web ACTIVA en este mensaje (clic para desactivar)",
    free_chat: "Chat libre (Sin espacio)", free_chat_short: "Chat libre", agents_nav: "Agentes", formats_nav: "Formatos",
    agent_name_title: "Nombra a tu agente", agent_name_label: "Nombre del agente", agent_name_desc: "Se muestra en cada respuesta de la IA y en las exportaciones (por defecto: Saga).", reset_agent_name: "Restaurar a Saga",
    sync_agent_palette_title: "Sincronizar colores con el agente activo", sync_agent_palette_desc: "Adapta automáticamente la paleta al cambiar entre Saga, Lisbeth, Milton y otros agentes (editable en Agentes)."
  }
};
"""
    + I18N_SETTINGS_SCRIPT
    + I18N_VIEWS_SCRIPT
    + I18N_EXTRA_SCRIPT
    + I18N_FEEDBACK_SCRIPT
    + I18N_GUIDE_SCRIPT
    + r"""

const STARTER_TERMS = {
  de: {
    "Welcome to REALM Knowledge Engine": "Willkommen bei REALM Engine",
    "How Knowledge Areas Work": "Wie Wissensbereiche funktionieren",
    "Hybrid Retrieval & Privacy": "Hybride Suche & Datenschutz",
    "Publishing a Read-Only Public API": "Eine schreibgeschützte öffentliche API bereitstellen"
  },
  es: {
    "Welcome to REALM Knowledge Engine": "Bienvenido a REALM Engine",
    "How Knowledge Areas Work": "Cómo funcionan los espacios de conocimiento",
    "Hybrid Retrieval & Privacy": "Búsqueda híbrida y privacidad",
    "Publishing a Read-Only Public API": "Publicar una API pública de solo lectura"
  }
};
function localizeStarterTerm(text) {
  const map = STARTER_TERMS[activeLanguage];
  return (map && map[text]) || text;
}
function localizeIdea(prompt) {
  const raw = String(prompt || "").trim();
  if (!raw || activeLanguage === "en") { return raw; }
  if (raw === I18N.en.seed_1) { return t("seed_1"); }
  if (raw === I18N.en.seed_2) { return t("seed_2"); }
  if (raw === I18N.en.seed_3) { return t("seed_3"); }
  const exp = raw.match(/^Explain (.+) in (.+)$/);
  if (exp) {
    const sec = localizeStarterTerm(exp[1]), title = localizeStarterTerm(exp[2]);
    return activeLanguage === "de" ? ("Erkläre „" + sec + "“ in " + title) : ("Explica «" + sec + "» en " + title);
  }
  const sum = raw.match(/^Summarize (.+)$/);
  if (sum) {
    const title = localizeStarterTerm(sum[1]);
    return activeLanguage === "de" ? ("Fasse " + title + " zusammen") : ("Resume " + title);
  }
  const top = raw.match(/^What are the main topics covered in (.+)\?$/);
  if (top) {
    const topic = localizeStarterTerm(top[1]);
    return activeLanguage === "de" ? ("Welche Hauptthemen deckt " + topic + " ab?") : ("¿Cuáles son los temas principales de " + topic + "?");
  }
  return raw;
}
function t(key, vars) {
  const dict = I18N[activeLanguage] || I18N.en;
  let out = dict[key] || I18N.en[key] || key;
  if (vars && typeof vars === "object") {
    for (const [k, v] of Object.entries(vars)) { out = out.replaceAll("{" + k + "}", String(v)); }
  }
  return out;
}
function revealFolderLabel() {
  const ua = (navigator.platform || navigator.userAgent || "").toLowerCase();
  if (ua.includes("mac")) { return t("reveal_finder"); }
  if (ua.includes("win")) { return t("reveal_explorer"); }
  return t("reveal_folder");
}
function applyLanguage(lang, persistLocal) {
  const safe = lang === "de" || lang === "es" ? lang : "en", langChanged = safe !== activeLanguage;
  activeLanguage = safe;
  document.documentElement.lang = safe;
  if (persistLocal !== false) { safeStorageSet("realm_lang", safe); }
  document.querySelectorAll("[data-i18n]").forEach(function (el) {
    const key = el.getAttribute("data-i18n");
    if (key && I18N[safe] && I18N[safe][key]) { el.textContent = I18N[safe][key]; }
  });
  document.querySelectorAll("[data-i18n-span]").forEach(function (el) {
    const key = el.getAttribute("data-i18n-span");
    const target = el.querySelector("span");
    if (target && key && I18N[safe] && I18N[safe][key]) { target.textContent = I18N[safe][key]; }
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
    const key = el.getAttribute("data-i18n-placeholder");
    if (key && I18N[safe] && I18N[safe][key]) { el.placeholder = I18N[safe][key]; }
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach(function (el) {
    const key = el.getAttribute("data-i18n-aria-label");
    if (key && I18N[safe] && I18N[safe][key]) { el.setAttribute("aria-label", I18N[safe][key]); }
  });
  document.querySelectorAll("[data-i18n-title]").forEach(function (el) {
    const key = el.getAttribute("data-i18n-title");
    if (key && I18N[safe] && I18N[safe][key]) { el.setAttribute("title", I18N[safe][key]); }
  });
  defaultPlaceholder = t("ask_placeholder");
  if (queryEl) { queryEl.placeholder = isActiveView ? t("ask_followup") : defaultPlaceholder; }
  document.querySelectorAll("[data-lang-choice]").forEach(function (btn) {
    const active = btn.getAttribute("data-lang-choice") === safe;
    btn.setAttribute("aria-pressed", String(active));
    btn.className = "py-1.5 px-3 rounded-lg text-xs font-medium transition " + (active ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]");
  });
  if (typeof syncThemeControlsUI === "function") {
    const mode = (workspaceConfig && workspaceConfig.theme_mode) || safeStorageGet("color-scheme") || "system";
    const accent = document.getElementById("theme-accent-picker") ? document.getElementById("theme-accent-picker").value.toUpperCase() : "#4BB8E8";
    const glow = document.getElementById("theme-glow-picker") ? document.getElementById("theme-glow-picker").value.toUpperCase() : "#6366F1";
    syncThemeControlsUI(mode, accent, glow);
  }
  document.querySelectorAll("[data-i18n-reveal]").forEach(function (el) { el.textContent = revealFolderLabel(); });
  if (typeof renderOnboardingSummary === "function") { renderOnboardingSummary(); }
  if (typeof renderSeedIdeas === "function") { renderSeedIdeas(); }
  if (typeof renderKnowledgeAreas === "function" && Array.isArray(knowledgeAreas) && knowledgeAreas.length) { renderKnowledgeAreas(); }
  if (typeof syncFolderHelper === "function") {
    const kDir = (workspaceConfig && workspaceConfig.knowledge_dir) || "";
    syncFolderHelper(kDir, "cfg-folder-helper"); syncFolderHelper(kDir, "onboarding-folder-helper");
  }
  if (typeof renderRecentChats === "function") { renderRecentChats(); }
  if (typeof applyLocalPolicy === "function" && workspaceConfig && workspaceConfig.knowledge_dir) { applyLocalPolicy(); }
  if (typeof syncKeyStatusUI === "function") { syncKeyStatusUI(); }
  if (typeof syncRagStudioUI === "function") { syncRagStudioUI(); }
  if (typeof syncWebSearchUI === "function") { syncWebSearchUI(workspaceConfig || {}); }
  if (typeof renderFormatStudio === "function") { renderFormatStudio(); }
  if (typeof renderAgentRoster === "function" && Array.isArray(agentTeam) && agentTeam.length) { renderAgentRoster(); }
  if (typeof syncInspectorSidebar === "function") { syncInspectorSidebar(); }
  if (typeof renderChatStream === "function" && currentTurns && currentTurns.length) { renderChatStream(); }
  if (typeof refreshBudget === "function" && typeof settingsModal !== "undefined" && settingsModal && settingsModal.open) { refreshBudget(); }
  if (typeof setUploadDestinationMode === "function" && typeof uploadDestinationMode !== "undefined") { setUploadDestinationMode(uploadDestinationMode); }
  const gv = document.getElementById("graph-view");
  if (langChanged && gv && !gv.classList.contains("hidden") && typeof openGraphView === "function" && typeof graphScope !== "undefined") { openGraphView(graphScope); }
  else if (langChanged && document.getElementById("library-view") && typeof openLibraryCatalog === "function") { openLibraryCatalog(selectedTag); }
  else if (langChanged && typeof activeReaderGuide !== "undefined" && activeReaderGuide && document.getElementById("reader-heading") && typeof renderGuideReader === "function") { renderGuideReader(activeReaderGuide, selectedTag); }
  const sm = document.getElementById("study-modal");
  if (langChanged && sm && sm.open && typeof renderStudyCard === "function") { if (typeof syncStudyGenLabel === "function") { syncStudyGenLabel(); } renderStudyCard(); }
}
function bindLanguageControls() {
  document.querySelectorAll("[data-lang-choice]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const lang = btn.getAttribute("data-lang-choice") || "en";
      applyLanguage(lang, true);
      if (typeof persistAppearancePatch === "function") { persistAppearancePatch({ language: lang }); }
    });
  });
  const saved = safeStorageGet("realm_lang");
  if (saved === "de" || saved === "es") { applyLanguage(saved, false); }
}
"""
)
