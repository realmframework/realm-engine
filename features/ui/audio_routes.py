"""Multi-provider TTS (Local Ollama Phonon, OpenAI TTS, ElevenLabs) and Whisper STT routes."""

import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import Response
from starlette.datastructures import UploadFile

from core.contracts import WorkspaceConfig
from core.secrets import get_api_key
from features.ui.audio_text import truncate_speech_text as _truncate_speech_text
from features.ui.privacy import require_local

privacy_config: Callable[[], WorkspaceConfig] = WorkspaceConfig
cloud_admission: Callable[[str, str, str], None] = lambda *_args: None
router = APIRouter()
OLLAMA_BASE_URL = "http://127.0.0.1:11434"
OLLAMA_TAGS_URL, OLLAMA_SHOW_URL, OLLAMA_SPEECH_URL = f"{OLLAMA_BASE_URL}/api/tags", f"{OLLAMA_BASE_URL}/api/show", f"{OLLAMA_BASE_URL}/v1/audio/speech"
OPENAI_SPEECH_URL, ELEVENLABS_BASE_URL = "https://api.openai.com/v1/audio/speech", "https://api.elevenlabs.io/v1/text-to-speech"

EXCLUDED_RPG_PATTERNS = ("grub the ogre", "vyrmathrax", "thing under the stairs", "fairy godmother", "snow queen", "fennick", "captain silas", "sir bramwell", "master aldric", "morwenna", "old mortlake")
KNOWN_VOICES: dict[str, list[str]] = {
    "en": ["default", "Zoey (US Female)", "Easton (US Male)", "Freya (UK Female)", "Hugh (UK Male)", "Hadley (US Female)", "Alfie", "Bryony", "Delia", "Edwin", "Elodie-Rose", "Everly", "Harper", "Imogen", "Juniper", "Lottie", "Maeve", "Micah", "Miles", "Pippa", "Preston", "Russell", "Spencer", "Teddy", "Toby", "Trevor"],
    "de": ["default", "Anton (DE Male)", "Henrik (DE Male)", "Lotte (DE Female)", "Maja (DE Female)", "Emil (DE Male)", "Greta (DE Female)", "f-de-1", "m-de-1"],
}
ELEVENLABS_VOICE_IDS: dict[str, str] = {"Rachel": "21m00Tcm4TlvDq8ikWAM", "Adam": "pNInz6obpgDQGcFmaJgB", "Josh": "TxGEqnHWrfWFTfGW9XjX", "Bella": "EXAVITQu4vr4xnSDxMaL"}
DEFAULT_PHONON_CATALOG: list[dict[str, object]] = [{"model": "phonon:latest", "provider": "ollama", "voices": KNOWN_VOICES["en"]}, {"model": "phonon:40m-de", "provider": "ollama", "voices": KNOWN_VOICES["de"]}]
CLOUD_TTS_CATALOG: list[dict[str, object]] = [
    {"model": "openai:tts-1", "provider": "openai", "voices": ["alloy", "nova", "echo"]},
    {"model": "elevenlabs:tts", "provider": "elevenlabs", "voices": list(ELEVENLABS_VOICE_IDS.keys())},
    {"model": "disabled", "provider": "disabled", "voices": ["none"]},
]

def _fallback_voices(model_name: str) -> list[str]:
    return list(KNOWN_VOICES["de"] if "-de" in model_name.lower() else KNOWN_VOICES["en"])

def strip_voice_label(voice: str) -> str:
    """Strip UI display suffix in parentheses (e.g. ``Zoey (US Female)`` -> ``Zoey``)."""
    return re.sub(r"\s*\(.*?\)\s*$", "", voice.strip()).strip() or "default"

def filter_human_voices(raw_voices: list[object], model_name: str = "phonon:latest") -> list[str]:
    """Filter a voice list strictly to natural human voices, excluding RPG/monster voices."""
    curated = [str(v) for v in raw_voices if str(v).strip() and not any(p in str(v).lower() for p in EXCLUDED_RPG_PATTERNS)]
    if not curated:
        return _fallback_voices(model_name)
    return curated if "default" in curated else ["default", *curated]

def _discover_model_voices(model_name: str) -> tuple[bool, list[str]]:
    is_speech = model_name.lower().startswith(("phonon", "kokoro", "piper", "tts-"))
    try:
        res = httpx.post(OLLAMA_SHOW_URL, json={"model": model_name}, timeout=1.0)
        if res.status_code == 200:
            data = res.json()
            caps, voices = data.get("capabilities"), data.get("voices")
            if isinstance(caps, list) and "speech" in [str(c).lower() for c in caps]:
                is_speech = True
            if isinstance(voices, list) and voices:
                return is_speech, filter_human_voices(voices, model_name)
    except (httpx.HTTPError, ValueError, KeyError):
        pass
    return is_speech, _fallback_voices(model_name)

def _discover_tts_models() -> tuple[list[dict[str, object]], bool]:
    discovered: list[dict[str, object]] = []
    speech_hints = ("phonon", "kokoro", "piper", "tts", "speech", "voice")
    try:
        res = httpx.get(OLLAMA_TAGS_URL, timeout=1.0)
        names = [str(m.get("name", "")) for m in res.json().get("models", []) if isinstance(m, dict) and m.get("name")] if res.status_code == 200 else []
        for name in names:
            low = name.lower()
            if any(h in low for h in speech_hints) and not low.startswith(("nomic-embed", "mxbai-embed", "bge-", "all-minilm", "whisper")):
                is_speech, voices = _discover_model_voices(name)
                if is_speech:
                    discovered.append({"model": name, "provider": "ollama", "voices": voices})
    except (httpx.HTTPError, ValueError, KeyError):
        pass
    return (discovered or list(DEFAULT_PHONON_CATALOG)), len(discovered) > 0

