"""Offline spoken Audio Briefing script builder and pure-Python WAV stitcher."""

import io
import re
import wave
from collections.abc import Callable

from core.contracts import KnowledgeChunk
from core.scope import matches_scope

_MD_STRIP_RE = re.compile(r"[`*_#>]+|\[([^\]]+)\]\([^)]+\)")


def _spoken_clean(text: str, max_chars: int = 280) -> str:
    cleaned = _MD_STRIP_RE.sub(lambda m: m.group(1) or "", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    cut = cleaned[:max_chars]
    end = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))
    return cut[: end + 1].strip() if end > 60 else cut.rstrip() + "."


def build_briefing_script(
    chunks: list[KnowledgeChunk],
    mode: str = "solo",
    host_a: str = "Saga",
    host_b: str = "Blomkvist",
    doc_ids: list[str] | None = None,
    subfolder: str | None = None,
    area_label: str = "your workspace",
) -> list[dict[str, str]]:
    """Build a crisp, natural spoken briefing script (solo or two-voice duo) locally."""
    allowed = set(doc_ids) if doc_ids else None
    by_doc: dict[str, list[KnowledgeChunk]] = {}
    for chunk in chunks:
        if allowed is not None and chunk.doc_id not in allowed:
            continue
        if not matches_scope(chunk, None, subfolder):
            continue
        key = chunk.doc_id or chunk.file_path
        by_doc.setdefault(key, []).append(chunk)
    docs = list(by_doc.values())[:6]
    if not docs:
        return []
    a_name, b_name, duo = host_a.strip() or "Saga", host_b.strip() or "Blomkvist", mode == "duo"
    lines: list[dict[str, str]] = []
    if duo:
        lines.append({"speaker": a_name, "voice_slot": "a", "text": f"Welcome to your local REALM audio briefing for {area_label}. Today we're covering {len(docs)} key guides."})
        lines.append({"speaker": b_name, "voice_slot": "b", "text": "Let's cut straight to what matters and look at the main evidence across these notes."})
    else:
        lines.append({"speaker": a_name, "voice_slot": "a", "text": f"Here is your local REALM briefing for {area_label}, summarizing {len(docs)} key guides."})

    all_tags: list[str] = []
    for idx, doc_chunks in enumerate(docs):
        title = doc_chunks[0].title.split(" — ", 1)[0].strip() or f"Guide {idx + 1}"
        for c in doc_chunks:
            all_tags.extend(t for t in c.tags if t)
        lead = _spoken_clean(" ".join(c.content for c in doc_chunks[:2]), max_chars=260)
        if not lead:
            continue
        if duo and idx % 2 == 1:
            lines.append({"speaker": b_name, "voice_slot": "b", "text": f"Looking at {title}: {lead}"})
            if len(doc_chunks) > 2:
                extra = _spoken_clean(doc_chunks[2].content, max_chars=180)
                if extra and extra not in lead:
                    lines.append({"speaker": a_name, "voice_slot": "a", "text": f"And one detail worth keeping in mind: {extra}"})
        else:
            lines.append({"speaker": a_name, "voice_slot": "a", "text": f"First up, {title}. {lead}" if idx == 0 else f"Next, in {title}: {lead}"})
            if duo and len(doc_chunks) > 1:
                extra = _spoken_clean(doc_chunks[1].content, max_chars=170)
                if extra and extra not in lead:
                    lines.append({"speaker": b_name, "voice_slot": "b", "text": f"That connects directly to the core point: {extra}"})

    top_tags = list(dict.fromkeys(all_tags))[:4]
    tag_note = f" The strongest recurring themes are {', '.join(top_tags)}." if top_tags else ""
    if duo:
        lines.append({"speaker": a_name, "voice_slot": "a", "text": f"That wraps up your briefing.{tag_note} Everything stayed completely local on your device."})
    else:
        lines.append({"speaker": a_name, "voice_slot": "a", "text": f"That's the essence of these notes.{tag_note} Ask follow-up questions anytime."})
    return lines


def _is_wav(blob: bytes) -> bool:
    return len(blob) >= 12 and blob[:4] == b"RIFF" and blob[8:12] == b"WAVE"


def stitch_wav_segments(wav_blobs: list[bytes], pause_ms: int = 320) -> bytes:
    """Concatenate PCM WAV buffers safely with natural pauses using stdlib wave."""
    valid = [b for b in wav_blobs if _is_wav(b)]
    if not valid:
        return b""
    try:
        with wave.open(io.BytesIO(valid[0]), "rb") as first:
            params = first.getparams()
        if len(valid) == 1:
            return valid[0]
        silence_byte = b"\x80" if params.sampwidth == 1 else b"\x00"
        silence_frames = int(params.framerate * (pause_ms / 1000.0))
        silence = silence_byte * (silence_frames * params.nchannels * params.sampwidth)
        out = io.BytesIO()
        written = 0
        with wave.open(out, "wb") as dst:
            dst.setnchannels(params.nchannels)
            dst.setsampwidth(params.sampwidth)
            dst.setframerate(params.framerate)
            for idx, blob in enumerate(valid):
                try:
                    with wave.open(io.BytesIO(blob), "rb") as seg:
                        if (seg.getnchannels(), seg.getsampwidth(), seg.getframerate()) != (params.nchannels, params.sampwidth, params.framerate):
                            continue
                        dst.writeframes(seg.readframes(seg.getnframes()))
                        written += 1
                        if idx < len(valid) - 1:
                            dst.writeframes(silence)
                except (wave.Error, EOFError, OSError):
                    continue
        return out.getvalue() if written else b""
    except (wave.Error, EOFError, OSError):
        return b""


def synthesize_briefing_audio(
    script: list[dict[str, str]],
    speak_segment: Callable[[str, str], tuple[bytes, str] | None],
    voice_a: str = "default",
    voice_b: str = "Easton",
) -> tuple[bytes | None, str]:
    """Synthesize each script line via local TTS; stitch WAV blobs when compatible."""
    blobs: list[bytes] = []
    media_type = "audio/wav"
    for turn in script[:16]:
        voice = voice_b if turn.get("voice_slot") == "b" else voice_a
        spoken = speak_segment(turn.get("text", ""), voice)
        if not spoken:
            return None, ""
        raw, mime = spoken
        media_type = mime or media_type
        blobs.append(raw)
    if not blobs:
        return None, ""
    if all(_is_wav(b) for b in blobs):
        stitched = stitch_wav_segments(blobs)
        return (stitched, "audio/wav") if stitched else (None, "")
    return (blobs[0], media_type) if len(blobs) == 1 else (None, "")
