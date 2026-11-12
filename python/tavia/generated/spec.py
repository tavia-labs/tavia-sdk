# GENERATED from the API specification. Do not edit.
SDK_VERSION = "0.9.0"

LAYERS = {
    "voice": {
        "subprotocol": "tavia-voice",
    },
    "stt": {
        "subprotocol": "tavia-stt",
        "host": "stt.tavialabs.com",
    },
    "tts": {
        "subprotocol": "tavia-tts",
    },
}

TOKEN_SUBPROTOCOL_PREFIX = "tavia-token."

PRESET_PARAM = "preset"

BASE_PATH = "/v1"

BASE_URL = "https://api.tavialabs.com/v1"

DIALECT = {
    "param": "dialect",
    "value": "ga",
    "extrasKey": "tavia",
    "extrasField": "events",
    "sessionPaths": {
        "instructions": "instructions",
        "tools": "tools",
        "input_audio_format": "audio.input.format",
        "turn_detection": "audio.input.turn_detection",
        "output_audio_format": "audio.output.format",
        "voice": "audio.output.voice",
    },
    "renames": {
        "response.audio.delta": "response.output_audio.delta",
        "response.audio.done": "response.output_audio.done",
        "response.audio_transcript.delta": "response.output_audio_transcript.delta",
        "response.audio_transcript.done": "response.output_audio_transcript.done",
    },
}

PATHS = {
    "realtime": "/v1/realtime",
    "sttFiles": "/v1/transcriptions",
    "sttLive": "/transcribe-websocket",
    "ttsStream": "/v1/tts/stream",
    "ttsRender": "/v1/tts/render",
    "voices": "/v1/voices",
}

CLOSE_CODE_BASE = 4000

SESSION_OPTIONS = [
    "instructions",
    "tools",
    "voice",
    "languages",
    "turn_detection",
    "input_audio_format",
    "output_audio_format",
    "tool_auto_continue",
    "default_tool_effect",
    "knowledge",
    "emergency",
    "bound",
    "timezone",
    "country",
    "holidays",
    "closures",
    "hours",
    "guard",
    "notes",
    "voice_feedback",
]

CLIENT_EVENT_TYPES = [
    "session.update",
    "input_audio_buffer.append",
    "conversation.item.create",
    "conversation.item.truncate",
    "response.create",
    "input_audio_buffer.commit",
    "input_audio_buffer.clear",
    "response.cancel",
    "task.status",
]

SERVER_EVENT_TYPES = [
    "session.created",
    "session.updated",
    "session.ended",
    "error",
    "input_audio_buffer.speech_started",
    "input_audio_buffer.speech_stopped",
    "input_audio_buffer.committed",
    "input_audio_buffer.cleared",
    "conversation.item.added",
    "conversation.item.done",
    "conversation.item.truncated",
    "conversation.item.input_audio_transcription.delta",
    "conversation.item.input_audio_transcription.completed",
    "response.created",
    "response.done",
    "response.output_audio.delta",
    "response.output_audio.done",
    "response.output_audio_transcript.delta",
    "response.output_audio_transcript.done",
    "response.content_part.added",
    "response.content_part.done",
    "response.function_call_arguments.delta",
    "response.function_call_arguments.done",
    "response.output_item.added",
    "response.output_item.done",
    "turn.timing",
    "turn.backchannel",
    "turn.tool",
    "turn.warning",
    "turn.knowledge",
    "turn.guard",
    "notes.updated",
    "tool.started",
    "tool.result",
    "tasks.updated",
    "result.delivered",
    "turn.interrupted",
]

UNSUPPORTED_CLIENT_EVENT_TYPES = [
    "conversation.item.delete",
    "conversation.item.retrieve",
    "output_audio_buffer.clear",
    "transcription_session.update",
]

