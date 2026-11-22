"""Pinned llama.cpp release manifest, 4-tier RAM model catalog & thermal guardrails."""

from __future__ import annotations

import platform
import sys
from urllib.parse import urlparse

from core.local_ai_contracts import (
    LocalAiModelPreset,
    LocalAiPlatformKey,
    LocalAiProfile,
    LocalAiRuntimeAsset,
    LocalAiTier,
)
from core.local_ai_os import detect_physical_cores

LLAMA_RELEASE_TAG = "b12631"
_GH = f"https://github.com/ggml-org/llama.cpp/releases/download/{LLAMA_RELEASE_TAG}"
_HF = "https://huggingface.co"

ALLOWED_DOWNLOAD_HOSTS: frozenset[str] = frozenset({
    "github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
    "huggingface.co",
    "cas-bridge.xethub.hf.co",
    "cdn-lfs.hf.co",
    "cdn-lfs-us-1.hf.co",
    "cdn-lfs-eu-1.hf.co",
})


def _asset(key: LocalAiPlatformKey, suffix: str, sha256: str, size: int, binary: str = "llama-server") -> LocalAiRuntimeAsset:
    archive = f"llama-{LLAMA_RELEASE_TAG}-bin-{suffix}"
    return LocalAiRuntimeAsset(platform_key=key, release_tag=LLAMA_RELEASE_TAG, archive_name=archive, url=f"{_GH}/{archive}", sha256=sha256, size_bytes=size, binary_name=binary)


def _preset(
    pid: str, tier: LocalAiTier, label_key: str, repo: str, fname: str, sha256: str, size: int, min_ram: int,
    *, reasoning: bool = True, ctx_eco: int = 4096, ctx_perf: int = 8192,
) -> LocalAiModelPreset:
    return LocalAiModelPreset(
        id=pid, tier=tier, label_key=label_key, filename=fname, url=f"{_HF}/{repo}/resolve/main/{fname}",
        sha256=sha256, size_bytes=size, min_ram_gb=min_ram, supports_reasoning=reasoning, default_ctx_eco=ctx_eco, default_ctx_perf=ctx_perf,
    )


RUNTIME_ASSETS: dict[LocalAiPlatformKey, LocalAiRuntimeAsset] = {
    "macos-arm64": _asset("macos-arm64", "macos-arm64.tar.gz", "8de65a20e743b27405f05e6f89c636b879fd040fdd2c9abd4730fc0632ca49a5", 16_599_970),
    "macos-x64": _asset("macos-x64", "macos-x64.tar.gz", "3c785878e79257be7ba52c08b1303871a5b64665866036824b15c11c7b008e26", 12_382_009),
    "win-vulkan-x64": _asset("win-vulkan-x64", "win-vulkan-x64.zip", "f54121061f29cfcd59a3e3ca17870c41957f4a226146185ab6c5297258203fc4", 38_879_485, "llama-server.exe"),
    "win-vulkan-arm64": _asset("win-vulkan-arm64", "win-vulkan-arm64.zip", "5fdf0f935f00b83b55368d03c8ad8a3500ee0bc0e4b306776150b31c839a3727", 26_556_492, "llama-server.exe"),
    "linux-vulkan-x64": _asset("linux-vulkan-x64", "ubuntu-vulkan-x64.tar.gz", "ddaa5ca038cafffd4a858488a2ca6e2b703077e4cfa55b4d3f96f8a5590afa51", 36_909_311),
    "linux-vulkan-arm64": _asset("linux-vulkan-arm64", "ubuntu-vulkan-arm64.tar.gz", "744ddc8bf67f0824bfdcb43e1f764b5c97a2054b49f650438cc41c946b8a1e20", 29_867_386),
}

