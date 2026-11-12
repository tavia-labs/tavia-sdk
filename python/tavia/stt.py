"""Speech-to-text: live streams over a WebSocket, and recorded files as jobs over HTTP."""

import asyncio
import json
import os
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO
from urllib.parse import quote

import httpx

from tavia._transport import Context, SocketSession, open_socket, request
from tavia.errors import TaviaError, error_for_code, error_for_http
from tavia.generated.spec import LIMITS, SURFACE

__all__ = ["Stt", "SttFinal", "SttFinished", "SttPartial", "SttStream", "parse_message"]

AUDIO_FORMAT = "pcm_s16le"  # the only audio format live streams take
SAMPLE_RATE = LIMITS["stt.sampleRate"]
DECODERS = tuple(SURFACE["stt"]["decoders"])
JOB_STATUSES = tuple(SURFACE["stt"]["jobStatuses"])
FIN = "<fin>"
STREAM_EVENTS = ("partial", "final", "finished", "error")
DEFAULT_FILE_NAME = "audio"
# A recording to transcribe: a path, raw bytes or a binary file object.
AudioFile = str | os.PathLike | bytes | bytearray | memoryview | BinaryIO
# Hint words: a list, or a str with one term per line.
Terms = str | list[str] | tuple[str, ...]


@dataclass(frozen=True)
class SttPartial:
    """The whole current hypothesis of the open turn; each partial replaces the previous one.

    Attributes:
        tokens: The tokens as sent: {text, start_ms?, end_ms?, is_final, confidence?, filler?}.
        text: The tokens joined.
        fillers: The hesitations heard: [{type, start_ms, end_ms, is_final, before}].
    """

    tokens: list[dict]
    text: str
    fillers: list = field(default_factory=list)


@dataclass(frozen=True)
class SttFinal:
    """One finished turn.

    Attributes:
        tokens: The tokens as sent, ending with the <fin> marker.
        text: The tokens joined; with include_fillers it holds the (um) markers too.
        formatted: The readable transcript, or None when the stream set format=False.
        empty: True when the turn has no words; still sent, one per finalize.
        decoder: The recognizer that produced it.
        nbest: Alternative transcripts with their scores, when the stream asked for them.
        total_audio_proc_ms: How much audio the server has processed, in ms.
        fillers: The turn's hesitations: [{type, start_ms, end_ms, is_final, before}].
    """

    tokens: list[dict]
    text: str
    formatted: str | None
    empty: bool
    decoder: str | None
    nbest: list = field(default_factory=list)
    total_audio_proc_ms: float | None = None
    fillers: list = field(default_factory=list)


@dataclass(frozen=True)
class SttFinished:
    """The server's last message after end()."""


SttMessage = SttPartial | SttFinal | SttFinished | TaviaError


def _join(tokens: list[dict]) -> str:
    return "".join(t.get("text", "") for t in tokens if t.get("text") != FIN).strip()


def _final(msg: dict, tokens: list[dict]) -> SttFinal:
    text = _join(tokens)
    return SttFinal(
        tokens=tokens,
        text=text,
        formatted=msg.get("formatted"),
        empty=bool(msg.get("empty", not text)),
        decoder=msg.get("decoder"),
        nbest=list(msg.get("nbest") or []),
        total_audio_proc_ms=msg.get("total_audio_proc_ms"),
        fillers=list(msg.get("fillers") or []),
    )


def parse_message(msg: dict) -> tuple[str, SttMessage] | None:
    """(event name, parsed message) for a server message, or None for one the SDK does not know."""
    if "error_code" in msg:
        err = error_for_http(int(msg["error_code"]), {"error": {"message": msg.get("error_message")}})
        return "error", err
    if msg.get("finished"):
        return "finished", SttFinished()
    tokens = msg.get("tokens")
    if not isinstance(tokens, list):
        return None
    if tokens and tokens[-1].get("text") == FIN:
        return "final", _final(msg, tokens)
    return "partial", SttPartial(tokens=tokens, text=_join(tokens), fillers=list(msg.get("fillers") or []))


