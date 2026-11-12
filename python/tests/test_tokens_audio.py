import copy
import io
import json

import httpx
import pytest
from conftest import KEY, make_client

from tavia import (
    TOOL_TEMPLATES,
    BrowserToken,
    base64_to_pcm16,
    pcm16_to_base64,
    read_wav,
    template_tool,
    write_wav,
)

ORIGIN = "https://app.example.com"
REPLY = {
    "token": "t.1",
    "url": "wss://api.tavialabs.com/v1/realtime",
    "subprotocols": ["tavia-voice", "tavia-token.t.1"],
    "expires_at": "2026-10-30T10:00:00Z",
}


def token_answer(request):
    return httpx.Response(200, json=REPLY)


async def test_tokens_create_posts_product_and_origin_with_the_key():
    client, _, recorder = make_client(answer=token_answer)
    token = await client.tokens.create("voice", ORIGIN)
    assert token == BrowserToken(**REPLY)
    request = recorder.requests[0]
    assert str(request.url) == "https://api.tavialabs.com/v1/tokens"
    assert request.headers["Authorization"] == f"Bearer {KEY}"
    assert json.loads(request.content) == {"product": "voice", "origin": ORIGIN}


async def test_a_voice_token_may_bind_a_session_and_returns_its_string():
    bound = '{"instructions":"You are the front desk."}'
    client, _, recorder = make_client(answer=lambda r: httpx.Response(200, json={**REPLY, "session": bound}))
    token = await client.tokens.create("voice", ORIGIN, {"instructions": "You are the front desk."})
    assert token.session == bound
    assert json.loads(recorder.requests[0].content) == {
        "product": "voice",
        "origin": ORIGIN,
        "session": {"instructions": "You are the front desk."},
    }
    with pytest.raises(TypeError):
        await client.tokens.create("voice", ORIGIN, bound)


async def test_tokens_need_a_key_a_product_a_bare_https_origin_and_https():
    client, _, _ = make_client(answer=token_answer, token="t.0")
    with pytest.raises(ValueError, match="API key"):
        await client.tokens.create("voice", ORIGIN)
    client, _, _ = make_client(answer=token_answer)
    with pytest.raises(ValueError, match="product"):
        await client.tokens.create("billing", ORIGIN)
    with pytest.raises(ValueError, match="origin"):
        await client.tokens.create("voice", "https://app.example.com/page")
    client, _, _ = make_client(answer=token_answer, urls={"tokens": "http://localhost:9000/v1/tokens"})
    with pytest.raises(ValueError, match="https"):
        await client.tokens.create("voice", ORIGIN)


def test_pcm_base64_round_trip():
    pcm = b"\x01\x00\xff\x7f"
    assert base64_to_pcm16(pcm16_to_base64(pcm)) == pcm


def test_wav_round_trip(tmp_path):
    path = tmp_path / "a.wav"
    write_wav(path, b"\x01\x00\x02\x00", 16000)
    assert read_wav(path) == (b"\x01\x00\x02\x00", 16000)
    buffer = io.BytesIO()
    write_wav(buffer, b"\x00\x00", 24000)
    buffer.seek(0)
    assert read_wav(buffer) == (b"\x00\x00", 24000)


def test_read_wav_refuses_stereo(tmp_path):
    import wave

    path = tmp_path / "stereo.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\0" * 8)
    with pytest.raises(ValueError):
        read_wav(path)


def test_template_tool_is_a_copy():
    first = TOOL_TEMPLATES[0]
    before = copy.deepcopy(first["tool"])
    tool = template_tool(first["id"])
    assert tool == before
    tool["name"] = "changed"
    assert first["tool"] == before
    with pytest.raises(ValueError):
        template_tool("no_such_template")
