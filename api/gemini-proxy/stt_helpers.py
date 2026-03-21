"""
Google Cloud Speech-to-Text: choose encoding / sample rate and optionally convert
browser AAC/M4A (Safari) to WAV LINEAR16 via ffmpeg (Docker/Cloud Run).
"""
from __future__ import annotations

import os
import shutil
import struct
import subprocess
import tempfile
from typing import Optional, Tuple

from google.cloud import speech_v1

Encoding = speech_v1.RecognitionConfig.AudioEncoding


def _sniff_container(audio: bytes) -> str:
    """Best-effort magic-byte sniff for container type."""
    if len(audio) < 12:
        return ""
    if audio[:4] == b"RIFF" and len(audio) > 12 and audio[8:12] == b"WAVE":
        return "wav"
    if audio[:3] == b"ID3" or (audio[0] == 0xFF and (audio[1] & 0xE0) == 0xE0):
        return "mp3"
    if len(audio) >= 4 and audio[0] == 0x1A and audio[1] == 0x45:
        return "webm"
    if audio[4:8] == b"ftyp":
        return "mp4"
    return ""


def _wav_sample_rate_hz(audio: bytes) -> int:
    """Parse sample rate from canonical PCM WAV header (fmt chunk)."""
    try:
        if audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
            return 48000
        offset = 12
        while offset + 8 <= len(audio):
            chunk_id = audio[offset : offset + 4]
            chunk_size = struct.unpack("<I", audio[offset + 4 : offset + 8])[0]
            chunk_data = offset + 8
            if chunk_id == b"fmt " and chunk_size >= 14:
                sr = struct.unpack("<I", audio[chunk_data + 4 : chunk_data + 8])[0]
                return int(sr) if 8000 <= sr <= 48000 else 48000
            offset = chunk_data + chunk_size
            if chunk_size % 2:
                offset += 1
    except Exception:
        pass
    return 48000


def _convert_to_wav_pcm_s16le_48k(audio_bytes: bytes, suffix: str) -> bytes:
    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "AAC/M4A audio needs ffmpeg on the server, or use Chrome/Edge which records WebM/Opus."
        )
    fd, in_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    out_path = in_path + ".wav"
    try:
        with open(in_path, "wb") as f:
            f.write(audio_bytes)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                in_path,
                "-acodec",
                "pcm_s16le",
                "-ac",
                "1",
                "-ar",
                "48000",
                out_path,
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
        with open(out_path, "rb") as wf:
            return wf.read()
    finally:
        for p in (in_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass


def build_recognition_config(
    *,
    encoding: Encoding,
    language_code: str,
    sample_rate_hertz: Optional[int],
) -> speech_v1.RecognitionConfig:
    """
    Google STT: MP3/FLAC often work best without a forced sample_rate_hertz.
    WEBM_OPUS / LINEAR16 need a rate that matches the audio.
    """
    kwargs = dict(
        encoding=encoding,
        language_code=language_code,
        enable_automatic_punctuation=True,
        model="latest_long",
    )
    if encoding in (
        Encoding.MP3,
        Encoding.FLAC,
    ):
        # Let API read rate from container where supported; avoids 'MP3' config errors.
        pass
    elif sample_rate_hertz is not None:
        kwargs["sample_rate_hertz"] = sample_rate_hertz
    return speech_v1.RecognitionConfig(**kwargs)


def prepare_audio_and_config(
    audio_bytes: bytes,
    filename: str,
    language_code: str,
) -> Tuple[bytes, speech_v1.RecognitionConfig]:
    """
    Normalize browser uploads to a format Google STT v1 accepts.
    Returns (bytes_to_send, RecognitionConfig).
    """
    ext = filename.rsplit(".", 1)[-1].lower() if filename and "." in filename else "webm"
    sniff = _sniff_container(audio_bytes)

    # Safari / iOS: often audio/mp4 saved as .m4a — not WEBM_OPUS; convert if possible.
    if ext in ("m4a", "mp4", "aac", "caf") or (ext == "webm" and sniff == "mp4"):
        audio_bytes = _convert_to_wav_pcm_s16le_48k(audio_bytes, f".{ext}")
        ext = "wav"
        sniff = "wav"

    encoding_map = {
        "webm": Encoding.WEBM_OPUS,
        "mp3": Encoding.MP3,
        "wav": Encoding.LINEAR16,
        "flac": Encoding.FLAC,
    }

    if ext not in encoding_map:
        if sniff == "webm":
            ext = "webm"
        elif sniff == "mp4":
            audio_bytes = _convert_to_wav_pcm_s16le_48k(audio_bytes, ".mp4")
            ext = "wav"
        elif sniff == "mp3":
            ext = "mp3"
        elif sniff == "wav":
            ext = "wav"
        else:
            ext = "webm"

    encoding = encoding_map.get(ext, Encoding.WEBM_OPUS)

    sample_rate: Optional[int] = None
    if encoding == Encoding.WEBM_OPUS:
        sample_rate = 48000
    elif encoding == Encoding.LINEAR16:
        sample_rate = _wav_sample_rate_hz(audio_bytes)
    elif encoding in (Encoding.MP3, Encoding.FLAC):
        sample_rate = None

    cfg = build_recognition_config(
        encoding=encoding,
        language_code=language_code,
        sample_rate_hertz=sample_rate,
    )
    return audio_bytes, cfg
