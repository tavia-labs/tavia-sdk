"""Text-to-speech: a stream of contexts over a WebSocket, one-shot renders and the voice list over HTTP."""

import base64
import json
import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from tavia._transport import Context, SocketSession, open_socket, request
from tavia.errors import SessionClosedError, TaviaError, error_for_code
from tavia.generated.spec import LIMITS, SURFACE, TTS_STYLES

__all__ = ["Tts", "TtsAudio", "TtsDone", "TtsRender", "TtsStream", "parse_audio_frame"]

SAMPLE_RATE = SURFACE["tts"]["sampleRate"]
HEADER_BYTES = SURFACE["tts"]["headerBytes"]
RENDER_MAX_CHARS = SURFACE["tts"]["renderMaxChars"]
STOPPED = tuple(SURFACE["tts"]["stopped"])
CONTEXT_ID = re.compile(LIMITS["ttsStream.contextIdRegex"])
STREAM_EVENTS = ("audio", "done", "error")


@dataclass(frozen=True)
class TtsAudio:
    """PCM16 mono at 24 kHz for one context."""

    context_id: str
    pcm: bytes


@dataclass(frozen=True)
class TtsDone:
    """One per speak, in order. stopped: None, or one of length, cap, timeout, cancelled."""

    context_id: str
    audio_s: float
    first_audio_ms: float | None
    stopped: str | None


@dataclass(frozen=True)
class TtsRender:
    """A finished render: the sample rate in Hz, the length in seconds, a WAV file and the text's sentences."""

    sample_rate: int
    audio_s: float
    wav: bytes
    sentences: list = field(default_factory=list)


TtsMessage = TtsAudio | TtsDone | TaviaError


def parse_audio_frame(frame: bytes) -> TtsAudio:
    """A 16-byte header (context_id as ASCII, NUL-padded), then PCM16."""
    if len(frame) < HEADER_BYTES:
        raise ValueError("audio frame shorter than its header")
    return TtsAudio(frame[:HEADER_BYTES].rstrip(b"\0").decode("ascii"), frame[HEADER_BYTES:])


def _check_context(context_id: str) -> None:
    if not isinstance(context_id, str) or not CONTEXT_ID.match(context_id):
        raise ValueError(f"context_id must match {CONTEXT_ID.pattern}")


def _check_style(style: str | None) -> None:
    if style is not None and style not in TTS_STYLES:
        raise ValueError(f"style must be one of {', '.join(TTS_STYLES)}")


def _parse_json(msg: dict) -> tuple[str, TtsMessage] | None:
    if msg.get("type") == "done":
        return "done", TtsDone(
            msg.get("context_id", ""), msg.get("audio_s", 0.0), msg.get("first_audio_ms"), msg.get("stopped")
        )
    if msg.get("type") == "error":
        return "error", error_for_code(
            msg.get("code") or "internal", msg.get("message"), context_id=msg.get("context_id")
        )
    return None


class TtsStream(SocketSession):
    """A speech stream. Events: audio, done, error; `async for` yields the same objects.

    A context is one agent reply. An error with a context_id replaces that speak's done and the session goes on;
    one without ends it.

    Example:
        async with Tavia(os.environ["TAVIA_API_KEY"]) as tavia:
            tts = await tavia.tts.stream("elaine")
            tts.on("audio", lambda a: player.enqueue(a.pcm))
            await tts.speak("reply1", "Hello there!", "en")
            await tts.close_context("reply1")
            await tts.end()
    """

    def __init__(self, socket: Any, voice: str, session_id: str):
        super().__init__(socket, STREAM_EVENTS)
        self.voice = voice
        self.session_id = session_id
        self._opened = False
        self._fatal: TaviaError | None = None

    async def open(self) -> None:
        """Sends the start frame; client.tts.stream() does this for you."""
        if self._opened:
            raise RuntimeError("the stream is already open")
        self._opened = True
        await self._begin(
            {"type": "start", "voice": self.voice, "session_id": self.session_id, "sample_rate": SAMPLE_RATE}
        )

    async def speak(self, context_id: str, text: str, lang: str, style: str | None = None) -> None:
        """Queues text to speak in a context. Raises ValueError for a bad context_id or an unknown style."""
        _check_context(context_id)
        _check_style(style)
        frame = {"type": "speak", "context_id": context_id, "text": text, "lang": lang}
        if style is not None:
            frame["style"] = style
        await self._send_json(frame)

    async def close_context(self, context_id: str) -> None:
        """The reply is complete; its queued speaks still play."""
        _check_context(context_id)
        await self._send_json({"type": "close_context", "context_id": context_id})

    async def cancel(self, context_id: str) -> None:
        """Stops now: drops the context's queued speaks. Send it on barge-in."""
        _check_context(context_id)
        await self._send_json({"type": "cancel", "context_id": context_id})

    async def end(self) -> None:
        """No more speaks: queued speaks finish, then the server closes.

        Raises SessionClosedError (with the close code; the cause is the error) if the session ended on an error.
        """
        await self._send_json({"type": "end"})
        await self.wait_closed()
        failure = self._fatal or self.close_error
        if failure is not None:
            raise SessionClosedError(self.close_code) from failure

    async def _receive(self, data: str | bytes) -> None:
        if isinstance(data, (bytes, bytearray, memoryview)):
            parsed: tuple[str, TtsMessage] | None = ("audio", parse_audio_frame(bytes(data)))
        else:
            msg = json.loads(data)
            parsed = _parse_json(msg) if isinstance(msg, dict) else None
        if parsed is None:
            return
        name, item = parsed
        if isinstance(item, TaviaError) and item.context_id is None:
            self._fatal = item
        self._push(item)
        await self._events.emit(name, item)


class Tts:
    """Text-to-speech, as tavia.tts: live streams, one-shot renders and the voice list."""

    def __init__(self, ctx: Context):
        self._ctx = ctx

    async def stream(self, voice: str, session_id: str | None = None) -> TtsStream:
        """Opens a stream in `voice` and sends its start frame; session_id defaults to a random id."""
        socket = await open_socket(self._ctx, "tts", self._ctx.urls["ttsStream"])
        stream = TtsStream(socket, voice, session_id or uuid.uuid4().hex)
        await stream.open()
        return stream

    async def render(self, voice: str, text: str, lang: str, style: str | None = None) -> TtsRender:
        """One short text as a WAV (PCM16 mono 24 kHz).

        Raises ValueError for text over the render character limit or an unknown style.
        """
        if len(text) > RENDER_MAX_CHARS:
            raise ValueError(f"text is at most {RENDER_MAX_CHARS} characters")
        _check_style(style)
        payload = {"voice": voice, "text": text, "lang": lang}
        if style is not None:
            payload["style"] = style
        body = await request(self._ctx, "POST", self._ctx.urls["ttsRender"], json=payload)
        return TtsRender(
            sample_rate=body["sample_rate"],
            audio_s=body["audio_s"],
            wav=base64.b64decode(body["wav_base64"]),
            sentences=list(body.get("sentences") or []),
        )

    async def voices(self) -> dict:
        """The public voices as {voices, default, by_language}: each voice's languages, the default voice id,
        and the fallback voice id for each language."""
        return await request(self._ctx, "GET", self._ctx.urls["voices"])
