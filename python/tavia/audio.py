"""PCM16 helpers: base64 for the realtime wire, and mono 16-bit WAV files in and out."""

import base64
import os
import wave
from typing import BinaryIO

__all__ = ["base64_to_pcm16", "pcm16_ms", "pcm16_to_base64", "read_wav", "write_wav"]

SAMPLE_BYTES = 2
WavFile = str | os.PathLike | BinaryIO


def pcm16_to_base64(pcm: bytes) -> str:
    """Encodes little-endian PCM16 bytes as base64, the form realtime audio events carry."""
    return base64.b64encode(bytes(pcm)).decode("ascii")


def base64_to_pcm16(data: str) -> bytes:
    """Decodes base64 audio from a realtime event into little-endian PCM16 bytes."""
    return base64.b64decode(data)


def pcm16_ms(n_bytes: int, sample_rate: int) -> float:
    """Duration of mono PCM16 audio in ms."""
    return n_bytes / SAMPLE_BYTES / sample_rate * 1000.0


def _target(file: WavFile) -> str | BinaryIO:
    # wave.open takes a str path or a file object, not a PathLike.
    return os.fspath(file) if isinstance(file, (str, os.PathLike)) else file


def read_wav(file: WavFile) -> tuple[bytes, int]:
    """A mono 16-bit WAV's PCM frames and sample rate; raises ValueError for any other WAV."""
    with wave.open(_target(file), "rb") as w:
        if w.getnchannels() != 1 or w.getsampwidth() != SAMPLE_BYTES:
            raise ValueError("need a mono 16-bit PCM WAV")
        return w.readframes(w.getnframes()), w.getframerate()


def write_wav(file: WavFile, pcm: bytes, sample_rate: int) -> None:
    """Writes mono PCM16 as a WAV file."""
    with wave.open(_target(file), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(SAMPLE_BYTES)
        w.setframerate(sample_rate)
        w.writeframes(bytes(pcm))
