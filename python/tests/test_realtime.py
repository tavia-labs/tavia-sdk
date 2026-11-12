import asyncio
import base64
import json

import pytest
from conftest import FakeSocket, make_client, until

from tavia import AuthenticationError, InsufficientCreditError, InvalidRequestError, SessionClosedError, ToolError
from tavia.generated.spec import LIMITS


async def connect(*frames, **kwargs):
    socket = FakeSocket(*frames)
    client, connector, _ = make_client(socket)
    call = await client.realtime.connect(**kwargs)
    return call, socket, connector


OPENING = {"type": "session.update", "session": {"type": "realtime", "tavia": {"events": True}}}


def after_open(socket):
    """The events sent after connect's opening update, which turns Tavia's events on."""
    events = socket.events()
    assert events[0] == OPENING
    return events[1:]


def audio_delta(item_id, n_bytes):
    return {
        "type": "response.output_audio.delta",
        "event_id": "e",
        "response_id": "r",
        "item_id": item_id,
        "output_index": 0,
        "content_index": 0,
        "delta": base64.b64encode(b"\0" * n_bytes).decode(),
    }


class FakePlayer:
    def __init__(self):
        self.chunks, self.flushes, self.played = [], 0, 0.0

    def enqueue(self, pcm):
        self.chunks.append(pcm)

    def flush(self):
        self.flushes += 1

    def played_ms(self):
        return self.played


async def test_session_is_sent_right_after_open():
    call, socket, _ = await connect(session={"voice": "elaine", "instructions": "Be brief."})
    assert socket.events() == [
        {
            "type": "session.update",
            "session": {
                "type": "realtime",
                "instructions": "Be brief.",
                "audio": {"output": {"voice": "elaine"}},
                "tavia": {"events": True},
            },
        }
    ]
    await call.close()


async def test_a_bound_session_is_sent_first_unchanged_then_the_session():
    bound = '{"instructions":"You are the front desk."}'
    call, socket, _ = await connect(bound_session=bound, session={"languages": ["en"]})
    assert socket.events() == [
        {"type": "session.update", "session": {"type": "realtime", "tavia": {"bound": bound, "events": True}}},
        {"type": "session.update", "session": {"type": "realtime", "tavia": {"languages": ["en"]}}},
    ]
    await call.close()
    with pytest.raises(TypeError):
        await connect(bound_session={"instructions": "x"})


async def test_preset_is_a_query_parameter():
    call, _, connector = await connect(preset="clinic front")
    assert connector.calls[0].url == "wss://api.tavialabs.com/v1/realtime?dialect=ga&preset=clinic+front"
    await call.close()


async def test_unknown_session_option_is_refused():
    with pytest.raises(ValueError):
        await connect(session={"voice": "elaine", "model": "x"})
    call, socket, _ = await connect()
    with pytest.raises(ValueError):
        await call.update({"temperature": 0.2})
    assert after_open(socket) == []
    await call.close()


async def test_send_audio_splits_into_capped_even_chunks():
    call, socket, _ = await connect()
    cap = LIMITS["realtime.maxAudioBytes"]
    pcm = bytes(range(256)) * ((cap * 2 + 1000) // 256)
    await call.send_audio(pcm)
    chunks = [base64.b64decode(e["audio"]) for e in after_open(socket)]
    assert all(e["type"] == "input_audio_buffer.append" for e in after_open(socket))
    assert b"".join(chunks) == pcm
    assert all(len(c) <= cap and len(c) % 2 == 0 for c in chunks)
    assert len(chunks) == 3
    with pytest.raises(ValueError):
        await call.send_audio(b"\0\0\0")
    await call.close()


async def test_client_event_wire_shapes():
    call, socket, _ = await connect()
    await call.send_text("Any slots Friday?")
    await call.send_text("The caller is a member.", role="system")
    await call.send_tool_output("call_1", {"slots": ["10:00"]})
    await call.send_tool_output("call_2", "plain")
    await call.truncate("item_9", 1520.7)
    await call.create_response()
    await call.cancel_response()
    await call.commit_audio()
    await call.clear_audio()
    assert after_open(socket) == [
        {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "Any slots Friday?"}],
            },
        },
        {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "system",
                "content": [{"type": "input_text", "text": "The caller is a member."}],
            },
        },
        {
            "type": "conversation.item.create",
            "item": {"type": "function_call_output", "call_id": "call_1", "output": '{"slots": ["10:00"]}'},
        },
        {
            "type": "conversation.item.create",
            "item": {"type": "function_call_output", "call_id": "call_2", "output": "plain"},
        },
        {"type": "conversation.item.truncate", "item_id": "item_9", "content_index": 0, "audio_end_ms": 1520},
        {"type": "response.create"},
        {"type": "response.cancel"},
        {"type": "input_audio_buffer.commit"},
        {"type": "input_audio_buffer.clear"},
    ]
    with pytest.raises(ValueError):
        await call.send_text("hi", role="assistant")
    await call.close()


