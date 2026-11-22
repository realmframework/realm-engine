"""Cross-platform physical RAM detection shared by core sidecar and UI advice."""

from __future__ import annotations

import ctypes
import os
import struct
import subprocess
import sys

_CACHED_RAM_GB: int | None = None


def physical_ram_gb() -> int:
    """Return detected physical RAM in GiB (0 when undetectable)."""
    global _CACHED_RAM_GB
    in_pytest = bool(os.environ.get("PYTEST_CURRENT_TEST"))
    if not in_pytest and _CACHED_RAM_GB is not None:
        return _CACHED_RAM_GB
    try:
        if sys.platform == "win32":
            memory = ctypes.create_string_buffer(64)
            struct.pack_into("<I", memory, 0, 64)
            loader = getattr(ctypes, "windll", None)
            if loader is None or not loader.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
                return 0
            size = struct.unpack_from("<Q", memory, 8)[0]
        elif sys.platform == "darwin":
            result = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=1, check=True)
            size = int(result.stdout.strip())
        else:
            size = os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
        detected = max(0, round(size / 1024**3))
        if not in_pytest:
            _CACHED_RAM_GB = detected
        return detected
    except (OSError, ValueError, AttributeError, subprocess.SubprocessError):
        try:
            if sys.platform == "win32":
                return 0
            return max(0, round(os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE") / 1024**3))
        except (OSError, ValueError, AttributeError):
            return 0
