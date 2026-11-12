"""Tavia: realtime voice sessions, speech-to-text and text-to-speech."""

import copy

from tavia.audio import base64_to_pcm16, pcm16_to_base64, read_wav, write_wav
from tavia.client import Tavia
from tavia.errors import (
    ERROR_CLASSES,
    STATUS_CLASSES,
    AuthenticationError,
    ConflictError,
    ConnectError,
    ErrorCode,
    InsufficientCreditError,
    InvalidRequestError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    RequestTimeoutError,
    ServerError,
    SessionClosedError,
    TaviaError,
    TooLargeError,
    ToolError,
    UnprocessableError,
    UnsupportedMediaError,
    WarningCode,
    error_for_close,
    error_for_code,
    error_for_http,
)
from tavia.generated.spec import SDK_VERSION
from tavia.generated.tool_templates import TOOL_TEMPLATES
from tavia.generated.types import (
    ClientEvent,
    KnowledgeConfig,
    ServerEvent,
    SessionConfig,
    ToolDefinition,
    ToolParameter,
    Usage,
    VoiceFeedback,
)
from tavia.realtime import Call, Player
from tavia.stt import SttFinal, SttFinished, SttPartial, SttStream
from tavia.tokens import BrowserToken
from tavia.tools import ACTION, EFFECT, EFFECTS, TOOL_RULES, ToolIssue, ToolReport, check_tools
from tavia.tts import TtsAudio, TtsDone, TtsRender, TtsStream

__version__ = SDK_VERSION

__all__ = [
    "ERROR_CLASSES",
    "STATUS_CLASSES",
    "TOOL_RULES",
    "TOOL_TEMPLATES",
    "AuthenticationError",
    "BrowserToken",
    "Call",
    "ClientEvent",
    "ConflictError",
    "ConnectError",
    "ErrorCode",
    "InsufficientCreditError",
    "InvalidRequestError",
    "KnowledgeConfig",
    "NotFoundError",
    "PermissionDeniedError",
    "Player",
    "RateLimitError",
    "RequestTimeoutError",
    "ServerError",
    "ServerEvent",
    "SessionClosedError",
    "SessionConfig",
    "SttFinal",
    "SttFinished",
    "SttPartial",
    "SttStream",
    "Tavia",
    "TaviaError",
    "TooLargeError",
    "ToolDefinition",
    "ToolError",
    "ToolIssue",
    "ToolParameter",
    "ToolReport",
    "TtsAudio",
    "TtsDone",
    "TtsRender",
    "TtsStream",
    "UnprocessableError",
    "UnsupportedMediaError",
    "Usage",
    "VoiceFeedback",
    "WarningCode",
    "__version__",
    "base64_to_pcm16",
    "check_tools",
    "error_for_close",
    "error_for_code",
    "error_for_http",
    "function_tool",
    "pcm16_to_base64",
    "read_wav",
    "template_tool",
    "write_wav",
]


def function_tool(
    name: str, *, effect: str, description: str = "", parameters: dict | None = None, action: str | None = None
) -> ToolDefinition:
    """Builds a function tool definition with its effect stated, ready for session tools.

    Args:
        name: The tool's name, as the agent calls it.
        effect: "read" runs at once; "write" only after a read-back and the caller's yes. A tool sent without
            an effect is treated as a write, so label every tool.
        description: What the tool does and when the agent should call it.
        parameters: A JSON Schema for the arguments; defaults to an object with no properties.
        action: The kind of change a write tool makes, such as "create" or "cancel".

    Raises:
        ValueError: effect is not "read" or "write".

    Example:
        find_order = function_tool(
            "find_order",
            effect="read",
            description="Look up an order by its number.",
            parameters={"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]},
        )
    """
    if effect not in EFFECTS:
        raise ValueError(f"effect must be one of {', '.join(EFFECTS)}")
    tool = {
        "type": "function",
        "name": name,
        EFFECT: effect,
        "parameters": copy.deepcopy(parameters) if parameters is not None else {"type": "object", "properties": {}},
    }
    if description:
        tool["description"] = description
    if action is not None:
        tool[ACTION] = action
    return tool  # type: ignore[return-value]


def template_tool(template_id: str) -> ToolDefinition:
    """A fresh copy of a ready-made tool, ready to edit and put in session tools.

    Raises:
        ValueError: template_id is not a known template.
    """
    for template in TOOL_TEMPLATES:
        if template["id"] == template_id:
            return copy.deepcopy(template["tool"])
    known = ", ".join(t["id"] for t in TOOL_TEMPLATES)
    raise ValueError(f"unknown tool template {template_id!r}; one of: {known}")