def tool_call(name, arguments, call_id="call_k2m8"):
    return {
        "type": "response.function_call_arguments.done",
        "event_id": "e",
        "response_id": "r",
        "output_index": 1,
        "item_id": "item_9",
        "call_id": call_id,
        "name": name,
        "arguments": arguments,
    }


def outputs(socket):
    return [e["item"] for e in socket.events() if e.get("item", {}).get("type") == "function_call_output"]


async def test_tool_handler_round_trip():
    call, socket, _ = await connect()
    seen = []
    call.tool("check_slots", lambda args: seen.append(args) or {"slots": ["10:00"]})
    socket.push(tool_call("check_slots", '{"doctor": "Dr Tan"}'))
    await until(lambda: outputs(socket))
    assert seen == [{"doctor": "Dr Tan"}]
    output = {"type": "function_call_output", "call_id": "call_k2m8", "output": '{"slots": ["10:00"]}'}
    assert outputs(socket) == [output]
    assert "response.create" not in socket.types()  # the server continues by itself
    await call.close()


async def test_async_tool_handler_as_decorator():
    call, socket, _ = await connect()

    @call.tool("lookup")
    async def lookup(args):
        await asyncio.sleep(0)
        return f"found {args['id']}"

    socket.push(tool_call("lookup", '{"id": "B7"}'))
    await until(lambda: outputs(socket))
    assert outputs(socket)[0]["output"] == "found B7"
    assert callable(lookup)
    await call.close()


async def test_raising_tool_handler_sends_an_error_output():
    call, socket, _ = await connect()

    def broken(args):
        raise RuntimeError("calendar offline")

    call.tool("book", broken)
    socket.push(tool_call("book", "{}"))
    await until(lambda: outputs(socket))
    assert json.loads(outputs(socket)[0]["output"]) == {"error": "tool_failed"}
    await call.close()


async def test_tool_error_message_is_passed_through_and_raw_errors_only_on_opt_in(caplog):
    call, socket, _ = await connect()

    def no_slot(args):
        raise ToolError("That day is fully booked.")

    def broken(args):
        raise RuntimeError("db at 10.0.0.5 refused")

    call.tool("book", no_slot)
    call.tool("debug", broken, expose_errors=True)
    call.tool("quiet", broken)
    socket.push(tool_call("book", "{}"))
    socket.push(tool_call("debug", "{}"))
    socket.push(tool_call("quiet", "{}"))
    await until(lambda: len(outputs(socket)) == 3)
    got = sorted(json.loads(o["output"])["error"] for o in outputs(socket))
    assert got == ["That day is fully booked.", "db at 10.0.0.5 refused", "tool_failed"]
    assert "db at 10.0.0.5 refused" in caplog.text
    await call.close()


async def test_unregistered_tool_is_left_alone():
    call, socket, _ = await connect()
    off = call.tool("book", lambda args: "ok")
    off()
    socket.push(tool_call("book", "{}"))
    socket.push({"type": "turn.backchannel", "event_id": "e", "turn_id": "t", "transcript": "mm", "at_ms": 1})
    got = []
    call.on("backchannel", got.append)
    await until(lambda: got)
    assert outputs(socket) == []
    with pytest.raises(ValueError):
        call.tool("bad name!", lambda args: None)
    await call.close()


