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


def _platform_webview_datas() -> list[tuple[str, str]]:
    if sys.platform == "darwin":
        return collect_data_files("webview", subdir="js")
    if sys.platform == "win32":
        return [
            (src, dst)
            for src, dst in collect_data_files("webview")
            if not src.endswith(".jar") and "win-arm64" not in src.replace("\\", "/") and "win-x86" not in src.replace("\\", "/")
        ]
    return collect_data_files("webview", subdir="js")


def _windows_version_info() -> object | None:
    if sys.platform != "win32":
        return None
    from PyInstaller.utils.win32.versioninfo import (
        FixedFileInfo,
        StringFileInfo,
        StringStruct,
        StringTable,
        VarFileInfo,
        VarStruct,
        VSVersionInfo,
    )

    parts = [int(p) if p.isdigit() else 0 for p in APP_VERSION.split(".")]
    ver_tuple = tuple((parts + [0, 0, 0, 0])[:4])
    return VSVersionInfo(
        ffi=FixedFileInfo(filevers=ver_tuple, prodvers=ver_tuple, mask=0x3F, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
        kids=[
            StringFileInfo([StringTable("040904B0", [
                StringStruct("CompanyName", "REALM Framework"),
                StringStruct("FileDescription", "REALM Engine — Local-First AI Knowledge Engine"),
                StringStruct("FileVersion", APP_VERSION),
                StringStruct("InternalName", APP_NAME),
                StringStruct("LegalCopyright", "Copyright (c) 2026 Luis Godoy Alvarez (MIT)"),
                StringStruct("OriginalFilename", f"{APP_NAME}.exe"),
                StringStruct("ProductName", APP_NAME),
                StringStruct("ProductVersion", APP_VERSION),
            ])]),
            VarFileInfo([VarStruct("Translation", [1033, 1200])]),
        ],
    )


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
        else ["webview.platforms.gtk", "webview.platforms.qt"]
    ),
]
assert "features.ui.app" in hiddenimports, "PyInstaller failed to discover features.ui.app"

datas = [
    (str(ROOT / "features" / "ui" / "static"), "features/ui/static"),
    (str(ROOT / "examples" / "starter_vault"), "examples/starter_vault"),
    *_platform_webview_datas(),
]

icon_path: str | None = None
if sys.platform == "darwin":
    icns = ROOT / "packaging" / "icons" / "realm-engine.icns"
    if icns.is_file():
        icon_path = str(icns)
elif sys.platform == "win32":
    for cand in (ROOT / "packaging" / "icons" / "realm-engine.ico", ROOT / "features" / "ui" / "static" / "favicon.ico"):
        if cand.is_file():
            icon_path = str(cand)
            break

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
    version=_windows_version_info(),
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
            "NSAppleEventsUsageDescription": "REALM Engine uses Apple Events only to display the native folder picker when you link or import a folder.",
        },
    )
