"""Client-side multi-language dictionary and live UI translator (English, Deutsch, Español)."""

I18N_SCRIPT: str = r"""
let activeLanguage = "en";
const I18N = {
  en: {
    new_chat: "+ New Chat", library: "Library", graph_view: "Graph View", recent_chats: "Recent Chats", settings: "Settings",
    hero_greeting: "Where should we start?", ask_placeholder: "Ask anything...", more_ideas: "↻ More ideas",
    browse_guides_pre: "Browse all ", browse_guides_post: " handbook guides →",
    seed_1: "Summarize the key points across my documents", seed_2: "Extract key action items and important details", seed_3: "What should I focus on next?",
    tab_workspace: "Workspace", tab_appearance: "Appearance", tab_ai: "AI & Voice", tab_rag: "RAG & Search", tab_privacy: "Privacy & DSGVO Audit",
    setup_wizard: "Setup Wizard", language_label: "Interface Language", workspace_title: "Workspace Title", knowledge_folder: "Knowledge Folder",
    save: "Save", new_folder: "+ New Folder",
    appearance_logo_title: "Workspace Logo", appearance_logo_sub: "Personalize Your Icon", change_logo: "Change Logo", reset_logo: "Reset Logo",
    appearance_theme_title: "Theme & Futuristic Colors", reset_colors: "Reset Colors", theme_mode: "Theme Mode",
    theme_dark: "Dark", theme_light: "Light (Clear)", starter_palettes: "Futuristic Starter Palettes",
    primary_accent: "Primary Accent", ambient_glow: "Ambient Glow", ambient_toggle: "Supernova & Interactive Dots",
    ambient_desc: "Sweeping cosmic glow and magnetic dot grid that reacts to your cursor.",
    reset_appearance: "Reset All Appearance", reset_defaults_title: "Reset All Settings to REALM Defaults", reset_defaults_btn: "Reset Defaults",
    allow_cloud: "Allow Cloud APIs", lock_local: "Lock to Local Only", save_key: "Save Key", active_model: "Active Model (switch between local & saved cloud models anytime)",
    ob_title: "Welcome to REALM Engine", ob_skip: "Skip for now", ob_back: "← Back", ob_next: "Next →",
    ob_s1_head: "Your Private, Local-First Knowledge Engine", ob_s1_sub: "Choose your language and see what REALM Engine can do for you.",
    ob_f1_t: "Private Document Vault", ob_f1_d: "Drop PDFs, Word files, Markdown, or notes — everything stays cleanly on your computer.",
    ob_f2_t: "Local or Cloud AI", ob_f2_d: "Ask grounded questions with citations using free offline Ollama or your own paid API keys.",
    ob_f3_t: "2D Graph & Privacy Shield", ob_f3_d: "Explore connections visually and detect or redact personal data (DSGVO/GDPR) before sharing.",
    ob_s2_head: "Make This Workspace Yours", ob_s2_sub: "Name your vault, upload your own logo, and try a futuristic color theme live behind this window.",
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
    free_chat: "Free Chat (No Area)", free_chat_short: "Free Chat", formats_nav: "Answer Formats",
    agent_name_title: "Name Your Agent", agent_name_label: "Agent Display Name", agent_name_desc: "Shown on every AI reply and exported note (default: Saga — the face of REALM).", reset_agent_name: "Reset to Saga"
  },
  de: {
    new_chat: "+ Neuer Chat", library: "Bibliothek", graph_view: "Wissensgraph", recent_chats: "Letzte Chats", settings: "Einstellungen",
    hero_greeting: "Womit sollen wir starten?", ask_placeholder: "Frag irgendetwas...", more_ideas: "↻ Mehr Ideen",
    browse_guides_pre: "Alle ", browse_guides_post: " Leitfäden durchsuchen →",
    seed_1: "Fasse die wichtigsten Punkte meiner Dokumente zusammen", seed_2: "Extrahiere wichtige Aufgaben und Details", seed_3: "Worauf sollte ich mich als Nächstes konzentrieren?",
    tab_workspace: "Arbeitsbereich", tab_appearance: "Erscheinungsbild", tab_ai: "KI & Sprache", tab_rag: "Suche & RAG", tab_privacy: "Datenschutz & DSGVO",
    setup_wizard: "Einrichtung", language_label: "Sprache der Oberfläche", workspace_title: "Titel des Arbeitsbereichs", knowledge_folder: "Wissensordner",
    save: "Speichern", new_folder: "+ Neuer Ordner",
    appearance_logo_title: "Arbeitsbereich-Logo", appearance_logo_sub: "Eigenes Symbol verwenden", change_logo: "Logo ändern", reset_logo: "Logo zurücksetzen",
    appearance_theme_title: "Design & Futuristische Farben", reset_colors: "Farben zurücksetzen", theme_mode: "Farbmodus",
    theme_dark: "Dunkel", theme_light: "Hell (Klar)", starter_palettes: "Futuristische Farbpaletten",
    primary_accent: "Hauptakzent", ambient_glow: "Umgebungsleuchten", ambient_toggle: "Supernova & Interaktive Punkte",
    ambient_desc: "Sanfter kosmischer Lichtstrahl und interaktives Punkteraster rund um deinen Mauszeiger.",
    reset_appearance: "Design zurücksetzen", reset_defaults_title: "Alle Einstellungen auf REALM-Standard zurücksetzen", reset_defaults_btn: "Standard wiederherstellen",
    allow_cloud: "Cloud-APIs erlauben", lock_local: "Nur lokal sperren", save_key: "Schlüssel speichern", active_model: "Aktives Modell (jederzeit zwischen lokal & Cloud wechseln)",
    ob_title: "Willkommen bei REALM Engine", ob_skip: "Überspringen", ob_back: "← Zurück", ob_next: "Weiter →",
    ob_s1_head: "Deine private, lokale Wissens-Engine", ob_s1_sub: "Wähle deine Sprache und entdecke, was du mit REALM Engine machen kannst.",
    ob_f1_t: "Privater Dokumenten-Tresor", ob_f1_d: "PDFs, Word-Dateien, Markdown oder Notizen ablegen — alles bleibt sicher auf deinem Computer.",
    ob_f2_t: "Lokale oder Cloud-KI", ob_f2_d: "Stelle Fragen mit Quellenangaben — kostenlos offline mit Ollama oder mit deinen eigenen API-Schlüsseln.",
    ob_f3_t: "2D-Graph & Datenschutz", ob_f3_d: "Verbindungen visuell erkunden und persönliche Daten (DSGVO) automatisch erkennen oder schwärzen.",
    ob_s2_head: "Gestalte deinen Arbeitsbereich", ob_s2_sub: "Vergib einen Namen, lade dein eigenes Logo hoch und teste futuristische Farben live im Hintergrund.",
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
    free_chat: "Freier Chat (Ohne Bereich)", free_chat_short: "Freier Chat", formats_nav: "Antwortformate",
    agent_name_title: "Benenne deinen Agenten", agent_name_label: "Anzeigename des Agenten", agent_name_desc: "Wird bei jeder KI-Antwort und in Exporten angezeigt (Standard: Saga).", reset_agent_name: "Auf Saga zurücksetzen"
  },
  es: {
    new_chat: "+ Nuevo Chat", library: "Biblioteca", graph_view: "Grafo 2D", recent_chats: "Chats recientes", settings: "Ajustes",
    hero_greeting: "¿Por dónde empezamos?", ask_placeholder: "Pregunta lo que quieras...", more_ideas: "↻ Más ideas",
    browse_guides_pre: "Explorar las ", browse_guides_post: " guías →",
    seed_1: "Resume los puntos clave de mis documentos", seed_2: "Extrae las tareas pendientes y detalles importantes", seed_3: "¿En qué debería enfocarme ahora?",
    tab_workspace: "Espacio", tab_appearance: "Apariencia", tab_ai: "IA y Voz", tab_rag: "Búsqueda y RAG", tab_privacy: "Privacidad y Auditoría",
    setup_wizard: "Asistente inicial", language_label: "Idioma de la interfaz", workspace_title: "Nombre del espacio", knowledge_folder: "Carpeta de conocimiento",
    save: "Guardar", new_folder: "+ Nueva carpeta",
    appearance_logo_title: "Logo del espacio", appearance_logo_sub: "Personaliza tu ícono", change_logo: "Cambiar logo", reset_logo: "Restaurar logo",
    appearance_theme_title: "Tema y Colores Futuristas", reset_colors: "Restaurar colores", theme_mode: "Modo de tema",
    theme_dark: "Oscuro", theme_light: "Claro", starter_palettes: "Paletas futuristas",
    primary_accent: "Color principal", ambient_glow: "Resplandor ambiental", ambient_toggle: "Supernova y Puntos Interactivos",
    ambient_desc: "Haz cósmico suave y matriz de puntos magnéticos que se abre al pasar el cursor.",
    reset_appearance: "Restaurar apariencia", reset_defaults_title: "Restaurar todos los ajustes de REALM", reset_defaults_btn: "Restaurar ajustes",
    allow_cloud: "Permitir APIs en la nube", lock_local: "Bloquear a solo local", save_key: "Guardar clave", active_model: "Modelo activo (cambia entre local y nube en cualquier momento)",
    ob_title: "Bienvenido a REALM Engine", ob_skip: "Omitir por ahora", ob_back: "← Atrás", ob_next: "Siguiente →",
    ob_s1_head: "Tu motor de conocimiento privado y local", ob_s1_sub: "Elige tu idioma y descubre todo lo que puedes personalizar en REALM Engine.",
    ob_f1_t: "Bóveda privada de documentos", ob_f1_d: "Arrastra PDFs, Word, Markdown o notas — todo se guarda de forma segura en tu computadora.",
    ob_f2_t: "IA local o en la nube", ob_f2_d: "Haz preguntas con citas usando Ollama gratis sin internet o tus propias claves API.",
    ob_f3_t: "Grafo 2D y escudo de privacidad", ob_f3_d: "Explora conexiones visualmente y detecta o anonimiza datos personales automáticamente.",
    ob_s2_head: "Hazlo tuyo", ob_s2_sub: "Ponle nombre a tu espacio, sube tu propio logo y prueba colores futuristas en vivo detrás de esta ventana.",
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
    free_chat: "Chat libre (Sin área)", free_chat_short: "Chat libre", formats_nav: "Formatos",
    agent_name_title: "Nombra a tu agente", agent_name_label: "Nombre del agente", agent_name_desc: "Se muestra en cada respuesta de la IA y en las exportaciones (por defecto: Saga).", reset_agent_name: "Restaurar a Saga"
  }
};

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
function t(key) {
  const dict = I18N[activeLanguage] || I18N.en;
  return dict[key] || I18N.en[key] || key;
}
function revealFolderLabel() {
  const ua = (navigator.platform || navigator.userAgent || "").toLowerCase();
  if (ua.includes("mac")) { return t("reveal_finder"); }
  if (ua.includes("win")) { return t("reveal_explorer"); }
  return t("reveal_folder");
}
function applyLanguage(lang, persistLocal) {
  const safe = lang === "de" || lang === "es" ? lang : "en";
  activeLanguage = safe;
  document.documentElement.lang = safe;
  if (persistLocal !== false) { try { localStorage.setItem("realm_lang", safe); } catch (_e) {} }
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
  defaultPlaceholder = t("ask_placeholder");
  if (!isActiveView && queryEl) { queryEl.placeholder = defaultPlaceholder; }
  document.querySelectorAll("[data-lang-choice]").forEach(function (btn) {
    const active = btn.getAttribute("data-lang-choice") === safe;
    btn.setAttribute("aria-pressed", String(active));
    btn.className = "py-1.5 px-3 rounded-lg text-xs font-medium transition " + (active ? "bg-[#4BB8E8] text-[#04060F]" : "text-[#A0B0C8] hover:text-[#EEF2F8]");
  });
  if (typeof syncThemeControlsUI === "function") {
    const mode = (workspaceConfig && workspaceConfig.theme_mode) || localStorage.getItem("color-scheme") || "system";
    const accent = document.getElementById("theme-accent-picker") ? document.getElementById("theme-accent-picker").value.toUpperCase() : "#4BB8E8";
    const glow = document.getElementById("theme-glow-picker") ? document.getElementById("theme-glow-picker").value.toUpperCase() : "#6366F1";
    syncThemeControlsUI(mode, accent, glow);
  }
  document.querySelectorAll("[data-i18n-reveal]").forEach(function (el) { el.textContent = revealFolderLabel(); });
  if (typeof renderOnboardingSummary === "function") { renderOnboardingSummary(); }
  if (typeof renderSeedIdeas === "function") { renderSeedIdeas(); }
  if (typeof syncWebSearchUI === "function") { syncWebSearchUI(workspaceConfig || {}); }
}
function bindLanguageControls() {
  document.querySelectorAll("[data-lang-choice]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const lang = btn.getAttribute("data-lang-choice") || "en";
      applyLanguage(lang, true);
      if (typeof persistAppearancePatch === "function") { persistAppearancePatch({ language: lang }); }
    });
  });
  try {
    const saved = localStorage.getItem("realm_lang");
    if (saved === "de" || saved === "es") { applyLanguage(saved, false); }
  } catch (_e) {}
}
"""