async def test_interrupt_cancels_flushes_and_truncates_at_what_was_heard():
    player = FakePlayer()
    call, socket, _ = await connect(player=player)
    socket.push(audio_delta("item_1", 9600))  # 200 ms at 24 kHz
    socket.push(audio_delta("item_2", 4800))
    socket.push(audio_delta("item_2", 4800))
    await until(lambda: len(player.chunks) == 3)
    player.played = 250.0
    await call.interrupt()
    assert socket.events()[-2:] == [
        {"type": "response.cancel"},
        {"type": "conversation.item.truncate", "item_id": "item_2", "content_index": 0, "audio_end_ms": 50},
    ]
    assert player.flushes == 1
    await call.close()


async def test_interrupt_after_playback_ended_only_cancels():
    player = FakePlayer()
    call, socket, _ = await connect(player=player)
    socket.push(audio_delta("item_1", 4800))
    await until(lambda: player.chunks)
    player.played = 100.0
    await call.interrupt()
    assert [e["type"] for e in after_open(socket)] == ["response.cancel"]
    await call.close()


async def test_server_interruption_flushes_the_player():
    player = FakePlayer()
    call, socket, _ = await connect(player=player)
    socket.push(
        {
            "type": "turn.interrupted",
            "event_id": "e",
            "turn_id": "t",
            "response_id": "r",
            "item_id": "i",
            "audio_end_ms": 900,
            "heard_text": "Your appointment",
        }
    )
    await until(lambda: player.flushes)
    await call.close()


async def test_friendly_events():
    call, socket, _ = await connect()
    got = {}
    for name in (
        "transcript",
        "turn",
        "interruption",
        "backchannel",
        "tool_call",
        "timing",
        "warning",
        "error",
        "audio",
        "ended",
    ):
        call.on(name, lambda data, name=name: got.setdefault(name, []).append(data))
    for frame in [
        {
            "type": "conversation.item.input_audio_transcription.delta",
            "event_id": "e",
            "item_id": "i",
            "content_index": 0,
            "delta": "my",
            "transcript": "my name",
        },
        {
            "type": "response.output_audio_transcript.delta",
            "event_id": "e",
            "response_id": "r",
            "item_id": "i",
            "output_index": 0,
            "content_index": 0,
            "delta": "Hello",
            "audio_start_ms": 40,
        },
        {
            "type": "response.output_audio_transcript.done",
            "event_id": "e",
            "response_id": "r",
            "item_id": "i",
            "output_index": 0,
            "content_index": 0,
            "transcript": "Hello there",
        },
        {"type": "input_audio_buffer.speech_started", "event_id": "e", "audio_start_ms": 10, "item_id": "i"},
        {"type": "response.created", "event_id": "e", "response": {"id": "r", "metadata": {"turn_id": "t"}}},
        {
            "type": "turn.interrupted",
            "event_id": "e",
            "turn_id": "t",
            "response_id": "r",
            "item_id": "i",
            "audio_end_ms": 900,
            "heard_text": "Your",
        },
        {
            "type": "turn.tool",
            "event_id": "e",
            "turn_id": "t",
            "call_id": "c",
            "name": "book",
            "arguments": "{}",
            "output": "ok",
            "at_ms": 5,
            "duration_ms": 12,
        },
        {
            "type": "turn.timing",
            "event_id": "e",
            "turn_id": "t",
            "mark": "first_audio",
            "at_ms": 700,
            "from_end_of_turn_ms": 650,
        },
        {
            "type": "turn.warning",
            "event_id": "e",
            "turn_id": None,
            "code": "tool_timeout",
            "message": "late",
            "at_ms": 3,
        },
        {
            "type": "error",
            "event_id": "e",
            "error": {"type": "invalid_request_error", "code": "bad_item", "message": "no"},
        },
        audio_delta("i", 4),
        {
            "type": "session.ended",
            "event_id": "e",
            "session_id": "s",
            "duration_ms": 1000,
            "usage": {"voice_seconds": 1.0, "model_tokens_in": 1, "model_tokens_out": 2, "amount_micros": 3},
        },
        {"type": "session.ended", "event_id": "e2", "session_id": "s", "duration_ms": 1000, "usage": {}},
    ]:
        socket.push(frame)
    await until(lambda: "ended" in got)
    assert got["transcript"] == [
        {"role": "caller", "text": "my name", "final": False},
        {"role": "agent", "text": "Hello", "final": False, "audio_start_ms": 40},
        {"role": "agent", "text": "Hello there", "final": True},
    ]
    assert got["turn"] == [{"phase": "speech_started"}, {"phase": "reply_start", "turn_id": "t"}]
    assert got["interruption"] == [{"heard_text": "Your", "audio_end_ms": 900}]
    assert got["tool_call"] == [{"turn_id": "t", "name": "book", "arguments": "{}", "output": "ok", "duration_ms": 12}]
    assert got["timing"] == [{"turn_id": "t", "mark": "first_audio", "at_ms": 700, "from_end_of_turn_ms": 650}]
    assert got["warning"] == [{"turn_id": None, "code": "tool_timeout", "message": "late"}]
    assert got["error"] == [{"code": "bad_item", "message": "no"}]
    assert got["audio"] == [{"pcm": base64.b64encode(b"\0" * 4).decode()}]
    assert len(got["ended"]) == 1 and got["ended"][0]["session_id"] == "s"
    await call.close()


