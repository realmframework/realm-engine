"""Physical-memory probes use each platform's byte count and degrade safely."""

import ctypes
import struct
import subprocess
from types import SimpleNamespace

import pytest

from features.ui import hardware


def test_linux_physical_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(hardware.sys, "platform", "linux")
    monkeypatch.setattr(hardware.os, "sysconf", lambda key: 4096 if key == "SC_PAGE_SIZE" else 4_194_304, raising=False)
    assert hardware.physical_ram_gb() == 16


def test_mac_probe_and_safe_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(hardware.sys, "platform", "darwin")
    monkeypatch.setattr(hardware.subprocess, "run", lambda *_args, **_kw: SimpleNamespace(stdout=str(32 * 1024**3)))
    assert hardware.physical_ram_gb() == 32

    def unavailable(*_args: object, **_kwargs: object) -> None:
        raise subprocess.TimeoutExpired("sysctl", 1)

    monkeypatch.setattr(hardware.subprocess, "run", unavailable)
    monkeypatch.setattr(hardware.os, "sysconf", lambda _key: 65536, raising=False)
    assert hardware.physical_ram_gb() == 4
    monkeypatch.setattr(hardware.os, "sysconf", lambda _key: int("unavailable"), raising=False)
    assert hardware.physical_ram_gb() == 0


def test_windows_memory_status_layout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(hardware.sys, "platform", "win32")

    def memory_status(pointer: ctypes.c_void_p) -> int:
        buffer = ctypes.cast(pointer, ctypes.POINTER(ctypes.c_char * 64)).contents
        assert struct.unpack_from("<I", buffer)[0] == 64
        struct.pack_into("<Q", buffer, 8, 64 * 1024**3)
        return 1

    monkeypatch.setattr(hardware.ctypes, "windll", SimpleNamespace(kernel32=SimpleNamespace(GlobalMemoryStatusEx=memory_status)), raising=False)
    assert hardware.physical_ram_gb() == 64
    monkeypatch.setattr(hardware.ctypes, "windll", None)
    assert hardware.physical_ram_gb() == 0


@pytest.mark.parametrize("ram,phrase", [(0, "could not be detected"), (4, "1B"), (8, "1–3B"), (16, "7–8B"), (32, "14B"), (64, "32B")])
def test_advice_is_plain_and_qualified(ram: int, phrase: str) -> None:
    result = hardware.hardware_advice(ram)
    assert result["ram_gb"] == ram and phrase in str(result["ram_tier_advice"])
    assert "other apps" in str(result["ram_tier_advice"])
