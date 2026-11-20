"""Pure-Python dmgbuild settings for a styled drag-to-Applications macOS DMG."""

import os
from pathlib import Path

ROOT = Path.cwd()
APP_PATH = os.environ.get("REALM_DMG_APP", str(ROOT / "dist" / "REALM Engine.app"))
BG_PATH = os.environ.get("REALM_DMG_BG", str(ROOT / "packaging" / "icons" / "installer-bg.png"))
ICON_PATH = os.environ.get("REALM_DMG_ICON", str(ROOT / "packaging" / "icons" / "realm-engine.icns"))

format = "UDZO"
files = [APP_PATH]
symlinks = {"Applications": "/Applications"}
badge_icon = ICON_PATH if Path(ICON_PATH).is_file() else None
background = BG_PATH if Path(BG_PATH).is_file() else "#F4F7FB"
icon_size = 104
text_size = 13
default_view = "icon-view"
show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False
window_rect = ((200, 200), (660, 440))
icon_locations = {
    "REALM Engine.app": (185, 168),
    "Applications": (475, 168),
}
