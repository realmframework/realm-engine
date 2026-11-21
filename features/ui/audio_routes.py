"""Multi-provider TTS (Local Ollama Phonon, OpenAI TTS, ElevenLabs) and Whisper STT routes."""

import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from starlette.datastructures import UploadFile

from core.contracts import WorkspaceConfig
from core.runtime import is_loopback_url, ollama_base_url
from core.secrets import get_api_key
from features.ui.audio_text import truncate_speech_text as _truncate_speech_text
from features.ui.privacy import require_local

privacy_config: Callable[[], WorkspaceConfig] = WorkspaceConfig
def _noop(*_args: str) -> None:
    return None
cloud_admission: Callable[[str, str, str], None] = _noop
router, _ORIG_GET, _ORIG_POST = APIRouter(), httpx.get, httpx.post
OLLAMA_BASE_URL = ollama_base_url()
OLLAMA_TAGS_URL, OLLAMA_SHOW_URL, OLLAMA_SPEECH_URL = f"{OLLAMA_BASE_URL}/api/tags", f"{OLLAMA_BASE_URL}/api/show", f"{OLLAMA_BASE_URL}/v1/audio/speech"
OPENAI_SPEECH_URL, ELEVENLABS_BASE_URL = "https://api.openai.com/v1/audio/speech", "https://api.elevenlabs.io/v1/text-to-speech"
EXCLUDED_RPG_PATTERNS = ("grub the ogre", "vyrmathrax", "thing under the stairs", "fairy godmother", "snow queen", "fennick", "captain silas", "sir bramwell", "master aldric", "morwenna", "old mortlake")
KNOWN_VOICES: dict[str, list[str]] = {
    "en": ["default", "Zoey (US Female)", "Easton (US Male)", "Freya (UK Female)", "Hugh (UK Male)", "Hadley (US Female)", "Alfie", "Bryony", "Delia", "Edwin", "Elodie-Rose", "Everly", "Harper", "Imogen", "Juniper", "Lottie", "Maeve", "Micah", "Miles", "Pippa", "Preston", "Russell", "Spencer", "Teddy", "Toby", "Trevor"],
    "de": ["default", "Anton (DE Male)", "Henrik (DE Male)", "Lotte (DE Female)", "Maja (DE Female)", "Emil (DE Male)", "Greta (DE Female)", "f-de-1", "m-de-1"],
}
ELEVENLABS_VOICE_IDS: dict[str, str] = {"Rachel": "21m00Tcm4TlvDq8ikWAM", "Adam": "pNInz6obpgDQGcFmaJgB", "Josh": "TxGEqnHWrfWFTfGW9XjX", "Bella": "EXAVITQu4vr4xnSDxMaL"}
DEFAULT_PHONON_CATALOG: list[dict[str, object]] = [{"model": "phonon:latest", "provider": "ollama", "voices": KNOWN_VOICES["en"]}, {"model": "phonon:40m-de", "provider": "ollama", "voices": KNOWN_VOICES["de"]}]
CLOUD_TTS_CATALOG: list[dict[str, object]] = [{"model": "openai:tts-1", "provider": "openai", "voices": ["alloy", "nova", "echo"]}, {"model": "elevenlabs:tts", "provider": "elevenlabs", "voices": list(ELEVENLABS_VOICE_IDS.keys())}, {"model": "disabled", "provider": "disabled", "voices": ["none"]}]

def _local_req(method: str, url: str, timeout: float, payload: dict[str, object] | None = None) -> httpx.Response:
    if method == "GET" and httpx.get is not _ORIG_GET:
        return httpx.get(url, timeout=timeout)
    if method == "POST" and httpx.post is not _ORIG_POST:
        return httpx.post(url, json=payload, timeout=timeout)
    live_url = url.replace(OLLAMA_BASE_URL, ollama_base_url(), 1) if url.startswith(OLLAMA_BASE_URL) else url
    with httpx.Client(trust_env=not is_loopback_url(live_url), follow_redirects=False, timeout=timeout) as client:
        return client.get(live_url) if method == "GET" else client.post(live_url, json=payload)
def _speech_error_detail(status: int) -> str:
    if status in {401, 403}:
        return f"Speech provider rejected credentials (HTTP {status}). Check your API key in Settings."
    return "Speech provider rate limit or quota reached (HTTP 429). Wait a moment and try again." if status == 429 else f"Speech synthesis failed (HTTP {status})."
def _fallback_voices(model_name: str) -> list[str]:
    return list(KNOWN_VOICES["de"] if "-de" in model_name.lower() else KNOWN_VOICES["en"])
def strip_voice_label(voice: str) -> str:
    return re.sub(r"\s*\(.*?\)\s*$", "", voice.strip()).strip() or "default"
def filter_human_voices(raw_voices: list[object], model_name: str = "phonon:latest") -> list[str]:
    curated = [str(v) for v in raw_voices if str(v).strip() and not any(p in str(v).lower() for p in EXCLUDED_RPG_PATTERNS)]
    return (curated if "default" in curated else ["default", *curated]) if curated else _fallback_voices(model_name)