def _check_decoder(decoder: str) -> None:
    if decoder not in DECODERS:
        raise ValueError(f"decoder must be one of {', '.join(DECODERS)}")


def _check_terms(terms: list[str]) -> None:
    """The server's own checks: a refused set_context ends the session, so refuse it here first."""
    if len(terms) > LIMITS["stt.terms"]:
        raise ValueError(f"context.terms must hold at most {LIMITS['stt.terms']} terms")
    size = sum(len(t.encode("utf-8", "replace")) for t in terms) + max(len(terms) - 1, 0)
    if size > LIMITS["limits.termsBytes"]:
        raise ValueError(f"context.terms must be at most {LIMITS['limits.termsBytes']} bytes")


def _terms_list(terms: Terms) -> list[str]:
    return terms.splitlines() if isinstance(terms, str) else [str(t) for t in terms]


class SttStream(SocketSession):
    """A live transcription stream. Events: partial, final, finished, error; `async for` yields the same objects.

    Example:
        async with Tavia(os.environ["TAVIA_API_KEY"]) as tavia:
            stt = await tavia.stt.stream(terms=["Tavia"])
            stt.on("final", lambda f: show_text(f.formatted or f.text))
            await stt.send_audio(pcm)  # PCM16 mono at 16 kHz by default
            await stt.end()
    """

    def __init__(self, socket: Any):
        super().__init__(socket, STREAM_EVENTS)
        self._settled = asyncio.Event()
        self._finished = False
        self._error: TaviaError | None = None

    async def send_audio(self, pcm: bytes) -> None:
        """Raw PCM16 mono at the config's sample rate, as a binary frame."""
        if pcm:
            await self._send(bytes(pcm))

    async def finalize(self) -> None:
        """Ends the current turn; the server always answers with a final."""
        await self._send_json({"type": SURFACE["stt"]["messages"]["finalize"]})

    async def set_decoder(self, decoder: str) -> None:
        """Switches the recognizer: "general", or "spell" while the caller spells something out."""
        _check_decoder(decoder)
        await self._send_json({"type": SURFACE["stt"]["messages"]["set_decoder"], "decoder": decoder})

    async def set_terms(self, terms: Terms) -> None:
        """Replaces the hint words: now if no audio came since the last final, else from the next turn.

        Raises ValueError over the API's term count or size limits.
        """
        listed = _terms_list(terms)
        _check_terms(listed)
        await self._send_json({"type": "set_context", "context": {"terms": listed}})

    async def keepalive(self) -> None:
        """Keeps an idle stream open while no audio is sent."""
        await self._send_json({"type": SURFACE["stt"]["messages"]["keepalive"]})

    async def end(self) -> None:
        """Ends the stream (an empty text frame) and waits for the server's finished message.

        Raises the stream's error, or a TaviaError, if it closed before it finished.
        """
        await self._send("")
        await self._settled.wait()
        if not self._finished:
            raise self._error or self.close_error or TaviaError("the stream closed before it finished")

    async def _receive(self, data: str | bytes) -> None:
        if not isinstance(data, str):
            return
        msg = json.loads(data)
        parsed = parse_message(msg) if isinstance(msg, dict) else None
        if parsed is None:
            return
        name, item = parsed
        if name == "error":
            self._error = item  # type: ignore[assignment]
        self._push(item)
        await self._events.emit(name, item)
        if name == "finished":
            self._finished = True
            self._settled.set()

    def _on_closed(self) -> None:
        self._settled.set()


async def _read_file(file: AudioFile) -> tuple[str, bytes]:
    if isinstance(file, (bytes, bytearray, memoryview)):
        return DEFAULT_FILE_NAME, bytes(file)
    if isinstance(file, (str, os.PathLike)):
        path = Path(file)
        return path.name, await asyncio.to_thread(path.read_bytes)
    if hasattr(file, "read"):
        data = await asyncio.to_thread(file.read)
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("open the file in binary mode")
        name = getattr(file, "name", None)
        return (Path(name).name if isinstance(name, str) else DEFAULT_FILE_NAME), bytes(data)
    raise TypeError("file must be a path, bytes or a binary file object")


