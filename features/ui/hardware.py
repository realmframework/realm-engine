"""Physical memory detection with platform fallbacks and cautious beginner guidance."""

import ctypes
import os
import subprocess
import sys

from core.hardware import physical_ram_gb

__all__ = ["ctypes", "hardware_advice", "os", "physical_ram_gb", "subprocess", "sys"]


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
