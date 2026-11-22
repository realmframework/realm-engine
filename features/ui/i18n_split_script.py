"""EN/DE/ES translations for Split Chat & Right Document Reader."""

I18N_SPLIT_SCRIPT: str = r"""
const I18N_SPLIT = {
  en: {
    sp_close: "Close Split Chat",
    sp_resize_aria: "Resize split chats",
    sp_pane_aria: "Split Chat",
    sp_mode_chat: "Chat",
    sp_mode_guide: "Document",
    sp_agent_aria: "Split chat agent",
    sp_guide_select_aria: "Choose a Library document",
    sp_no_guides: "No documents in this workspace yet.",
    sp_ask_in_chat: "Ask in Split Chat",
    sp_open_in_split: "Open in Split Chat"
  },
  de: {
    sp_close: "Geteilten Chat schließen",
    sp_resize_aria: "Geteilte Chats anpassen",
    sp_pane_aria: "Geteilter Chat",
    sp_mode_chat: "Chat",
    sp_mode_guide: "Dokument",
    sp_agent_aria: "Agent im geteilten Chat",
    sp_guide_select_aria: "Dokument aus Bibliothek wählen",
    sp_no_guides: "Noch keine Dokumente in diesem Arbeitsbereich.",
    sp_ask_in_chat: "Im geteilten Chat fragen",
    sp_open_in_split: "Im geteilten Chat öffnen"
  },
  es: {
    sp_close: "Cerrar chat dividido",
    sp_resize_aria: "Ajustar tamaño de chats divididos",
    sp_pane_aria: "Chat dividido",
    sp_mode_chat: "Chat",
    sp_mode_guide: "Documento",
    sp_agent_aria: "Agente del chat dividido",
    sp_guide_select_aria: "Elegir un documento de la Biblioteca",
    sp_no_guides: "Aún no hay documentos en este espacio.",
    sp_ask_in_chat: "Preguntar en chat dividido",
    sp_open_in_split: "Abrir en chat dividido"
  }
};
for (const _lang of ["en", "de", "es"]) { Object.assign(I18N[_lang], I18N_SPLIT[_lang]); }
"""