FRIENDLY_EVENTS = {
    "conversation.item.input_audio_transcription.delta": "transcript",
    "conversation.item.input_audio_transcription.completed": "transcript",
    "response.output_audio_transcript.delta": "transcript",
    "response.output_audio_transcript.done": "transcript",
    "input_audio_buffer.speech_started": "turn",
    "input_audio_buffer.speech_stopped": "turn",
    "response.created": "turn",
    "turn.interrupted": "interruption",
    "turn.backchannel": "backchannel",
    "turn.tool": "tool_call",
    "turn.timing": "timing",
    "turn.warning": "warning",
    "error": "error",
    "response.output_audio.delta": "audio",
    "session.ended": "ended",
}

TOOL_MARKS = {
    "effect": "x-effect",
    "effects": [
        "read",
        "write",
    ],
    "effectDefault": "write",
    "action": "x-action",
    "actions": [
        "create",
        "cancel",
        "change",
        "send",
        "transfer",
        "log",
    ],
    "freeText": "x-free-text",
    "date": "x-date",
    "dates": [
        "booking",
        "record",
    ],
}

VOICES = {
    "public": [
        {
            "id": "elaine",
            "name": "Elaine",
            "description": "warm, friendly",
            "languages": [
                "en",
                "zh",
                "ms",
                "id",
            ],
        },
        {
            "id": "wenhui",
            "name": "Wenhui",
            "description": "calm, clear",
            "languages": [
                "en",
                "zh",
                "ms",
                "id",
            ],
        },
        {
            "id": "gwen",
            "name": "Gwen",
            "description": "mature, reassuring",
            "languages": [
                "en",
                "zh",
                "id",
            ],
        },
        {
            "id": "henry",
            "name": "Henry",
            "description": "deep, patient",
            "languages": [
                "en",
                "zh",
                "ms",
            ],
        },
        {
            "id": "kai",
            "name": "Kai",
            "description": "bright, young",
            "languages": [
                "en",
                "zh",
            ],
        },
        {
            "id": "marcus",
            "name": "Marcus",
            "description": "steady, professional",
            "languages": [
                "en",
                "zh",
                "ms",
                "id",
            ],
        },
        {
            "id": "ren",
            "name": "Ren",
            "description": "casual, local",
            "languages": [
                "en",
                "zh",
                "ms",
            ],
        },
    ],
    "default": "elaine",
    "byLanguage": {
        "en": "elaine",
        "zh": "elaine",
        "ms": "elaine",
        "id": "elaine",
    },
}

LANGUAGES = {
    "supported": [
        "en",
        "zh",
        "ms",
        "id",
    ],
    "default": "en",
    "max": 2,
}

TTS_STYLES = [
    "neutral",
    "warm",
    "empathetic",
    "upbeat",
    "thinking",
]

