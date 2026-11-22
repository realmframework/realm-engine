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
    _preset("ultra-qwen35-2b", "ultra_light", "lai_tier_ultra", "unsloth/Qwen3.5-2B-GGUF", "Qwen3.5-2B-Q4_K_M.gguf", "aaf42c8b7c3cab2bf3d69c355048d4a0ee9973d48f16c731c0520ee914699223", 1_280_835_840, 4, ctx_eco=2048, ctx_perf=4096),
    _preset("compact-qwen35-4b", "compact", "lai_tier_compact", "unsloth/Qwen3.5-4B-GGUF", "Qwen3.5-4B-Q4_K_M.gguf", "00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4", 2_740_937_888, 8, ctx_eco=4096, ctx_perf=4096),
    _preset("balanced-qwen35-9b", "balanced", "lai_tier_balanced", "unsloth/Qwen3.5-9B-GGUF", "Qwen3.5-9B-Q4_K_M.gguf", "03b74727a860a56338e042c4420bb3f04b2fec5734175f4cb9fa853daf52b7e8", 5_680_522_464, 16, ctx_eco=4096, ctx_perf=8192),
    _preset("advanced-ministral3-14b", "advanced", "lai_tier_advanced", "unsloth/Ministral-3-14B-Instruct-2512-GGUF", "Ministral-3-14B-Instruct-2512-Q4_K_M.gguf", "76ce697c065f2e40f1e8e958118b02cab38e2c10a6015f7d7908036a292dc8c8", 8_239_067_840, 24, reasoning=False, ctx_eco=8192, ctx_perf=16384),
    _preset("flagship-muse-glimmer-30b", "flagship", "lai_tier_flagship", "meta-models/Muse-Glimmer-30B-GGUF", "Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf", "4cc57c0f51040a226e5a72cc47b7613f7772950e460a665f7083de89f183f60e", 16_756_683_904, 32, ctx_eco=8192, ctx_perf=16384),
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
        return MODEL_BY_ID["flagship-muse-glimmer-30b"]
    if ram_gb >= 24:
        return MODEL_BY_ID["advanced-ministral3-14b"]
    if ram_gb >= 16:
        return MODEL_BY_ID["balanced-qwen35-9b"]
    if ram_gb >= 8:
        return MODEL_BY_ID["compact-qwen35-4b"]
    return MODEL_BY_ID["ultra-qwen35-2b"]


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
        args.extend(["--reasoning-format", "auto"])
    if use_cpu:
        args.extend(["--device", "none"])
    return args
