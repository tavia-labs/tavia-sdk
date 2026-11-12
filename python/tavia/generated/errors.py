# GENERATED from the API specification. Do not edit.
from enum import Enum
from typing import NamedTuple, Union

CLOSE_CODE_BASE = 4000


class ErrorSpec(NamedTuple):
    http: int
    message: str


class ErrorCode(str, Enum):
    INVALID_REQUEST = "invalid_request"
    BLOCKED_URL = "blocked_url"
    CAPTCHA_FAILED = "captcha_failed"
    BAD_AUDIO = "bad_audio"
    BAD_FRAME = "bad_frame"
    BAD_JSON = "bad_json"
    BAD_START = "bad_start"
    BAD_ITEM = "bad_item"
    BAD_SESSION = "bad_session"
    TIMEZONE_REQUIRED = "timezone_required"
    BAD_TRUNCATE = "bad_truncate"
    TOO_LONG = "too_long"
    BAD_TEXT = "bad_text"
    UNSUPPORTED_LANGUAGE = "unsupported_language"
    TOO_MANY_TOOLS = "too_many_tools"
    PROMPT_TOO_LARGE = "prompt_too_large"
    UNKNOWN_EVENT = "unknown_event"
    UNKNOWN_ITEM = "unknown_item"
    UNKNOWN_CALL_ID = "unknown_call_id"
    INVALID_AUDIO_END = "invalid_audio_end"
    ACTIVE_RESPONSE = "active_response"
    BINARY_NOT_SUPPORTED = "binary_not_supported"
    NOT_SUPPORTED = "not_supported"
    VOICE_LOCKED = "voice_locked"
    UNAUTHORIZED = "unauthorized"
    ACCOUNT_REQUIRED = "account_required"
    CREDIT_EXHAUSTED = "credit_exhausted"
    FORBIDDEN = "forbidden"
    SCOPE_MISSING = "scope_missing"
    STEP_UP_REQUIRED = "step_up_required"
    PRESET_LOCKED = "preset_locked"
    NOT_ALLOWED = "not_allowed"
    NOT_FOUND = "not_found"
    UNKNOWN_VOICE = "unknown_voice"
    NO_START = "no_start"
    UPLOAD_TIMEOUT = "upload_timeout"
    SESSION_LIMIT = "session_limit"
    IDLE_TIMEOUT = "idle_timeout"
    CONFLICT = "conflict"
    LINK_EXPIRED = "link_expired"
    TOO_LARGE = "too_large"
    AUDIO_TOO_LONG = "audio_too_long"
    UNSUPPORTED_AUDIO = "unsupported_audio"
    UNSUPPORTED_FILE = "unsupported_file"
    VERIFY_FAILED = "verify_failed"
    RATE_LIMITED = "rate_limited"
    ACTIVE_JOB = "active_job"
    TOO_MANY_SESSIONS = "too_many_sessions"
    QUEUE_FULL = "queue_full"
    ITEM_LIMIT = "item_limit"
    REPLY_LIMIT = "reply_limit"
    TALK_LIMIT = "talk_limit"
    WAKE_LIMIT = "wake_limit"
    NOT_CONFIGURED = "not_configured"
    INTERNAL = "internal"
    ENGINE = "engine"
    REPLY_FAILED = "reply_failed"
    SESSION_FAILED = "session_failed"
    TRANSCRIPTION_FAILED = "transcription_failed"
    BUSY = "busy"
    TIMEOUT = "timeout"
    SERVER_SHUTDOWN = "server_shutdown"
    SERVICE_UNAVAILABLE = "service_unavailable"
    SPEECH_INPUT_UNAVAILABLE = "speech_input_unavailable"
    SPEECH_OUTPUT_UNAVAILABLE = "speech_output_unavailable"