TOOL_TEMPLATES = [
    {
        "id": "check_availability",
        "version": 1,
        "title": "Check availability",
        "tool": {
            "type": "function",
            "name": "check_availability",
            "x-effect": "read",
            "description": (
                "Free appointment times on one day. Call it before offering any time; "
                "never guess times."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "format": "date",
                        "description": (
                            "The day to check, as YYYY-MM-DD. Work out words like tomorrow from "
                            "today's date."
                        ),
                        "x-date": "booking",
                    },
                    "service": {
                        "type": "string",
                        "description": "The appointment type, if the caller named one.",
                    },
                    "staff": {
                        "type": "string",
                        "description": "The doctor or staff member the caller asked for, if any.",
                    },
                },
                "required": [
                    "date",
                ],
            },
        },
    },
    {
        "id": "book_appointment",
        "version": 1,
        "title": "Book appointment",
        "tool": {
            "type": "function",
            "name": "book_appointment",
            "x-effect": "write",
            "description": (
                "Book an appointment at a time the caller chose. Use only a time "
                "check_availability returned."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "format": "date",
                        "description": "The day, as YYYY-MM-DD.",
                    },
                    "time": {
                        "type": "string",
                        "format": "time",
                        "description": "The start time as HH:MM (24-hour), one check_availability returned.",
                    },
                    "name": {
                        "type": "string",
                        "description": "The caller's full name as they gave it.",
                    },
                    "phone": {
                        "type": "string",
                        "format": "phone",
                        "description": "The caller's mobile number.",
                    },
                    "service": {
                        "type": "string",
                        "description": "The appointment type, if the caller named one.",
                    },
                    "notes": {
                        "type": "string",
                        "x-free-text": True,
                        "description": "Anything else the caller wants the team to know.",
                    },
                },
                "required": [
                    "date",
                    "time",
                    "name",
                    "phone",
                ],
            },
        },
    },
    {
        "id": "reschedule_appointment",
        "version": 1,
        "title": "Reschedule appointment",
        "tool": {
            "type": "function",
            "name": "reschedule_appointment",
            "x-effect": "write",
            "description": (
                "Move an existing booking to a new day and time the caller chose from "
                "check_availability."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": (
                            "The booking reference, from lookup_booking or as the caller reads it "
                            "out."
                        ),
                    },
                    "new_date": {
                        "type": "string",
                        "format": "date",
                        "description": "The new day, as YYYY-MM-DD.",
                    },
                    "new_time": {
                        "type": "string",
                        "format": "time",
                        "description": "The new start time as HH:MM (24-hour).",
                    },
                },
                "required": [
                    "booking_id",
                    "new_date",
                    "new_time",
                ],
            },
        },
    },
    {
        "id": "cancel_appointment",
        "version": 1,
        "title": "Cancel appointment",
        "tool": {
            "type": "function",
            "name": "cancel_appointment",
            "x-effect": "write",
            "description": "Cancel an existing booking after the caller confirmed which one.",
            "parameters": {
                "type": "object",
                "properties": {
                    "booking_id": {
                        "type": "string",
                        "description": (
                            "The booking reference, from lookup_booking or as the caller reads it "
                            "out."
                        ),
                    },
                    "reason": {
                        "type": "string",
                        "x-free-text": True,
                        "description": "Why the caller is cancelling, if they said.",
                    },
                },
                "required": [
                    "booking_id",
                ],
            },
        },
    },
    {
        "id": "lookup_booking",
        "version": 1,
        "title": "Look up a booking",
        "tool": {
            "type": "function",
            "name": "lookup_booking",
            "x-effect": "read",
            "description": (
                "Find the caller's upcoming bookings by phone number or booking "
                "reference. Give at least one of them."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "format": "phone",
                        "description": "The mobile number the booking was made with.",
                    },
                    "booking_id": {
                        "type": "string",
                        "description": "The booking reference, if the caller has it.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "id": "opening_hours",
        "version": 1,
        "title": "Opening hours",
        "tool": {
            "type": "function",
            "name": "opening_hours",
            "x-effect": "read",
            "description": (
                "Opening hours, including public holidays. Call it when the caller asks "
                "when you are open."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "format": "date",
                        "description": (
                            "A specific day to check, as YYYY-MM-DD. Leave it out for the usual "
                            "weekly hours."
                        ),
                    },
                    "location": {
                        "type": "string",
                        "description": "The branch, if you have more than one.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "id": "geocode",
        "version": 1,
        "title": "Look up an address",
        "tool": {
            "type": "function",
            "name": "geocode",
            "x-effect": "read",
            "description": (
                "Turn a place the caller named (address, postal code, building or "
                "landmark) into a full address and map coordinates. Call it before "
                "ranking branches or checking the service area."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "The place as the caller said it, for example a street and block number, "
                            "a postal code or a landmark."
                        ),
                    },
                    "country": {
                        "type": "string",
                        "pattern": "^[A-Z]{2}$",
                        "description": (
                            "The two-letter country code to search in, for example SG. Leave it out "
                            "for the business's own country."
                        ),
                    },
                },
                "required": [
                    "query",
                ],
            },
        },
    },
    {
        "id": "find_nearest_branch",
        "version": 1,
        "title": "Find nearest branch by travel time",
        "tool": {
            "type": "function",
            "name": "find_nearest_branch",
            "x-effect": "read",
            "description": (
                "Rank the business's branches by travel time from the caller, for the way "
                "they will travel. Give origin, or latitude and longitude from geocode."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": (
                            "Where the caller is starting from: an address, postal code, area, "
                            "landmark or station."
                        ),
                    },
                    "latitude": {
                        "type": "number",
                        "minimum": -90,
                        "maximum": 90,
                        "description": "The caller's latitude, when geocode already returned it.",
                    },
                    "longitude": {
                        "type": "number",
                        "minimum": -180,
                        "maximum": 180,
                        "description": "The caller's longitude, when geocode already returned it.",
                    },
                    "mode": {
                        "type": "string",
                        "enum": [
                            "transit",
                            "driving",
                            "walking",
                            "cycling",
                        ],
                        "description": "How the caller will travel. Leave it out for public transport.",
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "description": "How many branches to return, nearest first. Leave it out for three.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "id": "get_directions",
        "version": 1,
        "title": "Directions to a branch",
        "tool": {
            "type": "function",
            "name": "get_directions",
            "x-effect": "read",
            "description": (
                "Step-by-step directions from the caller's place to one branch, by the "
                "way they will travel. Call it when the caller asks how to get there."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": (
                            "Where the caller is starting from: an address, postal code, area, "
                            "landmark or station."
                        ),
                    },
                    "branch": {
                        "type": "string",
                        "description": (
                            "The branch to go to, by the name find_nearest_branch returned or the "
                            "caller gave."
                        ),
                    },
                    "mode": {
                        "type": "string",
                        "enum": [
                            "transit",
                            "driving",
                            "walking",
                            "cycling",
                        ],
                        "description": "How the caller will travel. Leave it out for public transport.",
                    },
                },
                "required": [
                    "origin",
                    "branch",
                ],
            },
        },
    },
    {
        "id": "check_service_area",
        "version": 1,
        "title": "Check service area",
        "tool": {
            "type": "function",
            "name": "check_service_area",
            "x-effect": "read",
            "description": (
                "Whether an address or postal code is inside the area the business "
                "serves, for home visits, deliveries or on-site jobs. Call it before "
                "offering a visit to the caller's address."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "The caller's address or postal code, as they gave it.",
                    },
                    "service": {
                        "type": "string",
                        "description": "The service the caller wants, if your area differs by service.",
                    },
                },
                "required": [
                    "address",
                ],
            },
        },
    },
    {
        "id": "order_status",
        "version": 1,
        "title": "Order status",
        "tool": {
            "type": "function",
            "name": "order_status",
            "x-effect": "read",
            "description": (
                "Where an order is and when it should arrive. Ask for the order number "
                "first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order number as the caller reads it out, for example A1042.",
                    },
                },
                "required": [
                    "order_id",
                ],
            },
        },
    },
    {
        "id": "check_stock",
        "version": 1,
        "title": "Check stock",
        "tool": {
            "type": "function",
            "name": "check_stock",
            "x-effect": "read",
            "description": "Whether a product is in stock, and how many are left.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string",
                        "description": "The product name or model the caller asked about.",
                    },
                    "location": {
                        "type": "string",
                        "description": "The store to check, if you have more than one.",
                    },
                },
                "required": [
                    "item",
                ],
            },
        },
    },
    {
        "id": "transfer_to_staff",
        "version": 1,
        "title": "Transfer to staff",
        "tool": {
            "type": "function",
            "name": "transfer_to_staff",
            "x-effect": "write",
            "description": (
                "Hand the call to a person when the caller asks for one or the request is "
                "outside your tools."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "team": {
                        "type": "string",
                        "enum": [
                            "front_desk",
                            "billing",
                            "support",
                        ],
                        "description": "Which team should take the call. Edit this list to your own teams.",
                    },
                    "reason": {
                        "type": "string",
                        "x-free-text": True,
                        "description": "One line on what the caller needs, so staff pick up with context.",
                    },
                },
                "required": [
                    "team",
                ],
            },
        },
    },
    {
        "id": "take_message",
        "version": 1,
        "title": "Take a message",
        "tool": {
            "type": "function",
            "name": "take_message",
            "x-effect": "write",
            "description": "Leave a message for the team to call the caller back.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The caller's name.",
                    },
                    "phone": {
                        "type": "string",
                        "format": "phone",
                        "description": "The number to call back.",
                    },
                    "message": {
                        "type": "string",
                        "x-free-text": True,
                        "description": "What the caller wants, in their words.",
                    },
                    "callback_window": {
                        "type": "string",
                        "enum": [
                            "morning",
                            "afternoon",
                            "evening",
                            "any",
                        ],
                        "description": "When the caller prefers a call back.",
                    },
                },
                "required": [
                    "name",
                    "phone",
                    "message",
                ],
            },
        },
    },
    {
        "id": "send_confirmation",
        "version": 1,
        "title": "Send confirmation",
        "tool": {
            "type": "function",
            "name": "send_confirmation",
            "x-effect": "write",
            "description": (
                "Send the caller the details of a booking or order by text message or "
                "email."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reference": {
                        "type": "string",
                        "description": "The booking or order reference to confirm.",
                    },
                    "channel": {
                        "type": "string",
                        "enum": [
                            "sms",
                            "email",
                        ],
                        "description": "How to send it.",
                    },
                },
                "required": [
                    "reference",
                    "channel",
                ],
            },
        },
    },
]

