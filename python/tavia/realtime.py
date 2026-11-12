"""Realtime voice sessions: one Call per WebSocket, wire events and friendly events out, audio and tools in."""

import asyncio
import inspect
import json
import logging
import re
import warnings
from collections.abc import Callable
from typing import Any, Protocol
from urllib.parse import urlencode

from tavia._transport import Callback, Context, SocketSession, Unsubscribe, open_socket
from tavia.audio import base64_to_pcm16, pcm16_ms, pcm16_to_base64
from tavia.dialect import Dialect, standard_event, standard_type, wire_session
from tavia.errors import TOOL_FAILED, TaviaError, ToolError, error_for_code
from tavia.generated.spec import DIALECT, FRIENDLY_EVENTS, LIMITS, PRESET_PARAM, SERVER_EVENT_TYPES, SESSION_OPTIONS
from tavia.generated.types import SessionConfig

__all__ = ["FRIENDLY_MAPPERS", "Call", "Player", "Realtime", "to_friendly"]

log = logging.getLogger("tavia")

MAX_AUDIO_BYTES = LIMITS["realtime.maxAudioBytes"] - LIMITS["realtime.maxAudioBytes"] % 2
OUTPUT_RATE = LIMITS["realtime.outputRates"][0]
TOOL_NAME = re.compile(LIMITS["limits.toolNameRegex"])
MESSAGE_ROLES = ("user", "system")
FRIENDLY_NAMES = frozenset(FRIENDLY_EVENTS.values())
CALL_EVENTS = frozenset(SERVER_EVENT_TYPES) | FRIENDLY_NAMES
# Runs a client tool: gets the parsed arguments, returns (or awaits to) the output sent to the agent.
ToolHandler = Callable[[dict], Any]


class Player(Protocol):
    """Plays agent audio. May also offer played_ms() -> float: ms played since the last flush.

    With played_ms, Call.interrupt() also tells the server how much of the reply the caller heard.
    """

    def enqueue(self, pcm: bytes) -> None:
        """Queues PCM16 mono at the output rate to play after what is already queued."""

    def flush(self) -> None:
        """Stops playback at once and drops everything queued."""


def _transcript(role: str, key: str, final: bool) -> Callable[[dict], dict]:
    return lambda e: {"role": role, "text": e[key], "final": final}


def _agent_delta(e: dict) -> dict:
    data = {"role": "agent", "text": e["delta"], "final": False}
    if "audio_start_ms" in e:
        data["audio_start_ms"] = e["audio_start_ms"]
    return data


def _tool_call(e: dict) -> dict:
    data = {"turn_id": e["turn_id"], "name": e["name"], "arguments": e["arguments"], "output": e["output"]}
    if e.get("duration_ms") is not None:
        data["duration_ms"] = e["duration_ms"]
    return data


def _reply_start(e: dict) -> dict:
    """turn_id: the caller turn the reply answers, as on its tool_call and timing events; absent for a greeting."""
    turn_id = (e["response"].get("metadata") or {}).get("turn_id")
    return {"phase": "reply_start", "turn_id": turn_id} if turn_id else {"phase": "reply_start"}


# Server event type -> friendly event data; FRIENDLY_EVENTS gives each one's friendly name.
FRIENDLY_MAPPERS: dict[str, Callable[[dict], dict]] = {
    "conversation.item.input_audio_transcription.delta": _transcript("caller", "transcript", False),
    "conversation.item.input_audio_transcription.completed": _transcript("caller", "transcript", True),
    "response.output_audio_transcript.delta": _agent_delta,
    "response.output_audio_transcript.done": _transcript("agent", "transcript", True),
    "input_audio_buffer.speech_started": lambda e: {"phase": "speech_started"},
    "input_audio_buffer.speech_stopped": lambda e: {"phase": "speech_stopped"},
    "response.created": _reply_start,
    "turn.interrupted": lambda e: {"heard_text": e["heard_text"], "audio_end_ms": e["audio_end_ms"]},
    "turn.backchannel": lambda e: {"text": e["transcript"]},
    "turn.tool": _tool_call,
    "turn.timing": lambda e: {k: v for k, v in e.items() if k not in ("type", "event_id")},
    "turn.warning": lambda e: {"turn_id": e.get("turn_id"), "code": e["code"], "message": e["message"]},
    "error": lambda e: {"code": e["error"]["code"], "message": e["error"]["message"]},
    "response.output_audio.delta": lambda e: {"pcm": e["delta"]},
    "session.ended": lambda e: {"session_id": e["session_id"], "duration_ms": e["duration_ms"], "usage": e["usage"]},
}


