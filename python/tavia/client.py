"""The top-level client: one object per set of credentials, a namespace per product."""

from types import TracebackType

import httpx

from tavia._transport import DEFAULT_MAX_RETRIES, Auth, Context, WsConnect, build_urls
from tavia.realtime import Realtime
from tavia.stt import Stt
from tavia.tokens import Tokens
from tavia.tts import Tts

__all__ = ["Tavia"]


class Tavia:
    """The Tavia client: realtime voice sessions, speech-to-text, text-to-speech and browser tokens.

    Use Tavia(api_key) on your server, or Tavia(token=...) with a short-lived token your server got from
    tokens.create. Use it as an async context manager, or call aclose() when done.

    Args:
        api_key: Your API key; servers only.
        token: A short-lived token instead of an API key.
        base_url: Serves every endpoint under one URL, e.g. "https://api.tavialabs.com/v1" (the live
            speech-to-text socket keeps its host).
        urls: Overrides single endpoints, e.g. {"realtime": "ws://localhost:8080/v1/realtime"}: each value is a full
            URL used as given; keys are realtime, stt_live, stt_files, tts_stream, tts_render, voices, tokens.
        ws_connect: Opens WebSockets; defaults to the websockets package.
        http: An httpx.AsyncClient to use; one you pass stays yours to close.
        max_retries: Extra attempts after a rate limit, an unavailable server or a network failure (default 2).

    Raises:
        ValueError: not exactly one of api_key and token, or an unknown key in urls.

    Attributes:
        realtime: Realtime voice sessions.
        stt: Speech-to-text: live streams and recorded files.
        tts: Text-to-speech: live streams, one-shot renders and the voice list.
        tokens: Short-lived browser tokens.

    Example:
        async with Tavia(os.environ["TAVIA_API_KEY"]) as tavia:
            call = await tavia.realtime.connect(session={"voice": "elaine", "instructions": "Be brief."})
            call.on("transcript", lambda t: show_line(t["role"], t["text"]))
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        token: str | None = None,
        base_url: str | None = None,
        urls: dict[str, str] | None = None,
        ws_connect: WsConnect | None = None,
        http: httpx.AsyncClient | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        if bool(api_key) == bool(token):
            raise ValueError("pass exactly one of api_key or token")
        urls = build_urls(urls, base_url)
        self._ctx = Context(Auth(api_key=api_key, token=token), urls, ws_connect, http, max_retries)
        self.realtime = Realtime(self._ctx)
        self.stt = Stt(self._ctx)
        self.tts = Tts(self._ctx)
        self.tokens = Tokens(self._ctx)

    async def aclose(self) -> None:
        """Closes the HTTP client the SDK made (one passed in as http stays yours)."""
        await self._ctx.aclose()

    async def __aenter__(self) -> "Tavia":
        """Returns the client; leaving the block calls aclose()."""
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        await self.aclose()