LIMITS = {
    "limits.instructionsChars": 32000,
    "limits.tools": 64,
    "limits.toolNameRegex": "^[A-Za-z0-9_-]{1,64}$",
    "limits.termsBytes": 16384,
    "apiKeyLimits.sessionS": 1800,
    "apiKeyLimits.livePerKey": 2,
    "apiKeyLimits.livePerOrg": 3,
    "apiKeyLimits.livePerOrgMax": 8,
    "apiKeyLimits.sessionsPerHourPerKey": 40,
    "apiKeyLimits.sessionsPerHourPerOrg": 80,
    "apiKeyLimits.rendersPerMinute": 40,
    "realtime.maxEventBytes": 131072,
    "realtime.maxAudioBytes": 65536,
    "realtime.maxVoiceChars": 64,
    "realtime.maxToolOutputChars": 32768,
    "realtime.maxIdChars": 64,
    "realtime.silenceMs": {
        "min": 200,
        "max": 3000,
        "default": 1000,
    },
    "realtime.inputRates": [
        24000,
        16000,
    ],
    "realtime.outputRates": [
        24000,
    ],
    "realtime.maxToolRounds": 4,
    "realtime.pendingTools": {
        "fillerMs": 1000,
        "timeoutS": 10,
    },
    "realtime.idleS": 300,
    "realtime.context": {
        "windowTokens": 16384,
        "promptTokens": 8192,
    },
    "realtime.toolSchema": {
        "maxDepth": 10,
        "maxNodes": 2000,
        "maxKeyChars": 64,
        "maxPatternChars": 256,
        "maxPatternsPerTool": 32,
        "maxPatterns": 64,
        "patternSubset": {
            "escapes": "\\.*+?()[]{}|^$/-tnrfv",
            "shorthand": "dDwWsSbB",
            "maxRepeat": 100,
            "maxExpandedChars": 1000,
        },
    },
    "realtime.tokenCaps": {
        "promptChars": 4096,
        "tools": 8,
        "replies": 60,
        "items": 20,
        "itemChars": 4096,
        "sessionS": 600,
        "sessionsPerHour": 20,
        "sessionsPerHourAll": 200,
    },
    "realtime.knowledge.maxIdChars": 64,
    "realtime.knowledge.pluginDeadlineMs": {
        "min": 50,
        "default": 120,
        "max": 800,
    },
    "realtime.builtinTools.prefix": "tavia_",
    "languages.supported": [
        "en",
        "zh",
        "ms",
        "id",
    ],
    "languages.max": 2,
    "stt.sampleRate": 16000,
    "stt.terms": 120,
    "stt.fileBytes": 104857600,
    "stt.fileAudioS": 1800,
    "ttsStream.contextIdRegex": "^[A-Za-z0-9_-]{1,16}$",
    "ttsStream.maxQueuedSpeaks": 8,
    "ttsStream.maxContexts": 16,
    "ttsStream.styles": [
        "neutral",
        "warm",
        "empathetic",
        "upbeat",
        "thinking",
    ],
}

