import asyncio
import json

import httpx
import pytest
from conftest import FakeSocket, make_client, until

from tavia import InvalidRequestError, RateLimitError, SttFinal, SttFinished, SttPartial, TaviaError

PARTIAL = {
    "tokens": [
        {"text": "my", "start_ms": 120, "end_ms": 400, "is_final": False},
        {"text": " name", "start_ms": 400, "end_ms": 760, "is_final": False},
    ],
    "total_audio_proc_ms": 5240,
}
FINAL = {
    "tokens": [
        {"text": "my", "start_ms": 120, "end_ms": 400, "is_final": True},
        {"text": " name", "start_ms": 400, "end_ms": 760, "is_final": True},
        {"text": "<fin>", "is_final": True},
    ],
    "total_audio_proc_ms": 6900,
    "nbest": [],
    "decoder": "general",
    "empty": False,
    "formatted": "My name",
}
SPELL = {
    "tokens": [{"text": "S", "is_final": True}, {"text": "<fin>", "is_final": True}],
    "total_audio_proc_ms": 1,
    "nbest": [["S", -0.1], ["F", -1.2]],
    "decoder": "spell",
    "empty": False,
}
EMPTY = {
    "tokens": [{"text": "<fin>", "is_final": True}],
    "total_audio_proc_ms": 2,
    "nbest": [],
    "decoder": "general",
    "empty": True,
    "formatted": "",
}


async def open_stream(**config):
    socket = FakeSocket()
    client, connector, _ = make_client(socket)
    stream = await client.stt.stream(**config)
    return stream, socket, connector


async def test_config_defaults_and_terms():
    stream, socket, connector = await open_stream(terms=["Tavia", "Tan Tock Seng"], client_reference_id="call-1")
    assert connector.calls[0].url == "wss://stt.tavialabs.com/transcribe-websocket"
    assert json.loads(socket.sent[0]) == {
        "audio_format": "pcm_s16le",
        "sample_rate": 16000,
        "context": {"terms": ["Tavia", "Tan Tock Seng"]},
        "client_reference_id": "call-1",
    }
    await stream.close()


async def test_config_passes_every_field():
    stream, socket, _ = await open_stream(
        num_channels=1, decoder="spell", nbest=3, format=False, context={"terms": ["A"]}
    )
    assert json.loads(socket.sent[0]) == {
        "audio_format": "pcm_s16le",
        "sample_rate": 16000,
        "num_channels": 1,
        "decoder": "spell",
        "context": {"terms": ["A"]},
        "nbest": 3,
        "format": False,
    }
    await stream.close()


async def test_config_refuses_unknown_fields_and_decoders():
    client, _, _ = make_client(FakeSocket())
    with pytest.raises(TypeError):
        await client.stt.stream(enable_endpoint_detection=True)
    with pytest.raises(ValueError):
        await client.stt.stream(decoder="fast")


async def test_set_terms_sends_a_set_context_frame():
    stream, socket, _ = await open_stream()
    await stream.set_terms(["Dr Ong", "Raffles"])
    await stream.set_terms([])
    assert [json.loads(f) for f in socket.sent[1:]] == [
        {"type": "set_context", "context": {"terms": ["Dr Ong", "Raffles"]}},
        {"type": "set_context", "context": {"terms": []}},
    ]
    await stream.close()


async def test_set_terms_refuses_over_the_limits_before_sending():
    stream, socket, _ = await open_stream()
    with pytest.raises(ValueError, match=r"context\.terms must hold at most 120 terms"):
        await stream.set_terms([f"t{i}" for i in range(121)])
    with pytest.raises(ValueError, match=r"context\.terms must be at most 16384 bytes"):
        await stream.set_terms(["é" * 4096, "x" * 8192])
    assert len(socket.sent) == 1
    await stream.close()


async def test_control_messages():
    stream, socket, _ = await open_stream()
    await stream.send_audio(b"\x01\x02\x03")
    await stream.finalize()
    await stream.set_decoder("spell")
    await stream.keepalive()
    with pytest.raises(ValueError):
        await stream.set_decoder("loud")
    assert socket.sent[1] == b"\x01\x02\x03"
    assert [json.loads(f) for f in socket.sent[2:]] == [
        {"type": "finalize"},
        {"type": "set_decoder", "decoder": "spell"},
        {"type": "keepalive"},
    ]
    await stream.close()


async def test_partials_and_finals_are_parsed():
    stream, socket, _ = await open_stream()
    got = {"partial": [], "final": []}
    stream.on("partial", got["partial"].append)
    stream.on("final", got["final"].append)
    for msg in (PARTIAL, FINAL, SPELL, EMPTY):
        socket.push(msg)
    await until(lambda: len(got["final"]) == 3)
    assert got["partial"] == [SttPartial(tokens=PARTIAL["tokens"], text="my name")]
    final, spell, empty = got["final"]
    assert isinstance(final, SttFinal)
    assert (final.text, final.formatted, final.empty, final.decoder, final.total_audio_proc_ms) == (
        "my name",
        "My name",
        False,
        "general",
        6900,
    )
    assert final.tokens[-1]["text"] == "<fin>"
    assert (spell.text, spell.formatted, spell.decoder, spell.nbest) == ("S", None, "spell", [["S", -0.1], ["F", -1.2]])
    assert (empty.text, empty.empty, empty.formatted) == ("", True, "")
    await stream.close()


