"""Shared 1.5px stroke monochrome SVG icons reused across the REALM spatial shell."""


def _svg(size: int, body: str, stroke: str = "1.6", cls: str = "") -> str:
    dim = f'class="{cls}"' if cls else f'width="{size}" height="{size}"'
    return (
        f'<svg aria-hidden="true" {dim} viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round">{body}</svg>'
    )


ICON_SIDEBAR_LEFT: str = _svg(17, '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/>')
ICON_BOTTOM_PANEL: str = _svg(17, '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 14h18"/>')
ICON_RIGHT_SIDEBAR: str = _svg(17, '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M15 4v16"/>')
ICON_SPLIT_EDITOR: str = _svg(17, '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 4v16"/>')
ICON_INSPECTOR_LUPE: str = _svg(15, '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5M11 8v6M8 11h6"/>', "1.65")
ICON_COPILOT: str = _svg(15, '<path d="M12 3 14.3 9.7 21 12l-6.7 2.3L12 21l-2.3-6.7L3 12l6.7-2.3Z"/>', "1.6")
ICON_FOLDER_TREE: str = _svg(15, '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z"/>')
ICON_REFRESH: str = _svg(14, '<path d="M21 12a9 9 0 1 1-2.64-6.36"/><path d="M21 3v6h-6"/>', "1.65")
ICON_COLLAPSE_ALL: str = _svg(14, '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M8 12h8"/>', "1.65")
ICON_HOME: str = _svg(18, '<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5.5v-6h-5v6H4a1 1 0 0 1-1-1v-9.5Z"/>', "1.5")
ICON_LIBRARY: str = _svg(16, '<path d="M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6Zm0 6h16M10 4v16"/>', "1.5")
ICON_WORK: str = _svg(16, '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16M15 4v16M3 10h6M9 14h6"/>', "1.5")
ICON_WORKFLOWS: str = _svg(16, '<rect x="3" y="4" width="6" height="5" rx="1.2"/><rect x="15" y="4" width="6" height="5" rx="1.2"/><rect x="15" y="15" width="6" height="5" rx="1.2"/><path d="M9 6.5h6M12 6.5v11h3"/>', "1.5")
ICON_AGENTS: str = _svg(16, '<path d="M16 11a4 4 0 1 0-8 0 4 4 0 0 0 8 0Zm-11 9a7 7 0 0 1 14 0"/>', "1.5")
ICON_FORMATS: str = _svg(15, '<path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2M9 5h6M9 12h6m-6 4h4"/>', "1.5")
ICON_GRAPH: str = _svg(15, '<circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="12" cy="18" r="2.5"/><path d="M8.2 7.2 10.8 16m5-8.8L13.2 16M8.5 6h7"/>', "1.5")
ICON_MORE: str = (
    '<svg aria-hidden="true" width="17" height="17" viewBox="0 0 24 24" fill="currentColor">'
    '<circle cx="6" cy="12" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="18" cy="12" r="1.4"/></svg>'
)
ICON_SEARCH: str = _svg(16, '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>')
ICON_HELP: str = _svg(18, '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 0 1 5 .7c0 1.6-2.5 2-2.5 3.3m0 3h.01"/>', "1.5")
ICON_SETTINGS: str = _svg(
    18,
    '<path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 0 0-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 0 0-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 0 0-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 0 0-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 0 0 1.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065Z"/><circle cx="12" cy="12" r="3"/>',
    "1.5",
)
ICON_PLUS: str = _svg(15, '<path d="M12 5v14M5 12h14"/>', "1.5")
ICON_UPLOAD: str = _svg(15, '<path d="M12 16V4m0 0-4 4m4-4 4 4M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/>', "1.5")
ICON_STUDY: str = _svg(15, '<rect x="4" y="5" width="16" height="14" rx="2"/><path d="M8 10h8M8 14h5"/>', "1.5")
ICON_FOCUS: str = _svg(15, '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3.5"/>', "1.5")
ICON_IMPACT: str = _svg(15, '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2M9.5 2.5h5"/>', "1.5")
ICON_CHEVRON_UP: str = _svg(15, '<path d="m18 15-6-6-6 6"/>', "1.7")
ICON_MIC: str = _svg(16, '<path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v3m-3 0h6"/>', "1.5", "w-4 h-4 shrink-0")
ICON_GLOBE: str = _svg(16, '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>', "1.5", "w-4 h-4 shrink-0")
