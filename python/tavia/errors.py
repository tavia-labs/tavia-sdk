"""Typed errors: one class per HTTP status, every API error code mapped to its class."""

from typing import Any

from tavia.generated.errors import CLOSE_CODE_BASE, ERRORS, ErrorCode, WarningCode

__all__ = [
    "ERROR_CLASSES",
    "STATUS_CLASSES",
    "AuthenticationError",
    "ConflictError",
    "ConnectError",
    "ErrorCode",
    "InsufficientCreditError",
    "InvalidRequestError",
    "NotFoundError",
    "PermissionDeniedError",
    "RateLimitError",
    "RequestTimeoutError",
    "ServerError",
    "SessionClosedError",
    "TaviaError",
    "TooLargeError",
    "UnprocessableError",
    "UnsupportedMediaError",
    "WarningCode",
    "error_for_close",
    "error_for_code",
    "error_for_http",
]

NORMAL_CLOSES = frozenset({1000, 1001})


class TaviaError(Exception):
    """Every failure the SDK reports: the API's error code (when the server named one) and its HTTP status.

    Attributes:
        code: The API's error code, such as "unauthorized", or None.
        http: The HTTP status, or None.
        message: A readable message; defaults to the code's standard message.
        close_code: The WebSocket close code, for a socket failure.
        context_id: The text-to-speech context the error belongs to, or None for the whole stream.
        param: The failing request field, as session.tools[1].name, when the server names one.
    """

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        http: int | None = None,
        close_code: int | None = None,
        context_id: str | None = None,
        param: str | None = None,
    ):
        spec = ERRORS.get(code) if code else None
        self.code = code
        self.http = http if http is not None else (spec.http if spec else None)
        self.message = message or (spec.message if spec else None) or code or "request failed"
        self.close_code = close_code
        self.context_id = context_id
        self.param = param
        super().__init__(self.message)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(code={self.code!r}, http={self.http!r}, message={self.message!r})"


class InvalidRequestError(TaviaError):
    """HTTP 400: the request is malformed or has an invalid field."""


class AuthenticationError(TaviaError):
    """HTTP 401: the API key or token is missing, invalid or expired."""


class InsufficientCreditError(TaviaError):
    """HTTP 402: the account has no credit left."""


class PermissionDeniedError(TaviaError):
    """HTTP 403: the key or token may not do this."""


class NotFoundError(TaviaError):
    """HTTP 404: the resource does not exist."""


class RequestTimeoutError(TaviaError):
    """HTTP 408: the request took too long."""


class ConflictError(TaviaError):
    """HTTP 409 or 410: the request conflicts with the resource's state, or the resource is gone."""


class TooLargeError(TaviaError):
    """HTTP 413: the request or file is too large."""


class UnsupportedMediaError(TaviaError):
    """HTTP 415: the media type is not supported."""


class UnprocessableError(TaviaError):
    """HTTP 422: the request is well formed but cannot be processed."""


class RateLimitError(TaviaError):
    """HTTP 429: too many requests or sessions; retry later."""


class ServerError(TaviaError):
    """HTTP 5xx: the server failed."""


class SessionClosedError(TaviaError):
    """Raised by any send on a session whose socket is closed or closing; close_code is the close, once known."""

    def __init__(self, close_code: int | None = None):
        message = "the session is closed" if close_code is None else f"the session is closed ({close_code})"
        super().__init__(message, close_code=close_code)


# The error class for each HTTP status; other 5xx statuses map to ServerError.
STATUS_CLASSES: dict[int, type[TaviaError]] = {
    400: InvalidRequestError,
    401: AuthenticationError,
    402: InsufficientCreditError,
    403: PermissionDeniedError,
    404: NotFoundError,
    408: RequestTimeoutError,
    409: ConflictError,
    410: ConflictError,
    413: TooLargeError,
    415: UnsupportedMediaError,
    422: UnprocessableError,
    429: RateLimitError,
    500: ServerError,
    502: ServerError,
    503: ServerError,
    504: ServerError,
}


def _class_for(http: int | None) -> type[TaviaError]:
    if http in STATUS_CLASSES:
        return STATUS_CLASSES[http]
    return ServerError if http is not None and http >= 500 else TaviaError


# Every API error code and the error class it raises.
ERROR_CLASSES: dict[str, type[TaviaError]] = {code: _class_for(spec.http) for code, spec in ERRORS.items()}


def error_for_code(code: str, message: str | None = None, **extra: Any) -> TaviaError:
    """The typed error for an API error code; an unknown code gives a plain TaviaError carrying it."""
    fallback = extra.pop("http", None)
    http = ERRORS[code].http if code in ERRORS else fallback
    return _class_for(http)(message, code=code, http=http, **extra)


def close_info(close_code: int | None) -> tuple[int | None, str | None]:
    """(HTTP status, API error code) a close code reports; the code is None when several share that status."""
    if close_code is None:
        return None, None
    http = close_code - CLOSE_CODE_BASE
    if not 400 <= http < 600:
        return None, None
    codes = [code for code, spec in ERRORS.items() if spec.http == http]
    return http, codes[0] if len(codes) == 1 else None


def error_for_close(close_code: int | None) -> TaviaError | None:
    """The error a close code reports, or None for a normal close (1000, 1001)."""
    if close_code in NORMAL_CLOSES:
        return None
    http, code = close_info(close_code)
    return _class_for(http)(f"the session closed ({close_code})", code=code, http=http, close_code=close_code)


def error_for_http(status: int, body: Any) -> TaviaError:
    """The typed error for an HTTP error response.

    The body is {"error": {code, message, param?}} or {"error": "code"}.
    """
    err = body.get("error") if isinstance(body, dict) else None
    code = err if isinstance(err, str) else (err.get("code") if isinstance(err, dict) else None)
    fields = err if isinstance(err, dict) else {}
    return _class_for(status)(fields.get("message"), code=code, http=status, param=fields.get("param"))


class ConnectError(TaviaError):
    """The server could not be reached, or a socket closed or was refused before the session opened.

    For a socket, close_code carries the server's reason (4000 + HTTP status); for a network failure the cause is
    the underlying exception.
    """

    def __init__(
        self,
        close_code: int | None = None,
        *,
        http: int | None = None,
        code: str | None = None,
        message: str | None = None,
    ):
        closed_http, closed_code = close_info(close_code)
        http = http if http is not None else closed_http
        code = code if code is not None else closed_code
        reason = close_code if close_code is not None else http
        super().__init__(
            message or f"the session closed before it opened ({reason})", code=code, http=http, close_code=close_code
        )


# The message the agent gets when a tool handler fails without a ToolError.
TOOL_FAILED = "tool_failed"


class ToolError(Exception):
    """Raise from a tool handler to tell the agent why: this message, and only this, reaches the model."""
