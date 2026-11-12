"""Serves the page and mints a short-lived token for it. The API key never leaves this server.

Usage: TAVIA_API_KEY=... APP_ORIGIN=https://your-app.example python server.py
APP_ORIGIN is the https origin the page is served from; add it to your organisation's allowed origins first.
"""

import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from tavia import Tavia, TaviaError

PAGE = (Path(__file__).parent / "index.html").read_bytes()


async def mint_token() -> dict:
    async with Tavia(os.environ["TAVIA_API_KEY"]) as tavia:
        token = await tavia.tokens.create("voice", os.environ["APP_ORIGIN"])
        return {"token": token.token, "url": token.url, "expires_at": token.expires_at}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self._reply(200, "text/html", PAGE)

    def do_POST(self) -> None:
        if self.path != "/token":
            self._reply(404, "text/plain", b"not found")
            return
        try:
            self._reply(200, "application/json", json.dumps(asyncio.run(mint_token())).encode())
        except TaviaError as err:
            self._reply(502, "text/plain", str(err).encode())

    def _reply(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("content-type", content_type)
        self.end_headers()
        self.wfile.write(body)


print("listening on :3000")
ThreadingHTTPServer(("", 3000), Handler).serve_forever()
