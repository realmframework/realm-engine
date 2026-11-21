# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build specification for the REALM Engine desktop application."""

import sys
import tomllib
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

with (ROOT / "pyproject.toml").open("rb") as _handle:
    APP_VERSION = str(tomllib.load(_handle)["project"]["version"])

APP_NAME = "REALM Engine"
BUNDLE_ID = "org.realmframework.realm-engine"


def _non_test_submodules(package: str) -> list[str]:
    return [
        mod
        for mod in collect_submodules(package)
        if not any(part.startswith("test_") or part == "conftest" for part in mod.split("."))
    ]


hiddenimports = [
    *_non_test_submodules("core"),
    *_non_test_submodules("features"),
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
    "multipart",
    "python_multipart",
    "webview",
    *(
        ["webview.platforms.cocoa"]
        if sys.platform == "darwin"
        else ["webview.platforms.winforms", "webview.platforms.edgechromium"]
        if sys.platform == "win32"
        else []
    ),
]
assert "features.ui.app" in hiddenimports, "PyInstaller failed to discover features.ui.app"

datas = [
    (str(ROOT / "features" / "ui" / "static"), "features/ui/static"),
    (str(ROOT / "examples" / "starter_vault"), "examples/starter_vault"),
    *collect_data_files("webview"),
]

icon_path: str | None = None
if sys.platform == "darwin":
    icns = ROOT / "packaging" / "icons" / "realm-engine.icns"
    if icns.is_file():
        icon_path = str(icns)
elif sys.platform == "win32":
    ico = ROOT / "features" / "ui" / "static" / "favicon.ico"
    if ico.is_file():
        icon_path = str(ico)

a = Analysis(
    [str(ROOT / "desktop_app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "pyright", "ruff", "tkinter", "test"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name=APP_NAME,
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=icon_path,
        bundle_identifier=BUNDLE_ID,
        info_plist={
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": APP_NAME,
            "CFBundleShortVersionString": APP_VERSION,
            "CFBundleVersion": APP_VERSION,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "13.0",
            "NSAppTransportSecurity": {"NSAllowsLocalNetworking": True},
            "NSMicrophoneUsageDescription": "REALM Engine uses the microphone only when you click voice dictation.",
        },
    )
