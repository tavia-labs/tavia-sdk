"""Shared plumbing for the three products: auth, URLs, sockets, HTTP and the event loop of a session."""

import asyncio
import inspect
import itertools
import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from contextlib import suppress
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlsplit, urlunsplit

import httpx
from websockets.exceptions import ConnectionClosed, InvalidStatus

from tavia.errors import ConnectError, SessionClosedError, TaviaError, error_for_close, error_for_http
from tavia.generated.spec import BASE_PATH, BASE_URL, LAYERS, PATHS, SURFACE, TOKEN_SUBPROTOCOL_PREFIX

log = logging.getLogger("tavia")

Callback = Callable[[Any], Any]
Unsubscribe = Callable[[], None]
HTTP_TIMEOUT = httpx.Timeout(120.0, connect=10.0)  # file uploads run up to the server's upload limit
ABNORMAL_CLOSE = 1006
DEFAULT_MAX_RETRIES = 2
RETRY_STATUSES = frozenset({429, 503})
BACKOFF_S = 0.5
MAX_BACKOFF_S = 8.0


class WebSocketLike(Protocol):
    """The part of a socket the SDK uses; a websockets connection or a test double."""

    async def send(self, data: str | bytes) -> None: ...

    async def recv(self) -> str | bytes: ...

    async def close(self) -> None: ...


WsConnect = Callable[[str, list[str], dict[str, str]], Awaitable[WebSocketLike]]


async def default_ws_connect(url: str, subprotocols: list[str], headers: dict[str, str]) -> WebSocketLike:
    from websockets.asyncio.client import connect

    return await connect(
        url,
        subprotocols=subprotocols,
        additional_headers=headers or None,  # type: ignore[arg-type]
        max_size=None,
    )


@dataclass(frozen=True)
class Auth:
    """A server holds an API key; a browser-style caller holds a short-lived token."""

    api_key: str | None = None
    token: str | None = None

    def http_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key or self.token}"}

    def ws_handshake(self, layer: str) -> tuple[list[str], dict[str, str]]:
        """A key rides as a Bearer header; a token as the second subprotocol, with no header."""
        subprotocol = LAYERS[layer]["subprotocol"]
        if self.api_key:
            return [subprotocol], self.http_headers()
        return [subprotocol, f"{TOKEN_SUBPROTOCOL_PREFIX}{self.token}"], {}


def _with_scheme(base: str, secure: str, plain: str, path: str) -> str:
    parts = urlsplit(base.rstrip("/"))
    scheme = secure if parts.scheme in ("https", "wss") else plain
    return urlunsplit((scheme, parts.netloc, parts.path + path, "", ""))


def ws_url(base: str, path: str) -> str:
    return _with_scheme(base, "wss", "ws", path)


def http_url(base: str, path: str) -> str:
    return _with_scheme(base, "https", "http", path)


URL_KEYS = tuple(SURFACE["urls"]["keys"])
_SOCKETS = frozenset({"realtime", "ttsStream"})
# The live speech-to-text socket is not served under the base URL; it keeps its own host.
_STT_LIVE_URL = ws_url(f"https://{LAYERS['stt']['host']}", PATHS["sttLive"])


def _camel(key: str) -> str:
    head, *rest = key.split("_")
    return head + "".join(w.title() for w in rest)


def endpoint_urls(base_url: str = BASE_URL) -> dict[str, str]:
    """Every endpoint's URL with base_url (e.g. https://api.tavialabs.com/v1) in front of its path."""
    base = base_url.rstrip("/")
    out = {"sttLive": _STT_LIVE_URL}
    for key, path in {**PATHS, "tokens": SURFACE["tokens"]["path"]}.items():
        if path.startswith(BASE_PATH + "/"):
            make = ws_url if key in _SOCKETS else http_url
            out[key] = make(base, path[len(BASE_PATH) :])
    return out