def to_friendly(event: dict) -> tuple[str, dict] | None:
    """(friendly name, data) for a server event that has a friendly event, else None."""
    mapper = FRIENDLY_MAPPERS.get(event.get("type", ""))
    return None if mapper is None else (FRIENDLY_EVENTS[event["type"]], mapper(event))


def check_session(session: Any) -> None:
    """Checks a session dict before it is sent.

    Raises:
        TypeError: session is not a dict.
        ValueError: session has an unknown option; the message names it.
    """
    if not isinstance(session, dict):
        raise TypeError("session must be a dict of session options")
    unknown = sorted(set(session) - set(SESSION_OPTIONS))
    if unknown:
        raise ValueError(f"unknown session option(s) {', '.join(unknown)}; allowed: {', '.join(SESSION_OPTIONS)}")


def _tool_text(result: Any) -> str:
    return result if isinstance(result, str) else json.dumps(result)


class Call(SocketSession):
    """One realtime session. Subscribe with on(); every server event is also yielded by `async for`.

    Get one from tavia.realtime.connect(). Every send raises SessionClosedError once the socket has closed;
    close_code and close_error are set when it closes.

    Example:
        async with Tavia(os.environ["TAVIA_API_KEY"]) as tavia:
            call = await tavia.realtime.connect(session={"voice": "elaine", "instructions": "Be brief."})
            call.on("transcript", lambda t: show_line(t["role"], t["text"]) if t["final"] else None)

            @call.tool("find_order")
            async def find_order(args: dict) -> dict:
                return {"order_id": args["order_id"], "status": "shipped"}

            await call.send_audio(pcm)  # PCM16 mono at the session's input rate
            await call.wait_closed()
    """

    def __init__(self, socket: Any, player: Player | None = None, dialect: Dialect = "ga"):
        super().__init__(socket, CALL_EVENTS)
        self._player = player
        self._dialect = dialect
        self._events_asked = False
        self._tools: dict[str, ToolHandler] = {}
        self._exposed: set[str] = set()
        self._tasks: set[asyncio.Task] = set()
        self._ended = False
        self._enqueued_ms = 0.0
        self._item_offset_ms = 0.0
        self._audio_item: str | None = None

    def on(self, event: str, cb: Callback) -> Unsubscribe:
        """event: a wire type (cb gets the event dict) or a friendly name (cb gets its data).

        "error" is both; it delivers the friendly {code, message}. A renamed (beta) event name subscribes to its
        standard name, with a DeprecationWarning. Returns a function that unsubscribes; raises ValueError for an
        unknown event.
        """
        standard = standard_type(event)
        if standard != event:
            warnings.warn(
                f"the {event!r} event is now {standard!r}; subscribe to the new name", DeprecationWarning, stacklevel=2
            )
        return super().on(standard, cb)

    def on_error(self, cb: Callable[[TaviaError], Any]) -> Unsubscribe:
        """cb gets a typed TaviaError for each error event."""
        return self.on("error", lambda data: cb(error_for_code(data["code"], data["message"])))

    async def update(self, session: SessionConfig) -> None:
        """Changes session options; the server answers with session.updated. Raises as check_session does."""
        check_session(session)
        await self._send_json(self._session_event(session))

    def _session_event(self, session: SessionConfig) -> dict:
        if self._dialect == "beta":
            return {"type": "session.update", "session": dict(session)}
        first, self._events_asked = not self._events_asked, True
        return {"type": "session.update", "session": wire_session(session, with_events=first)}

    async def send_audio(self, pcm: bytes) -> None:
        """Sends caller audio: PCM16 mono at the session's input rate, split so no event passes the size limit.

        Raises ValueError for an odd number of bytes.
        """
        pcm = bytes(pcm)
        if len(pcm) % 2:
            raise ValueError("PCM16 audio must have an even number of bytes")
        for start in range(0, len(pcm), MAX_AUDIO_BYTES):
            chunk = pcm[start : start + MAX_AUDIO_BYTES]
            await self._send_json({"type": "input_audio_buffer.append", "audio": pcm16_to_base64(chunk)})

    async def send_text(self, text: str, role: str = "user") -> None:
        """Adds a text message from the caller ("user") or to the agent ("system"); then call create_response()."""
        if role not in MESSAGE_ROLES:
            raise ValueError(f"role must be one of {', '.join(MESSAGE_ROLES)}")
        item = {"type": "message", "role": role, "content": [{"type": "input_text", "text": text}]}
        await self._send_json({"type": "conversation.item.create", "item": item})

    async def send_tool_output(self, call_id: str, output: Any) -> None:
        """A client-run tool's result. The server goes on by itself unless the session set
        tool_auto_continue to False; then call create_response()."""
        item = {"type": "function_call_output", "call_id": call_id, "output": _tool_text(output)}
        await self._send_json({"type": "conversation.item.create", "item": item})

    async def send_task_status(self, call_id: str, label: str) -> None:
        """A deferred tool's short status while it runs (async tools), e.g. "checking stock"; then send_tool_output."""
        await self._send_json({"type": "task.status", "call_id": call_id, "label": label})

    async def truncate(self, item_id: str, audio_end_ms: float) -> None:
        """Tells the server the caller heard only the first audio_end_ms ms of a reply item."""
        event = {
            "type": "conversation.item.truncate",
            "item_id": item_id,
            "content_index": 0,
            "audio_end_ms": max(0, int(audio_end_ms)),
        }
        await self._send_json(event)

    async def create_response(self) -> None:
        """Asks the agent to reply now."""
        await self._send_json({"type": "response.create"})

    async def cancel_response(self) -> None:
        """Cancels the reply in progress, without flushing the player (see interrupt())."""
        await self._send_json({"type": "response.cancel"})

    async def commit_audio(self) -> None:
        """Ends the caller turn now; with turn_detection None (push-to-talk), then call create_response."""
        await self._send_json({"type": "input_audio_buffer.commit"})

    async def clear_audio(self) -> None:
        """Drops the caller audio sent since the last turn."""
        await self._send_json({"type": "input_audio_buffer.clear"})

    def tool(
        self, name: str, handler: ToolHandler | None = None, *, expose_errors: bool = False
    ) -> Unsubscribe | Callable:
        """Runs handler(arguments dict) for each call of tool `name` and sends its result.

        A ToolError's message goes to the agent; any other exception is logged and sent as "tool_failed"
        (its text may hold internals) unless expose_errors=True. Returns an unregister function; with no
        handler, works as a decorator. Raises ValueError for a name the API would refuse.
        """
        if not TOOL_NAME.fullmatch(name):
            raise ValueError(f"tool name {name!r} must match {TOOL_NAME.pattern}")
        if handler is None:

            def register(fn: ToolHandler) -> ToolHandler:
                self._register(name, fn, expose_errors)
                return fn

            return register
        return self._register(name, handler, expose_errors)

    async def interrupt(self) -> None:
        """Stops the agent: cancels the reply, flushes the player and truncates the item at what was heard."""
        await self.cancel_response()
        cut = self._played_cut()
        self._flush_player()
        if cut is not None:
            await self.truncate(*cut)

    def _register(self, name: str, handler: ToolHandler, expose_errors: bool) -> Unsubscribe:
        if not callable(handler):
            raise TypeError("the tool handler must be callable")
        self._tools[name] = handler
        (self._exposed.add if expose_errors else self._exposed.discard)(name)

        def unregister() -> None:
            if self._tools.get(name) is handler:
                del self._tools[name]

        return unregister

    async def _receive(self, data: str | bytes) -> None:
        if not isinstance(data, str):
            return
        event = json.loads(data)
        if not isinstance(event, dict):
            return
        event = standard_event(event)
        kind = event.get("type")
        self._track_audio(event)
        self._push(event)
        if kind in SERVER_EVENT_TYPES and kind not in FRIENDLY_NAMES:
            await self._events.emit(kind, event)
        await self._emit_friendly(event)
        if kind == "response.function_call_arguments.done":
            self._dispatch_tool(event)

    async def _emit_friendly(self, event: dict) -> None:
        friendly = to_friendly(event)
        if friendly is None:
            return
        name, data = friendly
        if name == "ended":
            if self._ended:
                return
            self._ended = True
        await self._events.emit(name, data)

    def _track_audio(self, event: dict) -> None:
        if self._player is None:
            return
        if event.get("type") == "turn.interrupted":
            self._flush_player()
        elif event.get("type") == "response.output_audio.delta":
            pcm = base64_to_pcm16(event["delta"])
            if event.get("item_id") != self._audio_item:
                self._audio_item = event.get("item_id")
                self._item_offset_ms = self._enqueued_ms
            self._enqueued_ms += pcm16_ms(len(pcm), OUTPUT_RATE)
            self._player.enqueue(pcm)

    def _played_cut(self) -> tuple[str, int] | None:
        """(item, ms heard) while the current agent item is still playing, else None."""
        played_ms = getattr(self._player, "played_ms", None)
        if played_ms is None or self._audio_item is None:
            return None
        played = float(played_ms())
        if played >= self._enqueued_ms:
            return None
        return self._audio_item, int(max(0.0, played - self._item_offset_ms))

    def _flush_player(self) -> None:
        if self._player is not None:
            self._player.flush()
        self._enqueued_ms = self._item_offset_ms = 0.0
        self._audio_item = None

    def _dispatch_tool(self, event: dict) -> None:
        handler = self._tools.get(event.get("name", ""))
        if handler is None:
            return
        # Its own task: a slow tool never holds up audio or other events.
        task = asyncio.create_task(self._run_tool(handler, event))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _run_tool(self, handler: ToolHandler, event: dict) -> None:
        try:
            result = handler(json.loads(event.get("arguments") or "{}"))
            if inspect.isawaitable(result):
                result = await result
            output = _tool_text(result)
        except ToolError as exc:
            output = json.dumps({"error": str(exc)})
        except Exception as exc:
            log.exception("tavia: tool %r failed", event.get("name"))
            raw = event.get("name") in self._exposed
            output = json.dumps({"error": (str(exc) or type(exc).__name__) if raw else TOOL_FAILED})
        try:
            await self.send_tool_output(event.get("call_id", ""), output)
        except TaviaError as exc:
            log.warning("tavia: tool %r output not sent: %s", event.get("name"), exc)

    def _on_closed(self) -> None:
        if self._player is not None:
            self._flush_player()


