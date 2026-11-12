import asyncio
import base64
import json
import re

import httpx
import pytest
from conftest import FakeSocket, make_client, until

from tavia import InvalidRequestError, ServerError, SessionClosedError, TtsAudio, TtsDone, TtsRender
from tavia.tts import parse_audio_frame


async def open_stream(session_id=None):
    socket = FakeSocket()
    client, connector, _ = make_client(socket)
    stream = await client.tts.stream("elaine", session_id=session_id)
    return stream, socket, connector


async def test_start_frame():
    stream, socket, connector = await open_stream()
    assert connector.calls[0].url == "wss://api.tavialabs.com/v1/tts/stream"
    start = json.loads(socket.sent[0])
    assert start["type"] == "start" and start["voice"] == "elaine" and start["sample_rate"] == 24000
    assert re.fullmatch(r"[0-9a-f]{32}", start["session_id"])
    with pytest.raises(RuntimeError):
        await stream.open()
    await stream.close()


async def test_client_frames():
    stream, socket, _ = await open_stream(session_id="s1")
    await stream.speak("r1", "Hello.", "en")
    await stream.speak("r1", "Welcome back.", "en", style="warm")
    await stream.close_context("r1")
    await stream.cancel("r2")
    assert socket.events()[1:] == [
        {"type": "speak", "context_id": "r1", "text": "Hello.", "lang": "en"},
        {"type": "speak", "context_id": "r1", "text": "Welcome back.", "lang": "en", "style": "warm"},
        {"type": "close_context", "context_id": "r1"},
        {"type": "cancel", "context_id": "r2"},
    ]
    with pytest.raises(ValueError):
        await stream.speak("not valid!", "x", "en")
    with pytest.raises(ValueError):
        await stream.speak("r3", "x", "en", style="shouty")
    with pytest.raises(ValueError):
        await stream.cancel("a" * 17)
    await stream.close()


def test_binary_header_parse():
    frame = b"r1".ljust(16, b"\0") + b"\x01\x00\x02\x00"
    assert parse_audio_frame(frame) == TtsAudio("r1", b"\x01\x00\x02\x00")
    with pytest.raises(ValueError):
        parse_audio_frame(b"short")


async def test_audio_done_and_errors():
    stream, socket, _ = await open_stream()
    got = {"audio": [], "done": [], "error": []}
    for name, items in got.items():
        stream.on(name, items.append)
    socket.push(b"r1".ljust(16, b"\0") + b"\x10\x00")
    socket.push({"type": "done", "context_id": "r1", "audio_s": 0.5, "first_audio_ms": 180, "stopped": None})
    socket.push({"type": "done", "context_id": "r2", "audio_s": 0.1, "first_audio_ms": 90, "stopped": "cancelled"})
    socket.push({"type": "error", "code": "unsupported_language", "message": "no", "context_id": "r3"})
    await until(lambda: got["error"])
    assert got["audio"] == [TtsAudio("r1", b"\x10\x00")]
    assert got["done"] == [TtsDone("r1", 0.5, 180, None), TtsDone("r2", 0.1, 90, "cancelled")]
    err = got["error"][0]
    assert isinstance(err, InvalidRequestError)
    assert (err.code, err.context_id) == ("unsupported_language", "r3")
    await stream.speak("r4", "Still here.", "en")  # a context error leaves the session open
    await stream.close()


async def test_end_after_an_error_close_raises_session_closed_with_the_code():
    stream, socket, _ = await open_stream()
    socket.push({"type": "error", "code": "engine", "message": "failed"})
    socket.push_close(4500)
    with pytest.raises(SessionClosedError) as raised:
        await stream.end()
    assert raised.value.close_code == stream.close_code == 4500
    assert isinstance(raised.value.__cause__, ServerError)


async def test_end_after_a_fatal_error_then_a_normal_close_still_raises():
    stream, socket, _ = await open_stream()
    socket.push({"type": "error", "code": "engine", "message": "failed"})
    socket.push_close(1000)
    with pytest.raises(SessionClosedError) as raised:
        await stream.end()
    assert raised.value.close_code == 1000


async def test_end_after_a_clean_close():
    stream, socket, _ = await open_stream()
    socket.push_close(1000)
    await stream.end()
    assert socket.events()[-1] == {"type": "end"}


async def test_end_sends_end_then_waits():
    stream, socket, _ = await open_stream()
    iterator = aiter(stream)

    async def finish():
        await until(lambda: socket.types()[-1:] == ["end"])
        socket.push_close(1000)

    closer = asyncio.create_task(finish())
    await stream.end()
    await closer
    assert [item async for item in iterator] == []
    assert stream.close_code == 1000


async def test_render_and_voices():
    wav = b"RIFF....WAVE"

    def answer(request):
        if request.url.path == "/v1/tts/render":
            return httpx.Response(
                200,
                json={
                    "sample_rate": 24000,
                    "audio_s": 1.2,
                    "wav_base64": base64.b64encode(wav).decode(),
                    "sentences": [{"audio_s": 1.2, "scores": {}}],
                },
            )
        return httpx.Response(
            200, json={"voices": [{"id": "elaine"}], "default": "elaine", "by_language": {"en": "elaine"}}
        )

    client, _, recorder = make_client(answer=answer)
    render = await client.tts.render("elaine", "Hello.", "en", style="warm")
    assert render == TtsRender(sample_rate=24000, audio_s=1.2, wav=wav, sentences=[{"audio_s": 1.2, "scores": {}}])
    post = recorder.requests[0]
    assert post.method == "POST" and str(post.url) == "https://api.tavialabs.com/v1/tts/render"
    assert json.loads(post.content) == {"voice": "elaine", "text": "Hello.", "lang": "en", "style": "warm"}
    voices = await client.tts.voices()
    assert voices["default"] == "elaine"
    assert str(recorder.requests[1].url) == "https://api.tavialabs.com/v1/voices"
    with pytest.raises(ValueError):
        await client.tts.render("elaine", "x" * 501, "en")


async def test_render_error_is_typed():
    client, _, _ = make_client(
        answer=lambda r: httpx.Response(
            400, json={"error": {"code": "unsupported_language", "message": "This voice does not speak that language."}}
        )
    )
    with pytest.raises(InvalidRequestError) as caught:
        await client.tts.render("kai", "Selamat pagi.", "ms")
    assert caught.value.code == "unsupported_language"
