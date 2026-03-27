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
    """Best-effort magic-byte sniff for container type.

    Order matters: MP4 (ftyp) and WebM/EBML must be checked *before* the MP3
    0xFF sync heuristic — that pattern also matches AAC-ADTS and other streams.
    Sending those bytes as Encoding.MP3 makes Speech-to-Text fail (often as \"MP3\").
    """
    if len(audio) < 12:
        return ""
    if audio[:4] == b"RIFF" and len(audio) > 12 and audio[8:12] == b"WAVE":
        return "wav"
    # ISO BMFF (Safari MediaRecorder: audio/mp4, video/mp4)
    if len(audio) >= 8 and audio[4:8] == b"ftyp":
        return "mp4"
    # Matroska / WebM EBML header (0x1A45DFA3)
    if len(audio) >= 4 and audio[0] == 0x1A and audio[1:4] == b"\x45\xdf\xa3":
        return "webm"
    # Looser WebM/Matroska (some muxers)
    if len(audio) >= 2 and audio[0] == 0x1A and audio[1] == 0x45:
        return "webm"
    if audio[:4] == b"fLaC":
        return "flac"
    # True MP3: ID3 tag or MPEG-1/2 audio frame sync (may also match AAC-ADTS — decode uses probe-first to avoid wrong demuxer)
    if audio[:3] == b"ID3":
        return "mp3"
    if len(audio) >= 2 and audio[0] == 0xFF and (audio[1] & 0xE0) == 0xE0:
        return "mp3"
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


def _wav_is_valid_pcm16_wav(audio: bytes) -> bool:
    """True if bytes look like a RIFF WAVE with PCM 16-bit mono/stereo (fmt chunk parsed)."""
    if len(audio) < 44 or audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
        return False
    return _wav_fmt_is_pcm16(audio)


def _wav_fmt_is_pcm16(audio: bytes) -> bool:
    """True if RIFF WAVE with PCM (format tag 1) and 16-bit samples."""
    try:
        if len(audio) < 44 or audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
            return False
        offset = 12
        while offset + 8 <= len(audio):
            chunk_id = audio[offset : offset + 4]
            chunk_size = struct.unpack("<I", audio[offset + 4 : offset + 8])[0]
            chunk_data = offset + 8
            if chunk_id == b"fmt " and chunk_size >= 16:
                w_format = struct.unpack("<H", audio[chunk_data : chunk_data + 2])[0]
                bits = struct.unpack("<H", audio[chunk_data + 14 : chunk_data + 16])[0]
                return w_format == 1 and bits == 16
            offset = chunk_data + chunk_size
            if chunk_size % 2:
                offset += 1
    except Exception:
        return False
    return False


def _ffmpeg_input_suffix(ext: str, sniff: str) -> str:
    """Pick a filename suffix so ffmpeg picks the right demuxer."""
    if sniff == "wav":
        return ".wav"
    if sniff == "mp4":
        return ".mp4"
    if sniff == "webm":
        return ".webm"
    if sniff == "mp3":
        return ".mp3"
    if sniff == "flac":
        return ".flac"
    e = (ext or "webm").lower().strip().lstrip(".")
    if e in ("webm", "mp4", "m4a", "aac", "mp3", "flac", "caf", "ogg", "opus"):
        return f".{e}"
    return ".bin"


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


def _convert_media_bytes_to_wav_probe(audio_bytes: bytes) -> bytes:
    """
    Decode audio whose format is ambiguous (MP3 vs AAC-ADTS, wrong extension, etc.).
    Lets ffmpeg probe the bitstream instead of forcing a demuxer via file extension.
    """
    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "ffmpeg is required to decode this audio. Use Chrome/Edge (WebM/Opus) or install ffmpeg."
        )
    fd, in_path = tempfile.mkstemp(prefix="stt_", suffix=".bin")
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
    Normalize browser uploads to mono PCM16 WAV @ 48 kHz before Google STT.

    Always send ``Encoding.LINEAR16`` with a matching sample rate. Sending
    WEBM_OPUS / MP3 / FLAC with mismatched bytes produces opaque API errors
    (often surfaced as just ``MP3``).
    """
    ext = filename.rsplit(".", 1)[-1].lower() if filename and "." in filename else "webm"
    sniff = _sniff_container(audio_bytes)

    # Filename from MIME can lie (e.g. audio/mpeg → .mp3 while bytes are WebM/Opus).
    if sniff == "webm" and ext in ("mp3", "mpeg", "mpga", "mpg"):
        ext = "webm"

    # Already what Google expects: PCM16 WAV (e.g. from a previous server-side transcode).
    if sniff == "wav" and _wav_is_valid_pcm16_wav(audio_bytes):
        sample_rate = _wav_sample_rate_hz(audio_bytes)
        cfg = build_recognition_config(
            encoding=Encoding.LINEAR16,
            language_code=language_code,
            sample_rate_hertz=sample_rate,
        )
        return audio_bytes, cfg

    # Everything else: ffmpeg → PCM16 WAV. Probe-first avoids wrong demuxer when
    # 0xFF sync is mis-sniffed as MP3 (AAC-ADTS etc.); fall back to suffix hint.
    hint = _ffmpeg_input_suffix(ext, sniff)
    last_err: Optional[Exception] = None
    for _, fn in (
        ("probe", lambda: _convert_media_bytes_to_wav_probe(audio_bytes)),
        ("hint", lambda: _convert_to_wav_pcm_s16le_48k(audio_bytes, hint)),
    ):
        try:
            candidate = fn()
            if _wav_is_valid_pcm16_wav(candidate):
                audio_bytes = candidate
                break
        except Exception as e:
            last_err = e
            continue
    else:
        msg = (
            "Could not decode audio for speech recognition "
            "(try Chrome/Edge WebM/Opus or a shorter clip)."
        )
        if last_err:
            raise RuntimeError(msg) from last_err
        raise RuntimeError(msg + " (invalid WAV after decode)")

    sample_rate = _wav_sample_rate_hz(audio_bytes)
    cfg = build_recognition_config(
        encoding=Encoding.LINEAR16,
        language_code=language_code,
        sample_rate_hertz=sample_rate,
    )
    return audio_bytes, cfg
