"""Short-lived browser tokens, minted on your server with an API key."""

import re
from dataclasses import dataclass, field
from typing import Any

from tavia._transport import Context, request
from tavia.generated.spec import LAYERS

__all__ = ["BrowserToken", "Tokens"]

PRODUCTS = tuple(LAYERS)
ORIGIN = re.compile(r"https://[a-z0-9.-]+(:[0-9]+)?")  # a bare, lower-case https origin
HTTPS = "https://"


@dataclass(frozen=True)
class BrowserToken:
    """A short-lived token for one browser page, as returned by tokens.create.

    Attributes:
        token: The token itself; the page passes it as Tavia(token=...) or in its WebSocket subprotocols.
        url: The endpoint the token is for.
        subprotocols: The exact list for new WebSocket(url, subprotocols).
        expires_at: When the token stops working, as an ISO 8601 timestamp.
        session: A bound session's string: pass it unchanged to realtime.connect(bound_session=...).
    """

    token: str
    url: str
    subprotocols: list[str] = field(default_factory=list)
    expires_at: str = ""
    session: str | None = None


class Tokens:
    """Short-lived browser tokens, as tavia.tokens; minting one needs an API key."""

    def __init__(self, ctx: Context):
        self._ctx = ctx

    async def create(self, product: str, origin: str, session: dict[str, Any] | None = None) -> BrowserToken:
        """Mints a token a page on `origin` (one of your organisation's allowed origins) uses for one product.

        Args:
            product: "voice", "stt" or "tts".
            origin: The page's bare https origin, such as "https://app.example.com".
            session: For a voice token, session fields to bind (instructions, tools, voice, ...): the page
                cannot change those fields.

        Raises:
            ValueError: the client has no API key, or product, origin or the tokens URL is not valid.
            TypeError: session is not a dict.
            TaviaError: the API refused the request.

        Example:
            async with Tavia(os.environ["TAVIA_API_KEY"]) as tavia:
                minted = await tavia.tokens.create("voice", "https://app.example.com")
                # send minted.token to the page
        """
        if not self._ctx.auth.api_key:
            raise ValueError("tokens.create needs an API key; a token cannot mint tokens")
        if product not in PRODUCTS:
            raise ValueError(f"product must be one of {', '.join(PRODUCTS)}")
        if not ORIGIN.fullmatch(origin):
            raise ValueError("origin must be a bare https origin, such as https://app.example.com")
        url = self._ctx.urls["tokens"]
        if not url.startswith(HTTPS):
            raise ValueError("the tokens url must be https: the API key never goes out in clear text")
        if session is not None and not isinstance(session, dict):
            raise TypeError("session must be a dict of session fields")
        payload = {"product": product, "origin": origin, **({"session": session} if session is not None else {})}
        body = await request(self._ctx, "POST", url, json=payload)
        return BrowserToken(
            token=body["token"],
            url=body["url"],
            subprotocols=list(body.get("subprotocols") or []),
            expires_at=body.get("expires_at", ""),
            session=body.get("session"),
        )