ERRORS: dict[str, ErrorSpec] = {
    "invalid_request": ErrorSpec(400, "The request is not valid."),
    "blocked_url": ErrorSpec(400, "That address is not allowed."),
    "captcha_failed": ErrorSpec(400, "The human check failed. Please try again."),
    "bad_audio": ErrorSpec(400, "The audio could not be read."),
    "bad_frame": ErrorSpec(400, "A frame could not be read."),
    "bad_json": ErrorSpec(400, "A message is not valid JSON."),
    "bad_start": ErrorSpec(400, "The session start message is not valid."),
    "bad_item": ErrorSpec(400, "A conversation item is not valid."),
    "bad_session": ErrorSpec(400, "The session settings are not valid."),
    "timezone_required": ErrorSpec(400, "This country has more than one timezone. Set timezone."),
    "bad_truncate": ErrorSpec(400, "The truncate request is not valid."),
    "too_long": ErrorSpec(400, "The text is too long."),
    "bad_text": ErrorSpec(400, "The text cannot be spoken."),
    "unsupported_language": ErrorSpec(400, "This voice does not speak that language."),
    "too_many_tools": ErrorSpec(400, "Too many tools for this session."),
    "prompt_too_large": ErrorSpec(400, "The instructions and tools are too long for this session."),
    "unknown_event": ErrorSpec(400, "Unknown event type."),
    "unknown_item": ErrorSpec(400, "Unknown conversation item."),
    "unknown_call_id": ErrorSpec(400, "Unknown tool call."),
    "invalid_audio_end": ErrorSpec(400, "The audio end time is not valid."),
    "active_response": ErrorSpec(400, "A reply is already in progress."),
    "binary_not_supported": ErrorSpec(400, "Binary frames are not supported here."),
    "not_supported": ErrorSpec(400, "That is not supported."),
    "voice_locked": ErrorSpec(400, "The voice cannot change after the first reply."),
    "unauthorized": ErrorSpec(401, "Sign in or use a valid key."),
    "account_required": ErrorSpec(401, "This token carries no account. Sign in again."),
    "credit_exhausted": ErrorSpec(402, "Your credit has run out. New sessions are paused."),
    "forbidden": ErrorSpec(403, "You do not have access to this."),
    "scope_missing": ErrorSpec(403, "This key does not have access to this product."),
    "step_up_required": ErrorSpec(403, "Confirm it is you to continue."),
    "preset_locked": ErrorSpec(403, "These settings are fixed by the preset or by the session bound to the token."),
    "not_allowed": ErrorSpec(403, "That is not allowed in this session."),
    "not_found": ErrorSpec(404, "Not found."),
    "unknown_voice": ErrorSpec(404, "Unknown voice."),
    "no_start": ErrorSpec(408, "The session did not start in time."),
    "upload_timeout": ErrorSpec(408, "The upload took too long."),
    "session_limit": ErrorSpec(408, "The session reached its time limit."),
    "idle_timeout": ErrorSpec(408, "The session was idle for too long."),
    "conflict": ErrorSpec(409, "That conflicts with the current state."),
    "link_expired": ErrorSpec(410, "This link has expired or was already used."),
    "too_large": ErrorSpec(413, "The request is too large."),
    "audio_too_long": ErrorSpec(413, "The audio is too long."),
    "unsupported_audio": ErrorSpec(415, "That audio format is not supported."),
    "unsupported_file": ErrorSpec(415, "That file type is not supported. Upload txt, md, csv, pdf or docx."),
    "verify_failed": ErrorSpec(422, "The speech did not pass its quality check."),
    "rate_limited": ErrorSpec(429, "Too many requests. Please wait and try again."),
    "active_job": ErrorSpec(429, "Another job is still running. Wait for it to finish."),
    "too_many_sessions": ErrorSpec(429, "Too many sessions are open."),
    "queue_full": ErrorSpec(429, "The service is full. Please try again shortly."),
    "item_limit": ErrorSpec(429, "This session's text item limit is reached."),
    "reply_limit": ErrorSpec(429, "This session reached its reply limit."),
    "talk_limit": ErrorSpec(429, "Tavia has talked a lot today. Please try again tomorrow."),
    "wake_limit": ErrorSpec(429, "Tavia has been woken up many times today. Please try again later."),
    "not_configured": ErrorSpec(500, "The service is not configured."),
    "internal": ErrorSpec(500, "Something went wrong on our side."),
    "engine": ErrorSpec(500, "Speech generation failed."),
    "reply_failed": ErrorSpec(500, "The reply could not be produced."),
    "session_failed": ErrorSpec(500, "The session failed."),
    "transcription_failed": ErrorSpec(500, "The transcription failed. Please try again."),
    "busy": ErrorSpec(503, "The server is busy. Please try again shortly."),
    "timeout": ErrorSpec(504, "The transcription is still running: poll it as a job."),
    "server_shutdown": ErrorSpec(503, "The server is restarting. Please reconnect."),
    "service_unavailable": ErrorSpec(503, "The service is not available right now."),
    "speech_input_unavailable": ErrorSpec(503, "Listening is not available right now."),
    "speech_output_unavailable": ErrorSpec(503, "Speaking is not available right now."),
}