async def test_end_waits_for_finished():
    stream, socket, _ = await open_stream()
    items = []
    iterator = aiter(stream)  # subscribes now, before the reader runs

    async def collect():
        async for item in iterator:
            items.append(item)

    reader = asyncio.create_task(collect())
    socket.push(FINAL)
    socket.push({"finished": True})
    await stream.end()
    assert socket.sent[-1] == ""
    socket.push_close(1000)
    await reader
    assert [type(i) for i in items] == [SttFinal, SttFinished]


async def test_error_message_is_a_typed_error():
    stream, socket, _ = await open_stream()
    errors = []
    stream.on("error", errors.append)
    socket.push({"error_code": 400, "error_message": "bad config"})
    socket.push_close(4400)
    with pytest.raises(InvalidRequestError):
        await stream.end()
    assert errors[0].http == 400 and errors[0].code is None and errors[0].message == "bad config"
    assert stream.close_code == 4400


JOB = "a" * 32
RESULT = {"text": "hello", "duration_s": 1.0, "decoder": "general", "segments": []}


class Jobs:
    """A files server: POST makes a job, GETs walk `statuses`, DELETE answers 204."""

    def __init__(self, *statuses):
        self.statuses = list(statuses)

    def __call__(self, request):
        if request.method == "POST":
            return httpx.Response(202, json={"job_id": JOB})
        if request.method == "GET":
            return httpx.Response(200, json=self.statuses.pop(0))
        return httpx.Response(204)


async def test_transcribe_uploads_polls_and_deletes(tmp_path):
    path = tmp_path / "call.wav"
    path.write_bytes(b"RIFFdata")
    client, _, recorder = make_client(
        answer=Jobs({"status": "queued", "progress": 0}, {"status": "done", "progress": 1, "result": RESULT})
    )
    assert await client.stt.transcribe(path, terms=["Tavia", "Paxlovid"], poll_s=0) == RESULT
    post, *gets, delete = recorder.requests
    assert post.url == "https://api.tavialabs.com/v1/transcriptions"
    body = post.content
    assert b'name="file"; filename="call.wav"' in body and b"RIFFdata" in body
    assert b'name="terms"' in body and b"Tavia\nPaxlovid" in body
    assert [str(g.url) for g in gets] == [f"https://api.tavialabs.com/v1/transcriptions/{JOB}"] * 2
    assert delete.method == "DELETE" and str(delete.url).endswith(JOB)
    assert post.headers["Authorization"].startswith("Bearer ")


async def test_failed_job_raises_and_is_still_deleted():
    client, _, recorder = make_client(answer=Jobs({"status": "failed", "progress": 0.2, "error": "bad_audio"}))
    with pytest.raises(InvalidRequestError) as caught:
        await client.stt.transcribe(b"not audio", poll_s=0)
    assert caught.value.code == "bad_audio"
    assert recorder.requests[-1].method == "DELETE"


async def test_keep_leaves_the_job():
    client, _, recorder = make_client(answer=Jobs({"status": "done", "progress": 1, "result": RESULT}))
    await client.stt.transcribe(b"audio", keep=True, poll_s=0)
    assert [r.method for r in recorder.requests] == ["POST", "GET"]


async def test_job_calls_and_http_errors():
    client, _, _ = make_client(answer=lambda r: httpx.Response(429, json={"error": "active_job"}))
    with pytest.raises(RateLimitError) as caught:
        await client.stt.create_job(b"audio")
    assert caught.value.code == "active_job"
    client, _, _ = make_client(answer=Jobs({"status": "running", "progress": None}))
    assert await client.stt.get_job(JOB) == {"status": "running", "progress": None}
    assert await client.stt.delete_job(JOB) is None
    with pytest.raises(TypeError):
        await client.stt.create_job(12345)
    assert isinstance(caught.value, TaviaError)


FILLERS = [{"type": "uh", "start_ms": 400, "end_ms": 900, "is_final": True, "before": 1}]


async def test_include_fillers_is_sent_and_finals_and_partials_carry_the_fillers():
    stream, socket, _ = await open_stream(include_fillers=True)
    assert json.loads(socket.sent[0]) == {"audio_format": "pcm_s16le", "sample_rate": 16000, "include_fillers": True}
    got = {"partial": [], "final": []}
    stream.on("partial", got["partial"].append)
    stream.on("final", got["final"].append)
    socket.push({**PARTIAL, "fillers": [{**FILLERS[0], "is_final": False}]})
    socket.push({**FINAL, "fillers": FILLERS})
    socket.push(EMPTY)
    await until(lambda: len(got["final"]) == 2)
    assert got["partial"][0].fillers == [{**FILLERS[0], "is_final": False}]
    assert got["final"][0].fillers == FILLERS and got["final"][1].fillers == []
    await stream.close()