def build_urls(overrides: dict[str, str] | None = None, base_url: str | None = None) -> dict[str, str]:
    """Every endpoint under base_url (the public API by default), then a full URL per key in overrides, as given."""
    overrides = dict(overrides or {})
    unknown = sorted(set(overrides) - set(URL_KEYS))
    if unknown:
        raise ValueError(f"unknown url override(s) {', '.join(unknown)}; allowed: {', '.join(URL_KEYS)}")
    return {**endpoint_urls(base_url or BASE_URL), **{_camel(k): v for k, v in overrides.items()}}


class Context:
    """What every namespace shares: auth, endpoints, the socket factory and the HTTP client."""

    def __init__(
        self,
        auth: Auth,
        urls: dict[str, str],
        ws_connect: WsConnect | None,
        http: httpx.AsyncClient | None,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self.auth = auth
        self.urls = urls
        self.max_retries = max_retries
        self.ws_connect: WsConnect = ws_connect or default_ws_connect
        self._http = http
        self._owns_http = http is None

    @property
    def http(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=HTTP_TIMEOUT)
        return self._http

    async def aclose(self) -> None:
        if self._owns_http and self._http is not None:
            await self._http.aclose()
            self._http = None


def _response_body(response: httpx.Response) -> Any:
    if not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        return response.text


def _retry_delay(response: httpx.Response | None, attempt: int) -> float:
    """Retry-After in seconds when the server sends it, else exponential backoff."""
    try:
        return min(float(response.headers["retry-after"]), MAX_BACKOFF_S)  # type: ignore[union-attr]
    except (AttributeError, KeyError, ValueError):
        return min(BACKOFF_S * 2**attempt, MAX_BACKOFF_S)


def _should_retry(response: httpx.Response) -> bool:
    return response.status_code in RETRY_STATUSES and response.headers.get("x-should-retry") != "false"


async def _send(ctx: Context, method: str, url: str, **kwargs: Any) -> httpx.Response:
    """One attempt: the response, or the network failure as a ConnectError."""
    try:
        return await ctx.http.request(method, url, **kwargs)
    except httpx.TransportError as exc:
        raise ConnectError(message="could not reach the server") from exc


async def request(ctx: Context, method: str, url: str, **kwargs: Any) -> Any:
    """One authenticated request, retried as max_retries allows; a non-2xx answer raises its typed error."""
    headers = {**ctx.auth.http_headers(), **kwargs.pop("headers", {})}
    for attempt in itertools.count():
        response: httpx.Response | None = None
        try:
            response = await _send(ctx, method, url, headers=headers, **kwargs)
        except ConnectError:
            if attempt >= ctx.max_retries:
                raise
        if response is not None and response.status_code < 400:
            return _response_body(response)
        if response is not None and (attempt >= ctx.max_retries or not _should_retry(response)):
            raise error_for_http(response.status_code, _response_body(response))
        await asyncio.sleep(_retry_delay(response, attempt))


def _refused(exc: InvalidStatus) -> ConnectError:
    status = exc.response.status_code
    body: Any = None
    with suppress(ValueError, TypeError, AttributeError):
        body = json.loads(exc.response.body or b"")
    err = error_for_http(status, body)
    return ConnectError(http=status, code=err.code, message=f"the server refused the connection ({status})")


async def open_socket(ctx: Context, layer: str, url: str) -> WebSocketLike:
    """Opens a product socket with this client's credentials."""
    subprotocols, headers = ctx.auth.ws_handshake(layer)
    try:
        return await ctx.ws_connect(url, subprotocols, headers)
    except InvalidStatus as exc:
        raise _refused(exc) from exc
    except ConnectionClosed as exc:
        raise ConnectError(close_code_of(exc)) from exc


def close_code_of(exc: ConnectionClosed) -> int:
    for frame in (getattr(exc, "rcvd", None), getattr(exc, "sent", None)):
        if frame is not None:
            return int(frame.code)
    return ABNORMAL_CLOSE


class Emitter:
    """Named callbacks, sync or async; a raising callback is logged and never stops the session."""

    def __init__(self, names: Iterable[str]):
        self.names = frozenset(names)
        self._handlers: dict[str, list[Callback]] = {}

    def on(self, name: str, cb: Callback) -> Unsubscribe:
        if name not in self.names:
            raise ValueError(f"unknown event {name!r}; one of: {', '.join(sorted(self.names))}")
        if not callable(cb):
            raise TypeError("the callback must be callable")
        handlers = self._handlers.setdefault(name, [])
        handlers.append(cb)

        def off() -> None:
            with suppress(ValueError):
                handlers.remove(cb)

        return off

    async def emit(self, name: str, data: Any) -> None:
        for cb in list(self._handlers.get(name, ())):
            try:
                result = cb(data)
                if inspect.isawaitable(result):
                    await result
            except Exception:
                log.exception("tavia: a %r handler raised", name)


_DONE = object()


class SocketSession:
    """A live socket: a reader task feeds callbacks and `async for` iterators until the socket closes.

    close_code and close_error (None for a normal close) are set once it closes.
    """

    def __init__(self, socket: WebSocketLike, events: Iterable[str]):
        self._socket = socket
        self._events = Emitter(events)
        self._queues: list[asyncio.Queue] = []
        self._reader: asyncio.Task | None = None
        self._closed = asyncio.Event()
        self.close_code: int | None = None
        self.close_error: TaviaError | None = None

    def on(self, event: str, cb: Callback) -> Unsubscribe:
        """Calls cb (sync or async) for each such event; returns a function that unsubscribes it."""
        return self._events.on(event, cb)

    async def wait_closed(self) -> int | None:
        """Waits until the socket closes; returns its close code."""
        await self._closed.wait()
        return self.close_code

    async def close(self) -> None:
        """Closes the socket and waits for the reader to finish."""
        with suppress(Exception):
            await self._socket.close()
        if self._reader is None:
            self._finish(1000)
        await self._closed.wait()

    def __aiter__(self) -> AsyncIterator[Any]:
        queue: asyncio.Queue = asyncio.Queue()
        if self._closed.is_set():
            queue.put_nowait(_DONE)
        else:
            self._queues.append(queue)
        return self._drain(queue)

    async def _drain(self, queue: asyncio.Queue) -> AsyncIterator[Any]:
        try:
            while (item := await queue.get()) is not _DONE:
                yield item
        finally:
            with suppress(ValueError):
                self._queues.remove(queue)

    async def _begin(self, *first: dict | None) -> None:
        """Sends the opening frames, then starts reading. A socket already closed is a ConnectError."""
        for frame in (f for f in first if f is not None):
            try:
                await self._send_json(frame)
            except TaviaError as exc:
                with suppress(Exception):
                    await self._socket.close()
                raise ConnectError(exc.close_code) from exc
        self._reader = asyncio.create_task(self._read_loop())

    async def _read_loop(self) -> None:
        code: int | None = None
        try:
            while True:
                data = await self._socket.recv()
                try:
                    await self._receive(data)
                except Exception:
                    log.exception("tavia: a server message could not be handled")
        except ConnectionClosed as exc:
            code = close_code_of(exc)
        except Exception:
            log.exception("tavia: the session reader failed")
            code = ABNORMAL_CLOSE
        finally:
            self._finish(code)

    async def _receive(self, data: str | bytes) -> None:
        raise NotImplementedError

    def _on_closed(self) -> None:
        """Hook for subclasses: runs once when the socket closes."""

    def _finish(self, code: int | None) -> None:
        if self._closed.is_set():
            return
        self.close_code = code
        self.close_error = error_for_close(code) if code is not None else None
        self._on_closed()
        for queue in self._queues:
            queue.put_nowait(_DONE)
        self._closed.set()

    def _push(self, item: Any) -> None:
        for queue in self._queues:
            queue.put_nowait(item)

    def _closed_error(self, code: int | None) -> TaviaError:
        return SessionClosedError(code)

    async def _send(self, data: str | bytes) -> None:
        if self._closed.is_set():
            raise self._closed_error(self.close_code)
        try:
            await self._socket.send(data)
        except ConnectionClosed as exc:
            raise self._closed_error(close_code_of(exc)) from exc

    async def _send_json(self, obj: dict) -> None:
        await self._send(json.dumps(obj))