def _discover_model_voices(model_name: str) -> tuple[bool, list[str]]:
    is_speech = model_name.lower().startswith(("phonon", "kokoro", "piper", "tts-"))
    try:
        res = _local_req("POST", OLLAMA_SHOW_URL, 1.0, {"model": model_name})
        if res.status_code == 200 and isinstance((data := res.json()), dict):
            caps, voices = data.get("capabilities"), data.get("voices")
            is_speech = is_speech or (isinstance(caps, list) and "speech" in [str(c).lower() for c in caps])
            if isinstance(voices, list) and voices:
                return is_speech, filter_human_voices(voices, model_name)
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        pass
    return is_speech, _fallback_voices(model_name)

def _discover_tts_models() -> tuple[list[dict[str, object]], bool]:
    discovered, speech_hints = [], ("phonon", "kokoro", "piper", "tts", "speech", "voice")
    try:
        res = _local_req("GET", OLLAMA_TAGS_URL, 1.0)
        payload = res.json() if res.status_code == 200 else {}
        models = payload.get("models") if isinstance(payload, dict) else []
        for name in (str(m.get("name", "")) for m in (models or []) if isinstance(m, dict) and m.get("name")):
            low = name.lower()
            if any(h in low for h in speech_hints) and not low.startswith(("nomic-embed", "mxbai-embed", "bge-", "all-minilm", "whisper")):
                is_speech, voices = _discover_model_voices(name)
                if is_speech:
                    discovered.append({"model": name, "provider": "ollama", "voices": voices})
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
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
    whisper_ok, (local_models, phonon_installed) = shutil.which("whisper") is not None, _discover_tts_models()
    return {"whisper_available": whisper_ok, "whisper_cli": whisper_ok, "phonon_available": phonon_installed, "tts_models": [*local_models, *CLOUD_TTS_CATALOG], "stt_engine": "whisper-cli" if whisper_ok else "unavailable" if privacy_config().strict_local_only else "web_speech", "tts_engine": "phonon" if phonon_installed else "unavailable" if privacy_config().strict_local_only else "cloud"}

@router.post("/api/audio/speak")
def api_audio_speak(payload: dict[str, object], x_api_key: str | None = Header(default=None, alias="x-api-key")) -> Response:
    raw_text, model = str(payload.get("text") or "").strip(), str(payload.get("model") or "phonon:latest").strip() or "phonon:latest"
    if not raw_text:
        raise HTTPException(status_code=400, detail="Text is required for speech synthesis")
    require_local(privacy_config(), "openai" if model.startswith("openai") else "elevenlabs" if model.startswith("elevenlabs") else "ollama", model)
    if model == "disabled":
        raise HTTPException(status_code=400, detail="Voice output is disabled")
    voice, api_key, text = strip_voice_label(str(payload.get("voice") or "default")), str(payload.get("api_key") or x_api_key or "").strip(), _truncate_speech_text(raw_text, max_chars=4000)
    try:
        if model.startswith("openai"):
            if not (key := get_api_key("openai", api_key)):
                raise HTTPException(status_code=401, detail="OpenAI API key required for OpenAI TTS")
            cloud_admission("openai", text, "speech")
            oai_voice = voice.lower() if voice.lower() in ("alloy", "nova", "echo", "shimmer", "onyx", "fable") else "alloy"
            res = httpx.post(OPENAI_SPEECH_URL, headers={"Authorization": f"Bearer {key}"}, json={"model": "tts-1", "input": text, "voice": oai_voice, "response_format": "wav"}, timeout=30.0)
        elif model.startswith("elevenlabs"):
            if not (key := get_api_key("elevenlabs", api_key)):
                raise HTTPException(status_code=401, detail="ElevenLabs API key required for ElevenLabs TTS")
            cloud_admission("elevenlabs", text, "speech")
            vid = ELEVENLABS_VOICE_IDS.get(voice, ELEVENLABS_VOICE_IDS["Rachel"])
            res = httpx.post(f"{ELEVENLABS_BASE_URL}/{vid}", headers={"xi-api-key": key, "Accept": "audio/mpeg"}, json={"text": text, "model_id": "eleven_multilingual_v2"}, timeout=30.0)
        else:
            safe_voice = "default" if any(p in voice.lower() for p in EXCLUDED_RPG_PATTERNS) else voice
            body: dict[str, object] = {"model": model, "input": text, "voice": safe_voice, "response_format": "wav"}
            res = _local_req("POST", OLLAMA_SPEECH_URL, 30.0, body)
            if res.status_code == 400 and safe_voice != "default":
                res = _local_req("POST", OLLAMA_SPEECH_URL, 30.0, {**body, "voice": "default"})
        if res.status_code >= 400:
            raise HTTPException(status_code=res.status_code, detail=_speech_error_detail(res.status_code))
        return Response(content=res.content, media_type="audio/mpeg" if model.startswith("elevenlabs") else "audio/wav")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Speech endpoint is currently unavailable.") from exc

@router.post("/api/audio/transcribe")
async def api_audio_transcribe(request: Request) -> dict[str, object]:
    form = await request.form() if "multipart/form-data" in request.headers.get("content-type", "") else None
    try:
        upload = (form.get("file") or form.get("audio")) if form else None
        audio_bytes = await upload.read() if isinstance(upload, UploadFile) else await request.body()
    finally:
        if form is not None:
            await form.close()
    whisper_bin = shutil.which("whisper")
    if whisper_bin and audio_bytes and (text := await run_in_threadpool(_run_whisper_cli, whisper_bin, audio_bytes)):
        return {"text": text, "engine": "whisper-cli"}
    fallback = "unavailable" if privacy_config().strict_local_only else "web_speech"
    return {"text": "", "fallback": fallback, "engine": fallback}