SURFACE = {
    "client": {
        "realtime": [
            "connect",
        ],
        "stt": [
            "stream",
            "transcribe",
            "create_job",
            "get_job",
            "delete_job",
        ],
        "tts": [
            "stream",
            "render",
            "voices",
        ],
        "tokens": [
            "create",
        ],
    },
    "urls": {
        "keys": [
            "realtime",
            "stt_live",
            "stt_files",
            "tts_stream",
            "tts_render",
            "voices",
            "tokens",
        ],
    },
    "functions": {
        "names": [
            "check_tools",
            "template_tool",
            "function_tool",
        ],
    },
    "closed": {
        "error": "SessionClosedError",
        "afterErrorClose": {
            "methods": [
                "TtsStream.end",
            ],
        },
    },
    "realtime": {
        "methods": {
            "session.update": [
                "update",
            ],
            "input_audio_buffer.append": [
                "send_audio",
            ],
            "conversation.item.create": [
                "send_text",
                "send_tool_output",
            ],
            "conversation.item.truncate": [
                "truncate",
            ],
            "response.create": [
                "create_response",
            ],
            "response.cancel": [
                "cancel_response",
            ],
            "input_audio_buffer.commit": [
                "commit_audio",
            ],
            "input_audio_buffer.clear": [
                "clear_audio",
            ],
            "task.status": [
                "send_task_status",
            ],
        },
        "helpers": [
            "tool",
            "interrupt",
            "close",
        ],
    },
    "stt": {
        "config": [
            "audio_format",
            "sample_rate",
            "num_channels",
            "decoder",
            "context",
            "nbest",
            "format",
            "include_fillers",
            "client_reference_id",
        ],
        "decoders": [
            "general",
            "spell",
        ],
        "messages": {
            "finalize": "finalize",
            "set_decoder": "set_decoder",
            "set_context": "set_terms",
            "keepalive": "keepalive",
            "end": "end",
        },
        "final": [
            "tokens",
            "total_audio_proc_ms",
            "nbest",
            "decoder",
            "empty",
            "formatted",
            "fillers",
        ],
        "jobStatuses": [
            "queued",
            "running",
            "done",
            "failed",
        ],
    },
    "tts": {
        "frames": {
            "start": "open",
            "speak": "speak",
            "close_context": "close_context",
            "cancel": "cancel",
            "end": "end",
        },
        "speak": [
            "context_id",
            "text",
            "lang",
            "style",
        ],
        "render": [
            "voice",
            "text",
            "lang",
            "style",
        ],
        "stopped": [
            "length",
            "cap",
            "timeout",
            "cancelled",
        ],
        "sampleRate": 24000,
        "headerBytes": 16,
        "renderMaxChars": 500,
    },
    "tokens": {
        "host": "api.tavialabs.com",
        "path": "/v1/tokens",
        "request": [
            "product",
            "origin",
            "session",
        ],
        "response": [
            "token",
            "url",
            "subprotocols",
            "expires_at",
            "session",
        ],
    },
}