async def test_wire_subscriptions_iteration_and_unknown_names():
    call, socket, _ = await connect()
    wire, unsub_seen = [], []
    call.on("session.created", wire.append)
    off = call.on("response.done", unsub_seen.append)
    off()
    with pytest.raises(ValueError):
        call.on("not.an.event", print)
    created = {"type": "session.created", "event_id": "e", "session": {"id": "s", "object": "realtime.session"}}
    socket.push(created)
    socket.push(
        {"type": "response.done", "event_id": "e", "response": {"id": "r", "object": "o", "status": "s", "output": []}}
    )
    socket.push_close(1000)
    events = [event async for event in call]
    assert [e["type"] for e in events] == ["session.created", "response.done"]
    assert wire == [created] and unsub_seen == []
    assert await call.wait_closed() == 1000
    assert call.close_error is None


async def test_on_error_gets_typed_errors():
    call, socket, _ = await connect()
    errors = []
    call.on_error(errors.append)
    socket.push(
        {
            "type": "error",
            "event_id": "e",
            "error": {"type": "invalid_request_error", "code": "bad_session", "message": "voice is not valid"},
        }
    )
    await until(lambda: errors)
    assert isinstance(errors[0], InvalidRequestError)
    assert (errors[0].code, errors[0].message) == ("bad_session", "voice is not valid")
    await call.close()


async def test_async_callbacks_are_awaited():
    call, socket, _ = await connect()
    got = []

    async def on_turn(data):
        await asyncio.sleep(0)
        got.append(data)

    call.on("turn", on_turn)
    socket.push({"type": "input_audio_buffer.speech_stopped", "event_id": "e", "audio_end_ms": 5, "item_id": "i"})
    await until(lambda: got)
    assert got == [{"phase": "speech_stopped"}]
    await call.close()


async def test_close_code_becomes_a_typed_error():
    call, socket, _ = await connect()
    socket.push_close(4402)
    assert await call.wait_closed() == 4402
    assert isinstance(call.close_error, InsufficientCreditError)
    assert call.close_error.code == "credit_exhausted"
    with pytest.raises(SessionClosedError) as caught:
        await call.send_text("still there?")
    assert caught.value.close_code == 4402


async def test_every_send_on_a_closed_call_raises_session_closed():
    call, socket, _ = await connect()
    socket.push_close(1000)
    await call.wait_closed()
    sends = [
        call.update({"voice": "marcus"}),
        call.send_audio(b"\0\0"),
        call.send_text("hi"),
        call.send_tool_output("c1", {}),
        call.truncate("i1", 10),
        call.create_response(),
        call.cancel_response(),
        call.interrupt(),
    ]
    for send in sends:
        with pytest.raises(SessionClosedError):
            await send
    assert after_open(socket) == []


async def test_auth_close_is_an_authentication_error():
    call, socket, _ = await connect()
    socket.push_close(4401)
    await call.wait_closed()
    assert isinstance(call.close_error, AuthenticationError)