def close_code_for(code: Union[ErrorCode, str]) -> int:
    """A WebSocket that ends on an error closes with CLOSE_CODE_BASE + the HTTP status of its code."""
    return CLOSE_CODE_BASE + ERRORS[ErrorCode(code).value].http


def message_for(code: Union[ErrorCode, str]) -> str:
    return ERRORS[ErrorCode(code).value].message


class WarningCode(str, Enum):
    SPEECH_CLAUSE_DROPPED = "speech_clause_dropped"
    SPEECH_BACKUP_VOICE = "speech_backup_voice"
    TOOL_CALL_REFUSED = "tool_call_refused"
    TOOL_TIMEOUT = "tool_timeout"
    TOOL_EFFECT_DEFAULTED = "tool_effect_defaulted"
    REPLY_RETRIED = "reply_retried"
    UNBACKED_VALUE_BLOCKED = "unbacked_value_blocked"
    KNOWLEDGE_UNAVAILABLE = "knowledge_unavailable"
    KNOWLEDGE_LATE = "knowledge_late"
    CLAIM_HELD = "claim_held"
    LANG_MISMATCH = "lang_mismatch"
    REPLY_CUT = "reply_cut"
    EMERGENCY_RENDERED = "emergency_rendered"
    NOT_ALLOWED_NOW = "not_allowed_now"
    EMERGENCY_UNCONFIGURED_COUNTRY = "emergency_unconfigured_country"


WARNINGS: dict[str, str] = {
    "speech_clause_dropped": "Part of the reply could not be spoken.",
    "speech_backup_voice": "Part of the reply was spoken by the backup voice.",
    "tool_call_refused": "A tool call was refused and returned to the agent: unknown tool, invalid arguments, an unchecked date, an unconfirmed write or a call still pending.",
    "tool_timeout": "A tool call got no output in time; the agent was told it timed out.",
    "tool_effect_defaulted": "A tool has no x-effect, so it is treated as a write: it runs only after a read-back and the caller's yes. Set x-effect read or write on every tool.",
    "reply_retried": "The model failed or stalled; the agent said a holding line and tried once more.",
    "unbacked_value_blocked": "A spoken value that nothing in the instructions, the caller's words or this call's tool results backs was held back.",
    "knowledge_unavailable": "The knowledge base did not answer in time or failed; the turn went on without new knowledge.",
    "knowledge_late": "The knowledge plug-in missed its deadline; the agent said a holding line and the result is added when it arrives.",
    "claim_held": "The guard held a line saying something was done before it ran.",
    "lang_mismatch": "The guard held a line in another language than the caller's.",
    "reply_cut": "The guard cut a reply over its length cap at a sentence boundary.",
    "emergency_rendered": "The emergency line was spoken from the business's config.",
    "not_allowed_now": "The guard refused a tool call whose id no lookup in this call returned.",
    "emergency_unconfigured_country": "The session's country has no emergency line and no emergency config is set: an emergency turn gets a line with no number.",
}
