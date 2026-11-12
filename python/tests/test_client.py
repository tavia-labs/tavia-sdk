import httpx
import pytest
from conftest import KEY, FakeSocket, make_client

from tavia import ConnectError, RateLimitError, ServerError, Tavia, TaviaError, __version__
from tavia._transport import Context
from tavia.generated.spec import SDK_VERSION


def test_needs_exactly_one_credential():
    with pytest.raises(ValueError):
        Tavia()
    with pytest.raises(ValueError):
        Tavia(KEY, token="tok")


def test_version_is_the_spec_version():
    assert __version__ == SDK_VERSION


def test_default_endpoints_are_on_the_public_api():
    urls = Tavia(KEY)._ctx.urls
    assert urls["realtime"] == "wss://api.tavialabs.com/v1/realtime"
    assert urls["sttLive"] == "wss://stt.tavialabs.com/transcribe-websocket"  # the live socket keeps its host
    assert urls["sttFiles"] == "https://api.tavialabs.com/v1/transcriptions"
    assert urls["ttsStream"] == "wss://api.tavialabs.com/v1/tts/stream"
    assert urls["ttsRender"] == "https://api.tavialabs.com/v1/tts/render"
    assert urls["voices"] == "https://api.tavialabs.com/v1/voices"
    assert urls["tokens"] == "https://api.tavialabs.com/v1/tokens"


def test_url_overrides_are_full_urls_used_as_given():
    urls = Tavia(KEY, urls={"realtime": "ws://localhost:8080/rt", "stt_files": "http://localhost:9000/jobs"})._ctx.urls
    assert urls["realtime"] == "ws://localhost:8080/rt"
    assert urls["sttFiles"] == "http://localhost:9000/jobs"
    assert urls["sttLive"] == "wss://stt.tavialabs.com/transcribe-websocket"


def test_base_url_serves_every_path_under_it():
    urls = Tavia(KEY, base_url="http://localhost:8080/v1/")._ctx.urls
    assert urls["realtime"] == "ws://localhost:8080/v1/realtime"
    assert urls["sttFiles"] == "http://localhost:8080/v1/transcriptions"
    assert urls["ttsStream"] == "ws://localhost:8080/v1/tts/stream"
    assert urls["ttsRender"] == "http://localhost:8080/v1/tts/render"
    assert urls["voices"] == "http://localhost:8080/v1/voices"
    assert urls["tokens"] == "http://localhost:8080/v1/tokens"
    assert urls["sttLive"] == "wss://stt.tavialabs.com/transcribe-websocket"  # the live socket keeps its host


def test_a_url_override_beats_the_base_url():
    urls = Tavia(KEY, base_url="https://api.example.com/v1", urls={"voices": "http://x/v"})._ctx.urls
    assert urls["voices"] == "http://x/v" and urls["realtime"] == "wss://api.example.com/v1/realtime"


def test_an_unknown_url_override_is_refused():
    with pytest.raises(ValueError, match="stt"):
        Tavia(KEY, urls={"stt": "https://stt.example.com"})


async def test_an_overridden_socket_url_is_dialled_as_given():
    client, connector, _ = make_client(FakeSocket(), urls={"realtime": "ws://localhost:8080/rt"})
    call = await client.realtime.connect()
    assert connector.calls[0].url == "ws://localhost:8080/rt?dialect=ga"
    await call.close()


@pytest.mark.parametrize("product, subprotocol", [("voice", "tavia-voice"), ("stt", "tavia-stt"), ("tts", "tavia-tts")])
async def test_api_key_rides_as_bearer_header(product, subprotocol):
    client, connector, _ = make_client(FakeSocket())
    session = await _open(client, product)
    call = connector.calls[0]
    assert call.subprotocols == [subprotocol]
    assert call.headers == {"Authorization": f"Bearer {KEY}"}
    await session.close()


@pytest.mark.parametrize("product, subprotocol", [("voice", "tavia-voice"), ("stt", "tavia-stt"), ("tts", "tavia-tts")])
async def test_token_rides_as_second_subprotocol(product, subprotocol):
    client, connector, _ = make_client(FakeSocket(), token="abc.def")
    session = await _open(client, product)
    call = connector.calls[0]
    assert call.subprotocols == [subprotocol, "tavia-token.abc.def"]
    assert call.headers == {}
    await session.close()


async def _open(client, product):
    if product == "voice":
        return await client.realtime.connect()
    if product == "stt":
        return await client.stt.stream()
    return await client.tts.stream("elaine")


async def test_http_with_a_token_sends_it_as_bearer():
    client, _, recorder = make_client(answer=lambda r: httpx.Response(200, json={"voices": []}), token="tok")
    await client.tts.voices()
    assert recorder.requests[0].headers["Authorization"] == "Bearer tok"


async def test_a_socket_closed_before_open_is_a_connect_error():
    socket = FakeSocket()
    socket.closed = True
    client, _, _ = make_client(socket)
    with pytest.raises(ConnectError):
        await client.realtime.connect(session={"voice": "elaine"})


async def test_async_with_closes_the_http_client_it_made():
    async with Tavia(KEY) as client:
        http = client._ctx.http
    assert http.is_closed


async def test_a_passed_http_client_stays_open():
    http = httpx.AsyncClient()
    async with Tavia(KEY, http=http):
        pass
    assert not http.is_closed
    await http.aclose()


def test_context_makes_its_http_client_lazily():
    ctx = Context(Tavia(KEY)._ctx.auth, {}, None, None)
    assert ctx._http is None


def _answers(*replies):
    """An httpx handler answering each request with the next (status, json, headers) or raising a connect error."""
    queue = list(replies)

    def answer(request):
        reply = queue.pop(0)
        if isinstance(reply, Exception):
            raise reply
        status, body, headers = (*reply, {})[:3]
        return httpx.Response(status, json=body, headers=headers)

    return answer


NOW = {"retry-after": "0"}


async def test_rate_limits_and_unavailable_answers_are_retried():
    client, _, recorder = make_client(
        answer=_answers((429, {"error": "rate_limited"}, NOW), (503, None, NOW), (200, {"voices": []}))
    )
    assert await client.tts.voices() == {"voices": []}
    assert len(recorder.requests) == 3


async def test_retries_stop_at_max_retries_with_the_typed_error():
    client, _, recorder = make_client(
        answer=_answers((429, {"error": "rate_limited"}, NOW), (429, {"error": "rate_limited"}, NOW)), max_retries=1
    )
    with pytest.raises(RateLimitError):
        await client.tts.voices()
    assert len(recorder.requests) == 2


async def test_no_retry_when_the_server_says_not_to():
    client, _, recorder = make_client(answer=_answers((503, {"error": "timeout"}, {"x-should-retry": "false"})))
    with pytest.raises(ServerError):
        await client.tts.voices()
    assert len(recorder.requests) == 1


async def test_other_errors_are_not_retried():
    client, _, recorder = make_client(answer=_answers((500, None)))
    with pytest.raises(ServerError):
        await client.tts.voices()
    assert len(recorder.requests) == 1


async def test_a_network_failure_is_a_connect_error():
    down = httpx.ConnectError("refused")
    client, _, recorder = make_client(answer=_answers(down, down, down))
    with pytest.raises(ConnectError) as caught:
        await client.tts.voices()
    assert isinstance(caught.value, TaviaError) and caught.value.close_code is None and caught.value.http is None
    assert len(recorder.requests) == 3