class Realtime:
    """Realtime voice sessions, as tavia.realtime."""

    def __init__(self, ctx: Context):
        self._ctx = ctx

    async def connect(
        self,
        session: SessionConfig | None = None,
        preset: str | None = None,
        player: Player | None = None,
        bound_session: str | None = None,
        dialect: Dialect = "ga",
    ) -> Call:
        """Opens a call and sends its first session update.

        session: options sent as soon as the socket opens. preset: a saved agent configuration to start from.
        player: plays the agent's audio. bound_session: the session string tokens.create returned, sent first,
        unchanged. dialect: "beta" is deprecated, only for integrations written against the earlier event names.
        Raises ConnectError when the server cannot be reached or refuses the session.

            async with Tavia(api_key) as tavia:
                call = await tavia.realtime.connect(session={"voice": "elaine", "instructions": "Be brief."})
        """
        if session is not None:
            check_session(session)
        if bound_session is not None and not isinstance(bound_session, str):
            raise TypeError("bound_session is the session string from tokens.create, sent unchanged")
        if dialect == "beta":
            warnings.warn(
                "the beta dialect is deprecated; use the standard event names", DeprecationWarning, stacklevel=2
            )
        query = {DIALECT["param"]: dialect, **({PRESET_PARAM: preset} if preset else {})}
        url = f"{self._ctx.urls['realtime']}?{urlencode(query)}"
        call = Call(await open_socket(self._ctx, "voice", url), player, dialect)
        first = [{"bound": bound_session} if bound_session is not None else None, session]
        if dialect == "ga" and first == [None, None]:
            first = [{}]  # the friendly events need the turn events, which the first update turns on
        await call._begin(*(call._session_event(s) for s in first if s is not None))
        return call
