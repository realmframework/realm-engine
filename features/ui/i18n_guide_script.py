"""EN/DE/ES translations for the calm 3-tab Quick Guide, Sources Used inspector, and Setup tip."""

I18N_GUIDE_SCRIPT: str = r"""
const I18N_GUIDE = {
  en: {
    quick_guide_link: "Quick Guide",
    gtab_chat: "Chat & Commands", gtab_library: "Library & Reading", gtab_privacy: "Privacy & Basics",
    guide_files_t: "Documents & Linked Folders",
    guide_files_d: "Drop PDFs, Word, Excel, PowerPoint, or Markdown notes into your Library — or choose Link Local Folder… to use an existing folder on your computer without copying files.",
    guide_study_t: "Study Cards & Audio Briefings",
    guide_priv_t: "Private & Local by Default",
    guide_priv_d: "Local-Only Lock is on by default so your documents stay on your computer. In Settings you can review or redact personal details, back up workspaces as ZIPs, or adjust text size and colors.",
    guide_jump_lbl: "Open:",
    xray_hint: "Pin a source to always include it, or Mute it to leave it out on your next reply.",
    xray_match_kw: "Keyword match", xray_match_sem: "Meaning match", xray_match_both: "Keyword + meaning match",
    ob_ollama_tip_pre: "Quick start: ", ob_ollama_tip_link: "install Ollama",
    ob_ollama_tip_post: ", then use Download Recommended Local AI in the Setup Wizard. No terminal is needed."
  },
  de: {
    quick_guide_link: "Kurzanleitung",
    gtab_chat: "Chat & Befehle", gtab_library: "Bibliothek & Lesen", gtab_privacy: "Datenschutz & Grundlagen",
    guide_files_t: "Dokumente & verknüpfte Ordner",
    guide_files_d: "Ziehe PDFs, Word-, Excel-, PowerPoint- oder Markdown-Dateien in deine Bibliothek — oder nutze „Lokalen Ordner verknüpfen…“, um bestehende Ordner direkt ohne Kopieren zu verwenden.",
    guide_study_t: "Lernkarten & Audio-Briefings",
    guide_priv_t: "Standardmäßig lokal & privat",
    guide_priv_d: "Der lokale Modus ist standardmäßig aktiv, damit deine Dokumente auf deinem Computer bleiben. In den Einstellungen kannst du persönliche Daten prüfen oder schwärzen, Backups als ZIP sichern sowie Textgröße und Farben anpassen.",
    guide_jump_lbl: "Öffnen:",
    xray_hint: "Hefte eine Quelle an, um sie einzubeziehen, oder blende sie für die nächste Antwort aus.",
    xray_match_kw: "Stichwort-Treffer", xray_match_sem: "Inhalts-Treffer", xray_match_both: "Stichwort + Inhalt",
    ob_ollama_tip_pre: "Schnellstart: ", ob_ollama_tip_link: "Ollama installieren",
    ob_ollama_tip_post: " und anschließend im Einrichtungsassistenten „Empfohlene lokale KI laden“ klicken. Kein Terminal nötig."
  },
  es: {
    quick_guide_link: "Guía rápida",
    gtab_chat: "Chat y comandos", gtab_library: "Biblioteca y lectura", gtab_privacy: "Privacidad y básicos",
    guide_files_t: "Documentos y carpetas vinculadas",
    guide_files_d: "Arrastra archivos PDF, Word, Excel, PowerPoint o Markdown a tu Biblioteca — o elige «Vincular carpeta local…» para usar una carpeta existente en tu equipo sin copiar archivos.",
    guide_study_t: "Tarjetas de estudio y audio",
    guide_priv_t: "Privado y local por defecto",
    guide_priv_d: "El bloqueo solo local está activo por defecto para que tus documentos permanezcan en tu equipo. En Ajustes puedes revisar o anonimizar datos personales, hacer copias ZIP y ajustar tamaño de texto y colores.",
    guide_jump_lbl: "Abrir:",
    xray_hint: "Fija una fuente para incluirla siempre u ocúltala para excluirla en tu próxima respuesta.",
    xray_match_kw: "Coincidencia exacta", xray_match_sem: "Coincidencia de sentido", xray_match_both: "Exacta + sentido",
    ob_ollama_tip_pre: "Inicio rápido: ", ob_ollama_tip_link: "instala Ollama",
    ob_ollama_tip_post: " y luego pulsa «Descargar IA local recomendada» en el asistente de configuración. No necesitas terminal."
  }
};
for (const _lang of ["en", "de", "es"]) { Object.assign(I18N[_lang], I18N_GUIDE[_lang]); }
"""
