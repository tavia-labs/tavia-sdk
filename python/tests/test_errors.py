from tavia.errors import (
    AuthenticationError,
    ConflictError,
    ConnectError,
    InsufficientCreditError,
    InvalidRequestError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TaviaError,
    error_for_close,
    error_for_code,
    error_for_http,
)


def test_error_for_code_picks_the_class_of_its_status():
    err = error_for_code("credit_exhausted")
    assert isinstance(err, InsufficientCreditError)
    assert (err.code, err.http) == ("credit_exhausted", 402)
    assert err.message == "Your credit has run out. New sessions are paused."
    assert isinstance(error_for_code("link_expired"), ConflictError)
    assert isinstance(error_for_code("busy"), ServerError)


def test_error_for_code_keeps_a_given_message():
    assert error_for_code("bad_session", "voice is not valid").message == "voice is not valid"


def test_unknown_code_is_a_plain_tavia_error():
    err = error_for_code("brand_new_code", "later")
    assert type(err) is TaviaError
    assert (err.code, err.message, err.http) == ("brand_new_code", "later", None)


def test_error_for_close():
    assert error_for_close(1000) is None
    assert error_for_close(1001) is None
    credit = error_for_close(4402)
    assert isinstance(credit, InsufficientCreditError)
    assert (credit.code, credit.close_code, credit.http) == ("credit_exhausted", 4402, 402)
    auth = error_for_close(4401)
    assert isinstance(auth, AuthenticationError)
    assert auth.code is None  # unauthorized and account_required share 401
    odd = error_for_close(1006)
    assert type(odd) is TaviaError and odd.close_code == 1006


def test_error_for_http_reads_both_body_shapes():
    err = error_for_http(404, {"error": "not_found"})
    assert isinstance(err, NotFoundError) and err.code == "not_found"
    err = error_for_http(429, {"error": {"code": "rate_limited", "message": "slow down"}})
    assert isinstance(err, RateLimitError)
    assert (err.code, err.message, err.http) == ("rate_limited", "slow down", 429)
    err = error_for_http(400, "plain text")
    assert isinstance(err, InvalidRequestError) and err.code is None


def test_error_for_http_names_the_failing_param():
    body = {
        "error": {
            "code": "bad_session",
            "message": "The session settings are not valid.",
            "param": "session.tools[1].name",
        }
    }
    err = error_for_http(400, body)
    assert (err.code, err.param) == ("bad_session", "session.tools[1].name")
    assert error_for_http(404, {"error": "not_found"}).param is None


def test_connect_error_carries_the_close_reason():
    err = ConnectError(4402)
    assert isinstance(err, TaviaError)
    assert (err.close_code, err.http, err.code) == (4402, 402, "credit_exhausted")