def _run_whisper_cli(whisper_bin: str, audio_bytes: bytes) -> str:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "input.wav").write_bytes(audio_bytes)
            subprocess.run([whisper_bin, str(tmp_path / "input.wav"), "--output_format", "txt", "--output_dir", str(tmp_path)], capture_output=True, text=True, timeout=15, check=False)
            return (tmp_path / "input.txt").read_text(encoding="utf-8", errors="replace").strip() if (tmp_path / "input.txt").is_file() else ""
    except (OSError, subprocess.SubprocessError):
        return ""

@router.get("/api/audio/status")
def api_audio_status() -> dict[str, object]:
    """Auto-discover local Whisper CLI, Ollama Phonon speech models, and cloud TTS providers."""
    whisper_ok = shutil.which("whisper") is not None
    local_models, phonon_installed = _discover_tts_models()
    return {"whisper_available": whisper_ok, "whisper_cli": whisper_ok, "phonon_available": phonon_installed, "tts_models": [*local_models, *CLOUD_TTS_CATALOG], "stt_engine": "whisper-cli" if whisper_ok else "unavailable" if privacy_config().strict_local_only else "web_speech", "tts_engine": "phonon" if phonon_installed else "unavailable" if privacy_config().strict_local_only else "cloud"}

@router.post("/api/audio/speak")
def api_audio_speak(payload: dict[str, object], x_api_key: str | None = Header(default=None, alias="x-api-key")) -> Response:
    """Synthesize speech via Local Phonon (Ollama), OpenAI TTS (tts-1), or ElevenLabs TTS."""
    raw_text = str(payload.get("text") or "").strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="Text is required for speech synthesis")
    model = str(payload.get("model") or "phonon:latest").strip() or "phonon:latest"
    require_local(privacy_config(), "openai" if model.startswith("openai") else "elevenlabs" if model.startswith("elevenlabs") else "ollama", model)
    if model == "disabled":
        raise HTTPException(status_code=400, detail="Voice output is disabled")
    voice, api_key, text = strip_voice_label(str(payload.get("voice") or "default")), str(payload.get("api_key") or x_api_key or "").strip(), _truncate_speech_text(raw_text, max_chars=4000)
    try:
        if model.startswith("openai"):
            key = get_api_key("openai", api_key)
            if not key:
                raise HTTPException(status_code=401, detail="OpenAI API key required for OpenAI TTS")
            cloud_admission("openai", text, "speech")
            oai_voice = voice.lower() if voice.lower() in ("alloy", "nova", "echo", "shimmer", "onyx", "fable") else "alloy"
            res = httpx.post(OPENAI_SPEECH_URL, headers={"Authorization": f"Bearer {key}"}, json={"model": "tts-1", "input": text, "voice": oai_voice, "response_format": "wav"}, timeout=30.0)
        elif model.startswith("elevenlabs"):
            key = get_api_key("elevenlabs", api_key)
            if not key:
                raise HTTPException(status_code=401, detail="ElevenLabs API key required for ElevenLabs TTS")
            cloud_admission("elevenlabs", text, "speech")
            vid = ELEVENLABS_VOICE_IDS.get(voice, ELEVENLABS_VOICE_IDS["Rachel"])
            res = httpx.post(f"{ELEVENLABS_BASE_URL}/{vid}", headers={"xi-api-key": key, "Accept": "audio/mpeg"}, json={"text": text, "model_id": "eleven_multilingual_v2"}, timeout=30.0)
        else:
            safe_voice = "default" if any(p in voice.lower() for p in EXCLUDED_RPG_PATTERNS) else voice
            body = {"model": model, "input": text, "voice": safe_voice, "response_format": "wav"}
            res = httpx.post(OLLAMA_SPEECH_URL, json=body, timeout=30.0)
            if res.status_code == 400 and safe_voice != "default":
                res = httpx.post(OLLAMA_SPEECH_URL, json={**body, "voice": "default"}, timeout=30.0)
        if res.status_code >= 400:
            raise HTTPException(status_code=res.status_code, detail=res.text or "Speech synthesis failed")
        return Response(content=res.content, media_type="audio/mpeg" if model.startswith("elevenlabs") else "audio/wav")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Speech endpoint unavailable: {exc}") from exc

@router.post("/api/audio/transcribe")
async def api_audio_transcribe(request: Request) -> dict[str, object]:
    """Transcribe uploaded audio via local Whisper CLI or return a Web Speech fallback."""
    form = await request.form() if "multipart/form-data" in request.headers.get("content-type", "") else None
    upload = (form.get("file") or form.get("audio")) if form else None
    audio_bytes = await upload.read() if isinstance(upload, UploadFile) else await request.body()
    whisper_bin = shutil.which("whisper")
    if whisper_bin and audio_bytes and (text := _run_whisper_cli(whisper_bin, audio_bytes)):
        return {"text": text, "engine": "whisper-cli"}
    fallback = "unavailable" if privacy_config().strict_local_only else "web_speech"
    return {"text": "", "fallback": fallback, "engine": fallback}
