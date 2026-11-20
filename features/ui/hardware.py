"""Physical memory detection with platform fallbacks and cautious beginner guidance."""

import ctypes
import os
import struct
import subprocess
import sys


def physical_ram_gb() -> int:
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
        return max(0, round(size / 1024**3))
    except (OSError, ValueError, AttributeError, subprocess.SubprocessError):
        try:
            return max(0, round(os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE") / 1024**3))
        except (OSError, ValueError, AttributeError):
            return 0


def hardware_advice(ram_gb: int | None = None) -> dict[str, object]:
    ram = physical_ram_gb() if ram_gb is None else ram_gb
    if ram <= 0:
        advice = "RAM could not be detected. Search and anonymization work now; check your memory before downloading a local model."
    elif ram < 8:
        advice = "Start with Search & Anonymize. If you try local AI, choose a small 1B model; cloud AI can do the work off your laptop."
    elif ram < 16:
        advice = "A small, compressed 1–3B local model is a sensible starting point. Search and anonymization need no AI setup."
    elif ram < 32:
        advice = "Try a compressed 7–8B local model. It can often fit in this memory, while leaving room for everyday apps."
    elif ram < 64:
        advice = "A compressed 14B local model is a reasonable starting point. Smaller models usually respond faster."
    else:
        advice = "You can consider a compressed 32B local model. Start smaller if you want faster responses."
    return {"ram_gb": ram, "ram_tier_advice": advice + " Model size, long conversations and other apps also affect memory use."}
