# tavia

The Python SDK for [Tavia](https://tavialabs.com): realtime voice agents, speech-to-text and text-to-speech. Asyncio,
typed (`py.typed`), Python 3.11 or later. Every endpoint is under `https://api.tavialabs.com/v1`, except the live
speech-to-text socket, which has its own host.

```sh
pip install tavia
```

## Quick start: a voice agent

```python
import asyncio, os
from tavia import Tavia, function_tool


async def main() -> None:
    async with Tavia(os.environ["TAVIA_API_KEY"]) as tavia:
        call = await tavia.realtime.connect(
            session={
                "voice": "elaine",
                "instructions": "You answer calls for a clinic. Be warm and brief.",
                "tools": [function_tool("check_slots", effect="read", description="Free slots on a day")],
            }
        )

        @call.tool("check_slots")
        async def check_slots(args: dict) -> dict:
            return {"day": args.get("day"), "slots": ["10:00", "14:30"]}

        call.on("transcript", lambda t: t["final"] and print(f"{t['role']}: {t['text']}"))
        await call.send_text("Any slots on Friday?")
        await call.wait_closed()


asyncio.run(main())
```

## Browser pages: tokens

A page never holds your API key. Your Python server mints a short-lived token for the page's origin; the page
connects with the TypeScript SDK (`@tavia/sdk`) and that token.

```python
async def mint_token(tavia: Tavia) -> dict:
    token = await tavia.tokens.create("voice", "https://app.example.com")  # origin on your allowed list
    return {"token": token.token, "url": token.url}
```

See [`examples/browser_voice`](examples/browser_voice) for a complete server and page.

## Speech-to-text and text-to-speech

```python
from pathlib import Path

result = await tavia.stt.transcribe("call.wav", terms=["Tavia"])
print(result["text"])

speech = await tavia.tts.render("elaine", "Your table is ready.", "en")
Path("speech.wav").write_bytes(speech.wav)
```

Live streams: `await tavia.stt.stream()` (partials and formatted finals) and `await tavia.tts.stream(voice)` (audio
as it is made). `await tavia.tts.voices()` lists the voices.

## Using a standard API client instead

Tavia also speaks the standard realtime and audio API, so an official client library built for that API works
when you change two settings: the base URL to `https://api.tavialabs.com/v1` and the key to your Tavia key. It
covers `/v1/realtime`, `POST /v1/audio/transcriptions` and `POST /v1/audio/speech`; Tavia's own session options go
under `session.tavia`. Use this SDK for Tavia's own features: friendly events, tool handlers, the tool checker and
live speech-to-text.

## Core concepts

- **Session.** One realtime conversation over a WebSocket. `connect()` sends your session options; `call.update()`
  changes them live. The SDK sends them in the standard shape, with Tavia's own options under `tavia`.
- **Events.** `call.on(name, cb)` takes a friendly name (`transcript`, `turn`, `tool_call`, `timing`, `ended`, ...)
  or a wire event type under its standard name (`response.output_audio.delta`, `conversation.item.added`, ...).
  `async for event in call` yields every event. Callbacks may be sync or async.
- **Tools.** `function_tool(name, effect="read")` or `effect="write"`: a read runs at once; a write runs only after
  the agent reads it back and the caller says yes. `@call.tool(name)` runs your handler and sends its result.
  `check_tools(tools)` reports what a session would refuse, before you connect.
- **Audio.** PCM16 mono bytes at the rates in `LIMITS["realtime.inputRates"]` and `LIMITS["realtime.outputRates"]`
  (`tavia.generated.spec`). `read_wav` and `write_wav` convert files.

## Errors

Every failure is a `TaviaError` with `.code`, `.message` and `.http`, and a subclass per kind:
`AuthenticationError` (401), `PermissionDeniedError` (403), `InsufficientCreditError` (402),
`InvalidRequestError` (400), `RateLimitError` (429), `ServerError` (5xx), `ConnectError` (the server could not be
reached, or a socket closed before it opened) and `SessionClosedError` (a send on a closed session).

```python
from tavia import RateLimitError

try:
    await tavia.tts.render("elaine", text, "en")
except RateLimitError as err:
    print("slow down:", err.message)
```

Rate limits and unavailable answers are retried twice with backoff (`max_retries` changes it); the server's
`Retry-After` is honoured.

## Configuration

```python
Tavia(
    api_key,
    base_url="https://api.tavialabs.com/v1",  # the default
    urls={"realtime": "ws://localhost:8080/v1/realtime"},  # point one endpoint elsewhere, e.g. a test server
    max_retries=2,
)
```

## Examples

[`examples/`](examples): a browser voice page with its token server, transcribing a file, and text-to-speech.

## Links

- Documentation: https://app.tavialabs.com/docs
- TypeScript SDK: `npm install @tavia/sdk`
- License: Apache-2.0
