"""Small fakes: a scripted socket, a recording socket factory and an httpx mock client."""

import asyncio
import json
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

import httpx
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from websockets.frames import Close

from tavia import Tavia

KEY = "tk_test_key"


def closed_exc(code: int) -> Exception:
    cls = ConnectionClosedOK if code in (1000, 1001) else ConnectionClosedError
    return cls(Close(code, ""), None)


class _Closing:
    def __init__(self, code: int):
        self.code = code


class FakeSocket:
    """Server frames are pushed in; frames the SDK sends are recorded in `sent`."""

    def __init__(self, *frames: dict | str | bytes):
        self.sent: list[str | bytes] = []
        self._inbox: asyncio.Queue = asyncio.Queue()
        self.closed = False
        for frame in frames:
            self.push(frame)

    def push(self, frame: dict | str | bytes) -> None:
        self._inbox.put_nowait(json.dumps(frame) if isinstance(frame, dict) else frame)

    def push_close(self, code: int = 1000) -> None:
        self._inbox.put_nowait(_Closing(code))

    async def recv(self) -> str | bytes:
        item = await self._inbox.get()
        if isinstance(item, _Closing):
            self.closed = True
            raise closed_exc(item.code)
        return item

    async def send(self, data: str | bytes) -> None:
        if self.closed:
            raise closed_exc(1000)
        self.sent.append(data)

    async def close(self) -> None:
        if not self.closed:
            self.closed = True
            self.push_close(1000)

    def events(self) -> list[dict]:
        """Every JSON text frame sent, parsed."""
        return [json.loads(f) for f in self.sent if isinstance(f, str) and f]

    def types(self) -> list[str]:
        return [e.get("type") for e in self.events()]


class Connector:
    """A ws_connect that records each handshake and hands out the given sockets in order."""

    def __init__(self, *sockets: FakeSocket):
        self.sockets = list(sockets)
        self.calls: list[SimpleNamespace] = []

    async def __call__(self, url: str, subprotocols: list[str], headers: dict[str, str]) -> FakeSocket:
        self.calls.append(SimpleNamespace(url=url, subprotocols=list(subprotocols), headers=dict(headers)))
        return self.sockets.pop(0)


Handler = Callable[[httpx.Request], httpx.Response]


class Recorder:
    """An httpx MockTransport handler that records requests and answers from a function."""

    def __init__(self, answer: Handler):
        self.answer = answer
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self.answer(request)


def make_client(
    *sockets: FakeSocket, answer: Handler | None = None, token: str | None = None, **kwargs: Any
) -> tuple[Tavia, Connector, Recorder]:
    connector = Connector(*sockets)
    recorder = Recorder(answer or (lambda request: httpx.Response(404, json={"error": "not_found"})))
    http = httpx.AsyncClient(transport=httpx.MockTransport(recorder))
    client = Tavia(None if token else KEY, token=token, ws_connect=connector, http=http, **kwargs)
    return client, connector, recorder


async def until(predicate: Callable[[], bool], tries: int = 500) -> None:
    """Lets the reader and tool tasks run until predicate holds."""
    for _ in range(tries):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("condition not met")
