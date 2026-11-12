"""The standard dialect on the wire: what connect asks for, the session shape, and old event names."""

import pytest
from conftest import FakeSocket, make_client, until

from tavia import Call

BOUND = '{"instructions":"You are the front desk."}'


def audio(kind: str, **extra) -> dict:
    return {
        "type": kind,
        "event_id": "e",
        "response_id": "r",
        "item_id": "a1",
        "output_index": 0,
        "content_index": 0,
        "delta": "AAAA",
        **extra,
    }


class Player:
    def __init__(self):
        self.chunks = []

    def enqueue(self, pcm):
        self.chunks.append(pcm)

    def flush(self):
        pass


async def connect(socket: FakeSocket, **kwargs) -> tuple[Call, object]:
    client, connector, _ = make_client(socket, token="t")
    return await client.realtime.connect(**kwargs), connector


async def test_connect_asks_for_the_standard_dialect_and_turns_tavia_events_on():
    socket = FakeSocket()
    call, connector = await connect(socket, preset="clinic")
    assert connector.calls[0].url == "wss://api.tavialabs.com/v1/realtime?dialect=ga&preset=clinic"
    assert socket.events() == [{"type": "session.update", "session": {"type": "realtime", "tavia": {"events": True}}}]
    await call.close()


async def test_a_bound_session_goes_first_unchanged_then_the_session():
    socket = FakeSocket()
    call, _ = await connect(socket, bound_session=BOUND, session={"languages": ["en"]})
    assert socket.events() == [
        {"type": "session.update", "session": {"type": "realtime", "tavia": {"bound": BOUND, "events": True}}},
        {"type": "session.update", "session": {"type": "realtime", "tavia": {"languages": ["en"]}}},
    ]
    await call.close()


async def test_update_nests_audio_fields_and_puts_tavia_options_under_tavia():
    socket = FakeSocket()
    call, _ = await connect(socket)
    await call.update(
        {
            "instructions": "Be brief.",
            "voice": "marcus",
            "turn_detection": None,
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "knowledge": {"mode": "rag", "kb_id": "kb1"},
        }
    )
    assert socket.events()[-1] == {
        "type": "session.update",
        "session": {
            "type": "realtime",
            "instructions": "Be brief.",
            "audio": {
                "input": {"turn_detection": None, "format": "pcm16"},
                "output": {"voice": "marcus", "format": "pcm16"},
            },
            "tavia": {"knowledge": {"mode": "rag", "kb_id": "kb1"}},
        },
    }
    await call.close()


async def test_standard_audio_plays_and_its_transcript_is_a_friendly_event():
    player = Player()
    socket = FakeSocket(
        audio("response.output_audio.delta"), audio("response.output_audio_transcript.done", transcript="Hello.")
    )
    said = []
    call, _ = await connect(socket, player=player)
    call.on("transcript", lambda t: said.append((t["role"], t["text"], t["final"])))
    await until(lambda: said)
    assert said == [("agent", "Hello.", True)] and len(player.chunks) == 1
    await call.close()


async def test_beta_names_from_the_server_are_read_as_their_standard_names():
    player = Player()
    socket = FakeSocket()
    seen = []
    call, _ = await connect(socket, player=player)
    call.on("response.output_audio.delta", lambda e: seen.append(e["type"]))
    socket.push(audio("response.audio.delta"))
    await until(lambda: seen)
    assert seen == ["response.output_audio.delta"] and len(player.chunks) == 1
    await call.close()


async def test_a_deprecated_event_name_still_subscribes_to_its_renamed_event():
    socket = FakeSocket()
    seen = []
    call, _ = await connect(socket)
    with pytest.warns(DeprecationWarning):
        call.on("response.audio.delta", lambda e: seen.append(e["type"]))
    socket.push(audio("response.output_audio.delta"))
    await until(lambda: seen)
    assert seen == ["response.output_audio.delta"]
    await call.close()


async def test_the_beta_dialect_is_an_explicit_opt_in_that_keeps_the_flat_session():
    socket = FakeSocket()
    with pytest.warns(DeprecationWarning):
        call, connector = await connect(socket, dialect="beta", session={"voice": "ren"})
    assert connector.calls[0].url == "wss://api.tavialabs.com/v1/realtime?dialect=beta"
    assert socket.events() == [{"type": "session.update", "session": {"voice": "ren"}}]
    await call.close()