MODEL_PRESETS: tuple[LocalAiModelPreset, ...] = (
    _preset("ultra-qwen25-1.5b", "ultra_light", "lai_tier_ultra", "Qwen/Qwen2.5-1.5B-Instruct-GGUF", "qwen2.5-1.5b-instruct-q4_k_m.gguf", "6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e", 1_117_320_736, 4, reasoning=False, ctx_eco=2048, ctx_perf=4096),
    _preset("compact-qwen3-4b", "compact", "lai_tier_compact", "Qwen/Qwen3-4B-GGUF", "Qwen3-4B-Q4_K_M.gguf", "7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5", 2_497_280_256, 8, ctx_eco=4096, ctx_perf=4096),
    _preset("balanced-qwen3-8b", "balanced", "lai_tier_balanced", "Qwen/Qwen3-8B-GGUF", "Qwen3-8B-Q4_K_M.gguf", "d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785", 5_027_783_488, 16, ctx_eco=4096, ctx_perf=8192),
    _preset("deep-qwen3-14b", "deep", "lai_tier_deep", "Qwen/Qwen3-14B-GGUF", "Qwen3-14B-Q4_K_M.gguf", "500a8806e85ee9c83f3ae08420295592451379b4f8cf2d0f41c15dffeb6b81f0", 9_001_752_960, 32, ctx_eco=8192, ctx_perf=16384),
)

MODEL_BY_ID: dict[str, LocalAiModelPreset] = {p.id: p for p in MODEL_PRESETS}


def is_allowed_download_url(raw_url: str) -> bool:
    parsed = urlparse((raw_url or "").strip())
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        return False
    return host in ALLOWED_DOWNLOAD_HOSTS or host.endswith((".hf.co", ".githubusercontent.com"))


def detect_platform_key(plat: str | None = None, arch: str | None = None) -> LocalAiPlatformKey | None:
    os_name = (plat or sys.platform).lower()
    machine = (arch or platform.machine()).lower()
    is_arm, is_x64 = machine in {"arm64", "aarch64"}, machine in {"x86_64", "amd64"}
    if os_name == "darwin":
        return "macos-arm64" if is_arm else ("macos-x64" if is_x64 else None)
    if os_name == "win32":
        return "win-vulkan-arm64" if is_arm else ("win-vulkan-x64" if is_x64 else None)
    if os_name.startswith("linux"):
        return "linux-vulkan-arm64" if is_arm else ("linux-vulkan-x64" if is_x64 else None)
    return None


def recommend_model_for_ram(ram_gb: int) -> LocalAiModelPreset:
    if ram_gb >= 32:
        return MODEL_BY_ID["deep-qwen3-14b"]
    if ram_gb >= 16:
        return MODEL_BY_ID["balanced-qwen3-8b"]
    if ram_gb >= 8:
        return MODEL_BY_ID["compact-qwen3-4b"]
    return MODEL_BY_ID["ultra-qwen25-1.5b"]


def compute_runtime_limits(ram_gb: int, profile: LocalAiProfile, preset: LocalAiModelPreset, cores: int | None = None) -> tuple[int, int, int]:
    """Return (threads, ctx_size, default_idle_minutes) enforcing thermal & RAM guardrails."""
    phys = max(2, detect_physical_cores() if cores is None else cores)
    if profile == "performance":
        threads = max(2, min(12, round(phys * 0.70)))
        ctx = preset.default_ctx_perf
        if 0 < ram_gb < 6:
            ctx = min(ctx, 2048)
        elif 0 < ram_gb < 16:
            ctx = min(ctx, 4096)
        return threads, ctx, 10
    threads = max(2, min(8, round(phys * 0.50)))
    return threads, preset.default_ctx_eco, 5


def build_llama_server_args(binary: str, model: str, port: int, token: str, ctx: int, threads: int, reasoning: bool, use_cpu: bool) -> list[str]:
    """Build hardened, loopback-only llama-server launch arguments."""
    args = [
        binary, "--model", model, "--host", "127.0.0.1", "--port", str(port), "--api-key", token,
        "--ctx-size", str(ctx), "--threads", str(threads), "--threads-batch", str(threads),
        "--cache-type-k", "q8_0", "--cache-type-v", "q8_0", "--jinja", "--no-webui", "--parallel", "1",
        "--n-gpu-layers", "0" if use_cpu else "99",
    ]
    if reasoning:
        args.extend(["--reasoning-format", "deepseek"])
    if use_cpu:
        args.extend(["--device", "none"])
    return args