class Stt:
    """Speech-to-text, as tavia.stt: live streams and recorded files."""

    def __init__(self, ctx: Context):
        self._ctx = ctx

    async def stream(
        self,
        *,
        audio_format: str = AUDIO_FORMAT,
        sample_rate: int = SAMPLE_RATE,
        num_channels: int | None = None,
        decoder: str | None = None,
        context: dict | None = None,
        nbest: int | None = None,
        format: bool | None = None,
        include_fillers: bool | None = None,
        client_reference_id: str | None = None,
        terms: Terms | None = None,
    ) -> SttStream:
        """Opens a live stream and sends its config.

        Args:
            audio_format: Always "pcm_s16le", the default.
            sample_rate: The audio's sample rate in Hz.
            num_channels: Always 1: mono.
            decoder: The recognizer to start with, "general" (default) or "spell".
            context: {"terms": [...]}: hint words, such as names and product terms.
            nbest: How many alternative transcripts each final carries.
            format: True (default): each final also carries formatted, the readable transcript.
            include_fillers: True: tokens also carry each hesitation as a (um) / (um…) marker in place.
            client_reference_id: Your own id for the stream.
            terms: Short for context={"terms": [...]}.

        Raises:
            ValueError: an unknown decoder.
            ConnectError: the server cannot be reached or refuses the stream.
        """
        if decoder is not None:
            _check_decoder(decoder)
        if terms is not None:
            context = {**(context or {}), "terms": _terms_list(terms)}
        fields = {
            "audio_format": audio_format,
            "sample_rate": sample_rate,
            "num_channels": num_channels,
            "decoder": decoder,
            "context": context,
            "nbest": nbest,
            "format": format,
            "include_fillers": include_fillers,
            "client_reference_id": client_reference_id,
        }
        config = {key: value for key, value in fields.items() if value is not None}
        stream = SttStream(await open_socket(self._ctx, "stt", self._ctx.urls["sttLive"]))
        await stream._begin(config)
        return stream

    async def create_job(self, file: AudioFile, terms: Terms | None = None) -> str:
        """Uploads a recording; returns the job id. terms: a list, or a str with one term per line.

        Raises TooLargeError for a file over the size limit.
        """
        name, data = await _read_file(file)
        if len(data) > LIMITS["stt.fileBytes"]:
            raise error_for_code("too_large")
        form = None if terms is None else {"terms": "\n".join(_terms_list(terms))}
        body = await request(self._ctx, "POST", self._ctx.urls["sttFiles"], files={"file": (name, data)}, data=form)
        return body["job_id"]

    async def get_job(self, job_id: str) -> dict:
        """A job as {status, progress, result?, error?}; result is set once status is "done"."""
        return await request(self._ctx, "GET", self._job_url(job_id))

    async def delete_job(self, job_id: str) -> None:
        """Deletes a job and its transcript from the server."""
        await request(self._ctx, "DELETE", self._job_url(job_id))

    async def transcribe(
        self, file: AudioFile, terms: Terms | None = None, poll_s: float = 2.0, keep: bool = False
    ) -> dict:
        """Uploads, polls every poll_s seconds until done and returns the result; deletes the job unless keep.

        Raises the job's typed error when transcription fails.
        """
        job_id = await self.create_job(file, terms)
        try:
            return await self._wait(job_id, poll_s)
        finally:
            if not keep:
                with suppress(TaviaError, httpx.HTTPError):
                    await self.delete_job(job_id)

    async def _wait(self, job_id: str, poll_s: float) -> dict:
        while True:
            job = await self.get_job(job_id)
            if job.get("status") == "done":
                return job["result"]
            if job.get("status") == "failed":
                raise error_for_code(job.get("error") or "transcription_failed")
            await asyncio.sleep(poll_s)

    def _job_url(self, job_id: str) -> str:
        return f"{self._ctx.urls['sttFiles']}/{quote(job_id, safe='')}"
