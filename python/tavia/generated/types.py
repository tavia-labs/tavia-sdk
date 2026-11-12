# GENERATED from the API specification. Do not edit.
# flake8: noqa: E501
from typing import Any, Literal, NotRequired, TypedDict, Union

SessionConfigTools = TypedDict("SessionConfigTools", {
    "type": Literal["function"],
    "name": str,
    "description": NotRequired[str],
    "parameters": NotRequired[dict[str, Any]],
    "x-effect": NotRequired[Literal["read", "write"]],
    "x-action": NotRequired[Literal["create", "cancel", "change", "send", "transfer", "log"]],
})

SessionConfigTurnDetection = TypedDict("SessionConfigTurnDetection", {
    "type": Literal["server_vad", "semantic_vad"],
    "create_response": NotRequired[bool],
    "interrupt_response": NotRequired[bool],
    "eagerness": NotRequired[Literal["low", "medium", "high", "auto"]],
    "silence_duration_ms": NotRequired[int],
    "audio_output": NotRequired[Literal["speaker", "headset", "unknown"]],
})

SessionConfigInputAudioFormatAudioPcm = TypedDict("SessionConfigInputAudioFormatAudioPcm", {
    "type": Literal["audio/pcm"],
    "rate": Literal[24000, 16000],
})

SessionConfigOutputAudioFormatAudioPcm = TypedDict("SessionConfigOutputAudioFormatAudioPcm", {
    "type": Literal["audio/pcm"],
    "rate": Literal[24000],
})

SessionConfigKnowledge = TypedDict("SessionConfigKnowledge", {
    "mode": Literal["prompt", "rag", "shadow"],
    "kb_id": NotRequired[str],
    "plugin": NotRequired[str],
    "deadline_ms": NotRequired[int],
})

SessionConfigEmergency = TypedDict("SessionConfigEmergency", {
    "country": str,
    "number": str,
})

SessionConfigHolidays = TypedDict("SessionConfigHolidays", {
    "date": str,
    "name": str,
    "aliases": NotRequired[list[str]],
})

SessionConfigClosures = TypedDict("SessionConfigClosures", {
    "date": str,
    "name": str,
    "aliases": NotRequired[list[str]],
})

SessionConfigHours = TypedDict("SessionConfigHours", {
    "day": Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
    "open": str,
    "close": str,
})

SessionConfigGuard = TypedDict("SessionConfigGuard", {
    "mode": Literal["off", "shadow", "enforce"],
})

SessionConfigNotes = TypedDict("SessionConfigNotes", {
    "forbid": NotRequired[list[Literal["nric", "card", "phone", "email"]]],
    "mask": NotRequired[list[Literal["nric", "card", "phone", "email"]]],
})

SessionConfigVoiceFeedback = TypedDict("SessionConfigVoiceFeedback", {
    "acks": NotRequired[bool],
    "backchannels": NotRequired[bool],
    "register": NotRequired[Literal["professional", "casual"]],
})

SessionConfig = TypedDict("SessionConfig", {
    "instructions": NotRequired[str],
    "tools": NotRequired[list[SessionConfigTools]],
    "voice": NotRequired[Literal["elaine", "wenhui", "gwen", "henry", "kai", "marcus", "ren", "mei"]],
    "languages": NotRequired[list[Literal["en", "zh", "ms", "id"]]],
    "turn_detection": NotRequired[Union[SessionConfigTurnDetection, None]],
    "input_audio_format": NotRequired[Union[Literal["pcm16"], SessionConfigInputAudioFormatAudioPcm]],
    "output_audio_format": NotRequired[Union[Literal["pcm16"], SessionConfigOutputAudioFormatAudioPcm]],
    "tool_auto_continue": NotRequired[bool],
    "default_tool_effect": NotRequired[Literal["read", "write"]],
    "knowledge": NotRequired[Union[SessionConfigKnowledge, None]],
    "emergency": NotRequired[Union[SessionConfigEmergency, None]],
    "bound": NotRequired[str],
    "timezone": NotRequired[str],
    "country": NotRequired[Literal["SG", "MY", "ID", "PH", "TH", "VN", "HK", "TW", "CN", "IN", "JP", "AE", "GB", "NZ", "AU", "BR", "CA", "CL", "KZ", "MN", "MX", "RU", "US"]],
    "holidays": NotRequired[list[SessionConfigHolidays]],
    "closures": NotRequired[list[SessionConfigClosures]],
    "hours": NotRequired[list[SessionConfigHours]],
    "guard": NotRequired[SessionConfigGuard],
    "notes": NotRequired[SessionConfigNotes],
    "voice_feedback": NotRequired[SessionConfigVoiceFeedback],
})

ToolParameter = TypedDict("ToolParameter", {
    "type": NotRequired[str],
    "description": NotRequired[str],
    "x-free-text": NotRequired[bool],
    "x-date": NotRequired[Literal["booking", "record"]],
})

WireSessionTools = TypedDict("WireSessionTools", {
    "type": Literal["function"],
    "name": str,
    "description": NotRequired[str],
    "parameters": NotRequired[dict[str, Any]],
    "x-effect": NotRequired[Literal["read", "write"]],
    "x-action": NotRequired[Literal["create", "cancel", "change", "send", "transfer", "log"]],
})

WireSessionAudioInputFormatAudioPcm = TypedDict("WireSessionAudioInputFormatAudioPcm", {
    "type": Literal["audio/pcm"],
    "rate": Literal[24000, 16000],
})

WireSessionAudioInputTurnDetection = TypedDict("WireSessionAudioInputTurnDetection", {
    "type": Literal["server_vad", "semantic_vad"],
    "create_response": NotRequired[bool],
    "interrupt_response": NotRequired[bool],
    "eagerness": NotRequired[Literal["low", "medium", "high", "auto"]],
    "silence_duration_ms": NotRequired[int],
    "audio_output": NotRequired[Literal["speaker", "headset", "unknown"]],
})

WireSessionAudioInput = TypedDict("WireSessionAudioInput", {
    "format": NotRequired[Union[Literal["pcm16"], WireSessionAudioInputFormatAudioPcm]],
    "turn_detection": NotRequired[Union[WireSessionAudioInputTurnDetection, None]],
})

WireSessionAudioOutputFormatAudioPcm = TypedDict("WireSessionAudioOutputFormatAudioPcm", {
    "type": Literal["audio/pcm"],
    "rate": Literal[24000],
})

WireSessionAudioOutput = TypedDict("WireSessionAudioOutput", {
    "format": NotRequired[Union[Literal["pcm16"], WireSessionAudioOutputFormatAudioPcm]],
    "voice": NotRequired[Literal["elaine", "wenhui", "gwen", "henry", "kai", "marcus", "ren", "mei"]],
})

WireSessionAudio = TypedDict("WireSessionAudio", {
    "input": NotRequired[WireSessionAudioInput],
    "output": NotRequired[WireSessionAudioOutput],
})

WireSessionTaviaKnowledge = TypedDict("WireSessionTaviaKnowledge", {
    "mode": Literal["prompt", "rag", "shadow"],
    "kb_id": NotRequired[str],
    "plugin": NotRequired[str],
    "deadline_ms": NotRequired[int],
})

WireSessionTaviaEmergency = TypedDict("WireSessionTaviaEmergency", {
    "country": str,
    "number": str,
})

WireSessionTaviaHolidays = TypedDict("WireSessionTaviaHolidays", {
    "date": str,
    "name": str,
    "aliases": NotRequired[list[str]],
})

WireSessionTaviaClosures = TypedDict("WireSessionTaviaClosures", {
    "date": str,
    "name": str,
    "aliases": NotRequired[list[str]],
})

WireSessionTaviaHours = TypedDict("WireSessionTaviaHours", {
    "day": Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
    "open": str,
    "close": str,
})

WireSessionTaviaGuard = TypedDict("WireSessionTaviaGuard", {
    "mode": Literal["off", "shadow", "enforce"],
})

WireSessionTaviaNotes = TypedDict("WireSessionTaviaNotes", {
    "forbid": NotRequired[list[Literal["nric", "card", "phone", "email"]]],
    "mask": NotRequired[list[Literal["nric", "card", "phone", "email"]]],
})

WireSessionTaviaVoiceFeedback = TypedDict("WireSessionTaviaVoiceFeedback", {
    "acks": NotRequired[bool],
    "backchannels": NotRequired[bool],
    "register": NotRequired[Literal["professional", "casual"]],
})

WireSessionTavia = TypedDict("WireSessionTavia", {
    "languages": NotRequired[list[Literal["en", "zh", "ms", "id"]]],
    "tool_auto_continue": NotRequired[bool],
    "default_tool_effect": NotRequired[Literal["read", "write"]],
    "knowledge": NotRequired[Union[WireSessionTaviaKnowledge, None]],
    "emergency": NotRequired[Union[WireSessionTaviaEmergency, None]],
    "bound": NotRequired[str],
    "timezone": NotRequired[str],
    "country": NotRequired[Literal["SG", "MY", "ID", "PH", "TH", "VN", "HK", "TW", "CN", "IN", "JP", "AE", "GB", "NZ", "AU", "BR", "CA", "CL", "KZ", "MN", "MX", "RU", "US"]],
    "holidays": NotRequired[list[WireSessionTaviaHolidays]],
    "closures": NotRequired[list[WireSessionTaviaClosures]],
    "hours": NotRequired[list[WireSessionTaviaHours]],
    "guard": NotRequired[WireSessionTaviaGuard],
    "notes": NotRequired[WireSessionTaviaNotes],
    "voice_feedback": NotRequired[WireSessionTaviaVoiceFeedback],
    "events": NotRequired[bool],
})

WireSession = TypedDict("WireSession", {
    "type": NotRequired[Literal["realtime"]],
    "instructions": NotRequired[str],
    "tools": NotRequired[list[WireSessionTools]],
    "audio": NotRequired[WireSessionAudio],
    "tavia": NotRequired[WireSessionTavia],
})

SessionCreatedEventSessionTools = TypedDict("SessionCreatedEventSessionTools", {

})

SessionCreatedEventSessionAudioInput = TypedDict("SessionCreatedEventSessionAudioInput", {

})

SessionCreatedEventSessionAudioOutput = TypedDict("SessionCreatedEventSessionAudioOutput", {

})

SessionCreatedEventSessionAudio = TypedDict("SessionCreatedEventSessionAudio", {
    "input": SessionCreatedEventSessionAudioInput,
    "output": SessionCreatedEventSessionAudioOutput,
})

SessionCreatedEventSessionTavia = TypedDict("SessionCreatedEventSessionTavia", {

})

SessionCreatedEventSession = TypedDict("SessionCreatedEventSession", {
    "type": Literal["realtime"],
    "object": str,
    "id": Union[str, None],
    "instructions": str,
    "tools": list[SessionCreatedEventSessionTools],
    "audio": SessionCreatedEventSessionAudio,
    "tavia": SessionCreatedEventSessionTavia,
})

SessionCreatedEvent = TypedDict("SessionCreatedEvent", {
    "type": Literal["session.created"],
    "event_id": str,
    "session": SessionCreatedEventSession,
})

SessionUpdatedEventSessionTools = TypedDict("SessionUpdatedEventSessionTools", {

})

SessionUpdatedEventSessionAudioInput = TypedDict("SessionUpdatedEventSessionAudioInput", {

})

SessionUpdatedEventSessionAudioOutput = TypedDict("SessionUpdatedEventSessionAudioOutput", {

})

SessionUpdatedEventSessionAudio = TypedDict("SessionUpdatedEventSessionAudio", {
    "input": SessionUpdatedEventSessionAudioInput,
    "output": SessionUpdatedEventSessionAudioOutput,
})

SessionUpdatedEventSessionTavia = TypedDict("SessionUpdatedEventSessionTavia", {

})

SessionUpdatedEventSession = TypedDict("SessionUpdatedEventSession", {
    "type": Literal["realtime"],
    "object": str,
    "id": Union[str, None],
    "instructions": str,
    "tools": list[SessionUpdatedEventSessionTools],
    "audio": SessionUpdatedEventSessionAudio,
    "tavia": SessionUpdatedEventSessionTavia,
})

SessionUpdatedEvent = TypedDict("SessionUpdatedEvent", {
    "type": Literal["session.updated"],
    "event_id": str,
    "session": SessionUpdatedEventSession,
})

SessionEndedEventUsage = TypedDict("SessionEndedEventUsage", {
    "voice_seconds": float,
    "model_tokens_in": int,
    "model_tokens_out": int,
    "amount_micros": int,
})

SessionEndedEventTasks = TypedDict("SessionEndedEventTasks", {
    "id": str,
    "label": str,
    "kind": Literal["read", "write"],
    "state": Literal["running", "done", "failed", "not_confirmed", "timed_out", "superseded", "cancelled"],
    "age_ms": float,
    "told": bool,
    "summary": NotRequired[str],
    "status_label": NotRequired[str],
})

SessionEndedEvent = TypedDict("SessionEndedEvent", {
    "type": Literal["session.ended"],
    "event_id": str,
    "session_id": str,
    "duration_ms": float,
    "usage": SessionEndedEventUsage,
    "guard": NotRequired[dict[str, Any]],
    "notes": NotRequired[dict[str, Any]],
    "tasks": NotRequired[list[SessionEndedEventTasks]],
})

ErrorEventError = TypedDict("ErrorEventError", {
    "type": Literal["invalid_request_error", "server_error"],
    "code": str,
    "message": str,
    "event_id": NotRequired[str],
    "issue": NotRequired[str],
    "tool": NotRequired[str],
    "param": Union[str, None],
})

ErrorEvent = TypedDict("ErrorEvent", {
    "type": Literal["error"],
    "event_id": str,
    "error": ErrorEventError,
})

InputAudioBufferSpeechStartedEvent = TypedDict("InputAudioBufferSpeechStartedEvent", {
    "type": Literal["input_audio_buffer.speech_started"],
    "event_id": str,
    "audio_start_ms": float,
    "item_id": str,
})

InputAudioBufferSpeechStoppedEvent = TypedDict("InputAudioBufferSpeechStoppedEvent", {
    "type": Literal["input_audio_buffer.speech_stopped"],
    "event_id": str,
    "audio_end_ms": float,
    "item_id": str,
})

InputAudioBufferCommittedEvent = TypedDict("InputAudioBufferCommittedEvent", {
    "type": Literal["input_audio_buffer.committed"],
    "event_id": str,
    "item_id": str,
    "previous_item_id": None,
})

InputAudioBufferClearedEvent = TypedDict("InputAudioBufferClearedEvent", {
    "type": Literal["input_audio_buffer.cleared"],
    "event_id": str,
})

ConversationItemAddedEventItem = TypedDict("ConversationItemAddedEventItem", {
    "id": str,
    "type": str,
})

ConversationItemAddedEvent = TypedDict("ConversationItemAddedEvent", {
    "type": Literal["conversation.item.added"],
    "event_id": str,
    "item": ConversationItemAddedEventItem,
    "previous_item_id": NotRequired[Union[str, None]],
})

ConversationItemDoneEventItem = TypedDict("ConversationItemDoneEventItem", {
    "id": str,
    "type": str,
})

ConversationItemDoneEvent = TypedDict("ConversationItemDoneEvent", {
    "type": Literal["conversation.item.done"],
    "event_id": str,
    "item": ConversationItemDoneEventItem,
})

ConversationItemTruncatedEvent = TypedDict("ConversationItemTruncatedEvent", {
    "type": Literal["conversation.item.truncated"],
    "event_id": str,
    "item_id": str,
    "content_index": int,
    "audio_end_ms": float,
})

ConversationItemInputAudioTranscriptionDeltaEvent = TypedDict("ConversationItemInputAudioTranscriptionDeltaEvent", {
    "type": Literal["conversation.item.input_audio_transcription.delta"],
    "event_id": str,
    "item_id": str,
    "content_index": int,
    "delta": str,
    "transcript": str,
})

ConversationItemInputAudioTranscriptionCompletedEventFillers = TypedDict("ConversationItemInputAudioTranscriptionCompletedEventFillers", {
    "before": int,
    "duration_ms": float,
})

ConversationItemInputAudioTranscriptionCompletedEventUsage = TypedDict("ConversationItemInputAudioTranscriptionCompletedEventUsage", {
    "type": Literal["duration"],
    "seconds": float,
})

ConversationItemInputAudioTranscriptionCompletedEvent = TypedDict("ConversationItemInputAudioTranscriptionCompletedEvent", {
    "type": Literal["conversation.item.input_audio_transcription.completed"],
    "event_id": str,
    "item_id": str,
    "content_index": int,
    "transcript": str,
    "fillers": NotRequired[list[ConversationItemInputAudioTranscriptionCompletedEventFillers]],
    "usage": NotRequired[ConversationItemInputAudioTranscriptionCompletedEventUsage],
})

ResponseCreatedEventResponseMetadata = TypedDict("ResponseCreatedEventResponseMetadata", {
    "kind": NotRequired[Literal["filler", "backchannel"]],
    "turn_id": NotRequired[Union[str, None]],
})

ResponseCreatedEventResponse = TypedDict("ResponseCreatedEventResponse", {
    "id": str,
    "metadata": NotRequired[ResponseCreatedEventResponseMetadata],
})

ResponseCreatedEvent = TypedDict("ResponseCreatedEvent", {
    "type": Literal["response.created"],
    "event_id": str,
    "response": ResponseCreatedEventResponse,
})

ResponseDoneEventResponseOutput = TypedDict("ResponseDoneEventResponseOutput", {

})

ResponseDoneEventResponseMetadata = TypedDict("ResponseDoneEventResponseMetadata", {
    "kind": NotRequired[Literal["filler", "backchannel"]],
    "turn_id": NotRequired[Union[str, None]],
})

ResponseDoneEventResponse = TypedDict("ResponseDoneEventResponse", {
    "id": str,
    "object": str,
    "status": str,
    "output": list[ResponseDoneEventResponseOutput],
    "metadata": NotRequired[ResponseDoneEventResponseMetadata],
})

ResponseDoneEvent = TypedDict("ResponseDoneEvent", {
    "type": Literal["response.done"],
    "event_id": str,
    "response": ResponseDoneEventResponse,
})

ResponseOutputAudioDeltaEvent = TypedDict("ResponseOutputAudioDeltaEvent", {
    "type": Literal["response.output_audio.delta"],
    "event_id": str,
    "response_id": str,
    "item_id": str,
    "output_index": int,
    "content_index": int,
    "delta": str,
})

ResponseOutputAudioDoneEvent = TypedDict("ResponseOutputAudioDoneEvent", {
    "type": Literal["response.output_audio.done"],
    "event_id": str,
    "response_id": str,
    "item_id": str,
    "output_index": int,
    "content_index": int,
})

ResponseOutputAudioTranscriptDeltaEvent = TypedDict("ResponseOutputAudioTranscriptDeltaEvent", {
    "type": Literal["response.output_audio_transcript.delta"],
    "event_id": str,
    "response_id": str,
    "item_id": str,
    "output_index": int,
    "content_index": int,
    "delta": str,
    "audio_start_ms": float,
})

ResponseOutputAudioTranscriptDoneEvent = TypedDict("ResponseOutputAudioTranscriptDoneEvent", {
    "type": Literal["response.output_audio_transcript.done"],
    "event_id": str,
    "response_id": str,
    "item_id": str,
    "output_index": int,
    "content_index": int,
    "transcript": str,
})

ResponseContentPartAddedEventPart = TypedDict("ResponseContentPartAddedEventPart", {
    "type": Literal["audio"],
    "transcript": str,
})

ResponseContentPartAddedEvent = TypedDict("ResponseContentPartAddedEvent", {
    "type": Literal["response.content_part.added"],
    "event_id": str,
    "response_id": str,
    "item_id": str,
    "output_index": int,
    "content_index": int,
    "part": ResponseContentPartAddedEventPart,
})

ResponseContentPartDoneEventPart = TypedDict("ResponseContentPartDoneEventPart", {
    "type": Literal["audio"],
    "transcript": str,
})

ResponseContentPartDoneEvent = TypedDict("ResponseContentPartDoneEvent", {
    "type": Literal["response.content_part.done"],
    "event_id": str,
    "response_id": str,
    "item_id": str,
    "output_index": int,
    "content_index": int,
    "part": ResponseContentPartDoneEventPart,
})

ResponseFunctionCallArgumentsDeltaEvent = TypedDict("ResponseFunctionCallArgumentsDeltaEvent", {
    "type": Literal["response.function_call_arguments.delta"],
    "event_id": str,
    "response_id": str,
    "output_index": int,
    "item_id": str,
    "call_id": str,
    "delta": str,
})

ResponseFunctionCallArgumentsDoneEvent = TypedDict("ResponseFunctionCallArgumentsDoneEvent", {
    "type": Literal["response.function_call_arguments.done"],
    "event_id": str,
    "response_id": str,
    "output_index": int,
    "item_id": str,
    "call_id": str,
    "name": str,
    "arguments": str,
})

ResponseOutputItemAddedEventItem = TypedDict("ResponseOutputItemAddedEventItem", {
    "id": str,
    "type": str,
})

ResponseOutputItemAddedEvent = TypedDict("ResponseOutputItemAddedEvent", {
    "type": Literal["response.output_item.added"],
    "event_id": str,
    "response_id": str,
    "output_index": int,
    "item": ResponseOutputItemAddedEventItem,
})

ResponseOutputItemDoneEventItem = TypedDict("ResponseOutputItemDoneEventItem", {
    "id": str,
    "type": str,
})

ResponseOutputItemDoneEvent = TypedDict("ResponseOutputItemDoneEvent", {
    "type": Literal["response.output_item.done"],
    "event_id": str,
    "response_id": str,
    "output_index": int,
    "item": ResponseOutputItemDoneEventItem,
})

TurnTimingEvent = TypedDict("TurnTimingEvent", {
    "type": Literal["turn.timing"],
    "event_id": str,
    "turn_id": str,
    "mark": Literal["heard", "speech_start", "end_of_turn", "barge_in", "reply_start", "first_audio", "speech_end", "stt_final", "model_request", "first_token", "first_clause", "tts_request", "ack_audio"],
    "at_ms": float,
    "from_end_of_turn_ms": Union[float, None],
    "by": NotRequired[Literal["model", "fallback"]],
    "p_eot": NotRequired[Union[float, None]],
})

TurnBackchannelEvent = TypedDict("TurnBackchannelEvent", {
    "type": Literal["turn.backchannel"],
    "event_id": str,
    "turn_id": str,
    "transcript": str,
    "at_ms": float,
})

TurnToolEvent = TypedDict("TurnToolEvent", {
    "type": Literal["turn.tool"],
    "event_id": str,
    "turn_id": str,
    "call_id": str,
    "name": str,
    "arguments": str,
    "output": str,
    "at_ms": float,
    "duration_ms": NotRequired[float],
    "runs": NotRequired[Literal["client", "webhook", "demo", "platform"]],
    "confirmed_by": NotRequired[str],
})

TurnWarningEvent = TypedDict("TurnWarningEvent", {
    "type": Literal["turn.warning"],
    "event_id": str,
    "turn_id": Union[str, None],
    "code": Literal["speech_clause_dropped", "speech_backup_voice", "tool_call_refused", "tool_timeout", "tool_effect_defaulted", "reply_retried", "unbacked_value_blocked", "knowledge_unavailable", "knowledge_late", "claim_held", "lang_mismatch", "reply_cut", "emergency_rendered", "not_allowed_now", "emergency_unconfigured_country"],
    "reason": NotRequired[str],
    "message": str,
    "at_ms": float,
    "tool": NotRequired[str],
    "detail": NotRequired[str],
})

TurnKnowledgeEventPassages = TypedDict("TurnKnowledgeEventPassages", {
    "ref": str,
    "id": str,
    "score": Union[float, None],
})

TurnKnowledgeEventCited = TypedDict("TurnKnowledgeEventCited", {
    "ref": str,
    "id": str,
    "values": list[str],
})

TurnKnowledgeEvent = TypedDict("TurnKnowledgeEvent", {
    "type": Literal["turn.knowledge"],
    "event_id": str,
    "turn_id": str,
    "mode": Literal["prompt", "rag", "shadow"],
    "status": Literal["prompt", "skipped", "empty", "warm", "appended", "rebuilt", "cold", "prefetched", "pending", "injected", "unavailable", "unsure"],
    "passages": list[TurnKnowledgeEventPassages],
    "cited": list[TurnKnowledgeEventCited],
    "searches": int,
    "prewarms": int,
    "prewarm_tokens": int,
    "final_check_ms": Union[float, None],
    "added_ms": float,
    "at_ms": float,
})

TurnGuardEventFires = TypedDict("TurnGuardEventFires", {
    "rule": Literal["write", "claim", "fact", "name", "emergency", "lang", "length", "scope"],
    "code": str,
    "action": str,
})

TurnGuardEvent = TypedDict("TurnGuardEvent", {
    "type": Literal["turn.guard"],
    "event_id": str,
    "turn_id": str,
    "response_id": str,
    "mode": Literal["shadow", "enforce"],
    "fires": list[TurnGuardEventFires],
    "clauses": int,
    "calls": int,
    "gate_ms": float,
})

NotesUpdatedEvent = TypedDict("NotesUpdatedEvent", {
    "type": Literal["notes.updated"],
    "event_id": str,
    "turn_id": str,
    "notes": dict[str, Any],
    "set": list[str],
    "removed": list[str],
    "at_ms": float,
})

ToolStartedEvent = TypedDict("ToolStartedEvent", {
    "type": Literal["tool.started"],
    "event_id": str,
    "turn_id": str,
    "call_id": str,
    "name": str,
    "write": bool,
    "at_ms": float,
})

ToolResultEvent = TypedDict("ToolResultEvent", {
    "type": Literal["tool.result"],
    "event_id": str,
    "turn_id": str,
    "call_id": str,
    "name": str,
    "status": Literal["ok", "error", "timeout", "late", "superseded", "cancelled"],
    "output": str,
    "at_ms": float,
    "duration_ms": float,
})

TasksUpdatedEventTasks = TypedDict("TasksUpdatedEventTasks", {
    "id": str,
    "label": str,
    "kind": Literal["read", "write"],
    "state": Literal["running", "done", "failed", "not_confirmed", "timed_out", "superseded", "cancelled"],
    "age_ms": float,
    "told": bool,
    "summary": NotRequired[str],
    "status_label": NotRequired[str],
})

TasksUpdatedEvent = TypedDict("TasksUpdatedEvent", {
    "type": Literal["tasks.updated"],
    "event_id": str,
    "tasks": list[TasksUpdatedEventTasks],
    "at_ms": float,
})

ResultDeliveredEvent = TypedDict("ResultDeliveredEvent", {
    "type": Literal["result.delivered"],
    "event_id": str,
    "turn_id": str,
    "response_id": str,
    "call_id": str,
    "name": str,
    "at_ms": float,
    "wait_ms": float,
})

TurnInterruptedEvent = TypedDict("TurnInterruptedEvent", {
    "type": Literal["turn.interrupted"],
    "event_id": str,
    "turn_id": str,
    "response_id": str,
    "item_id": str,
    "audio_end_ms": float,
    "heard_text": str,
})

ServerEvent = Union[
    SessionCreatedEvent,
    SessionUpdatedEvent,
    SessionEndedEvent,
    ErrorEvent,
    InputAudioBufferSpeechStartedEvent,
    InputAudioBufferSpeechStoppedEvent,
    InputAudioBufferCommittedEvent,
    InputAudioBufferClearedEvent,
    ConversationItemAddedEvent,
    ConversationItemDoneEvent,
    ConversationItemTruncatedEvent,
    ConversationItemInputAudioTranscriptionDeltaEvent,
    ConversationItemInputAudioTranscriptionCompletedEvent,
    ResponseCreatedEvent,
    ResponseDoneEvent,
    ResponseOutputAudioDeltaEvent,
    ResponseOutputAudioDoneEvent,
    ResponseOutputAudioTranscriptDeltaEvent,
    ResponseOutputAudioTranscriptDoneEvent,
    ResponseContentPartAddedEvent,
    ResponseContentPartDoneEvent,
    ResponseFunctionCallArgumentsDeltaEvent,
    ResponseFunctionCallArgumentsDoneEvent,
    ResponseOutputItemAddedEvent,
    ResponseOutputItemDoneEvent,
    TurnTimingEvent,
    TurnBackchannelEvent,
    TurnToolEvent,
    TurnWarningEvent,
    TurnKnowledgeEvent,
    TurnGuardEvent,
    NotesUpdatedEvent,
    ToolStartedEvent,
    ToolResultEvent,
    TasksUpdatedEvent,
    ResultDeliveredEvent,
    TurnInterruptedEvent,
]

SERVER_EVENT_CLASSES: dict[str, Any] = {
    "session.created": SessionCreatedEvent,
    "session.updated": SessionUpdatedEvent,
    "session.ended": SessionEndedEvent,
    "error": ErrorEvent,
    "input_audio_buffer.speech_started": InputAudioBufferSpeechStartedEvent,
    "input_audio_buffer.speech_stopped": InputAudioBufferSpeechStoppedEvent,
    "input_audio_buffer.committed": InputAudioBufferCommittedEvent,
    "input_audio_buffer.cleared": InputAudioBufferClearedEvent,
    "conversation.item.added": ConversationItemAddedEvent,
    "conversation.item.done": ConversationItemDoneEvent,
    "conversation.item.truncated": ConversationItemTruncatedEvent,
    "conversation.item.input_audio_transcription.delta": ConversationItemInputAudioTranscriptionDeltaEvent,
    "conversation.item.input_audio_transcription.completed": ConversationItemInputAudioTranscriptionCompletedEvent,
    "response.created": ResponseCreatedEvent,
    "response.done": ResponseDoneEvent,
    "response.output_audio.delta": ResponseOutputAudioDeltaEvent,
    "response.output_audio.done": ResponseOutputAudioDoneEvent,
    "response.output_audio_transcript.delta": ResponseOutputAudioTranscriptDeltaEvent,
    "response.output_audio_transcript.done": ResponseOutputAudioTranscriptDoneEvent,
    "response.content_part.added": ResponseContentPartAddedEvent,
    "response.content_part.done": ResponseContentPartDoneEvent,
    "response.function_call_arguments.delta": ResponseFunctionCallArgumentsDeltaEvent,
    "response.function_call_arguments.done": ResponseFunctionCallArgumentsDoneEvent,
    "response.output_item.added": ResponseOutputItemAddedEvent,
    "response.output_item.done": ResponseOutputItemDoneEvent,
    "turn.timing": TurnTimingEvent,
    "turn.backchannel": TurnBackchannelEvent,
    "turn.tool": TurnToolEvent,
    "turn.warning": TurnWarningEvent,
    "turn.knowledge": TurnKnowledgeEvent,
    "turn.guard": TurnGuardEvent,
    "notes.updated": NotesUpdatedEvent,
    "tool.started": ToolStartedEvent,
    "tool.result": ToolResultEvent,
    "tasks.updated": TasksUpdatedEvent,
    "result.delivered": ResultDeliveredEvent,
    "turn.interrupted": TurnInterruptedEvent,
}

ResponseAudioDeltaEvent = ResponseOutputAudioDeltaEvent  # deprecated: renamed "response.output_audio.delta"
ResponseAudioDoneEvent = ResponseOutputAudioDoneEvent  # deprecated: renamed "response.output_audio.done"
ResponseAudioTranscriptDeltaEvent = ResponseOutputAudioTranscriptDeltaEvent  # deprecated: renamed "response.output_audio_transcript.delta"
ResponseAudioTranscriptDoneEvent = ResponseOutputAudioTranscriptDoneEvent  # deprecated: renamed "response.output_audio_transcript.done"

SessionUpdateEventSessionTools = TypedDict("SessionUpdateEventSessionTools", {
    "type": Literal["function"],
    "name": str,
    "description": NotRequired[str],
    "parameters": NotRequired[dict[str, Any]],
    "x-effect": NotRequired[Literal["read", "write"]],
    "x-action": NotRequired[Literal["create", "cancel", "change", "send", "transfer", "log"]],
})

SessionUpdateEventSessionAudioInputFormatAudioPcm = TypedDict("SessionUpdateEventSessionAudioInputFormatAudioPcm", {
    "type": Literal["audio/pcm"],
    "rate": Literal[24000, 16000],
})

SessionUpdateEventSessionAudioInputTurnDetection = TypedDict("SessionUpdateEventSessionAudioInputTurnDetection", {
    "type": Literal["server_vad", "semantic_vad"],
    "create_response": NotRequired[bool],
    "interrupt_response": NotRequired[bool],
    "eagerness": NotRequired[Literal["low", "medium", "high", "auto"]],
    "silence_duration_ms": NotRequired[int],
    "audio_output": NotRequired[Literal["speaker", "headset", "unknown"]],
})

SessionUpdateEventSessionAudioInput = TypedDict("SessionUpdateEventSessionAudioInput", {
    "format": NotRequired[Union[Literal["pcm16"], SessionUpdateEventSessionAudioInputFormatAudioPcm]],
    "turn_detection": NotRequired[Union[SessionUpdateEventSessionAudioInputTurnDetection, None]],
})

SessionUpdateEventSessionAudioOutputFormatAudioPcm = TypedDict("SessionUpdateEventSessionAudioOutputFormatAudioPcm", {
    "type": Literal["audio/pcm"],
    "rate": Literal[24000],
})

SessionUpdateEventSessionAudioOutput = TypedDict("SessionUpdateEventSessionAudioOutput", {
    "format": NotRequired[Union[Literal["pcm16"], SessionUpdateEventSessionAudioOutputFormatAudioPcm]],
    "voice": NotRequired[Literal["elaine", "wenhui", "gwen", "henry", "kai", "marcus", "ren", "mei"]],
})

SessionUpdateEventSessionAudio = TypedDict("SessionUpdateEventSessionAudio", {
    "input": NotRequired[SessionUpdateEventSessionAudioInput],
    "output": NotRequired[SessionUpdateEventSessionAudioOutput],
})

SessionUpdateEventSessionTaviaKnowledge = TypedDict("SessionUpdateEventSessionTaviaKnowledge", {
    "mode": Literal["prompt", "rag", "shadow"],
    "kb_id": NotRequired[str],
    "plugin": NotRequired[str],
    "deadline_ms": NotRequired[int],
})

SessionUpdateEventSessionTaviaEmergency = TypedDict("SessionUpdateEventSessionTaviaEmergency", {
    "country": str,
    "number": str,
})

SessionUpdateEventSessionTaviaHolidays = TypedDict("SessionUpdateEventSessionTaviaHolidays", {
    "date": str,
    "name": str,
    "aliases": NotRequired[list[str]],
})

SessionUpdateEventSessionTaviaClosures = TypedDict("SessionUpdateEventSessionTaviaClosures", {
    "date": str,
    "name": str,
    "aliases": NotRequired[list[str]],
})

SessionUpdateEventSessionTaviaHours = TypedDict("SessionUpdateEventSessionTaviaHours", {
    "day": Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
    "open": str,
    "close": str,
})

SessionUpdateEventSessionTaviaGuard = TypedDict("SessionUpdateEventSessionTaviaGuard", {
    "mode": Literal["off", "shadow", "enforce"],
})

SessionUpdateEventSessionTaviaNotes = TypedDict("SessionUpdateEventSessionTaviaNotes", {
    "forbid": NotRequired[list[Literal["nric", "card", "phone", "email"]]],
    "mask": NotRequired[list[Literal["nric", "card", "phone", "email"]]],
})

SessionUpdateEventSessionTaviaVoiceFeedback = TypedDict("SessionUpdateEventSessionTaviaVoiceFeedback", {
    "acks": NotRequired[bool],
    "backchannels": NotRequired[bool],
    "register": NotRequired[Literal["professional", "casual"]],
})

SessionUpdateEventSessionTavia = TypedDict("SessionUpdateEventSessionTavia", {
    "languages": NotRequired[list[Literal["en", "zh", "ms", "id"]]],
    "tool_auto_continue": NotRequired[bool],
    "default_tool_effect": NotRequired[Literal["read", "write"]],
    "knowledge": NotRequired[Union[SessionUpdateEventSessionTaviaKnowledge, None]],
    "emergency": NotRequired[Union[SessionUpdateEventSessionTaviaEmergency, None]],
    "bound": NotRequired[str],
    "timezone": NotRequired[str],
    "country": NotRequired[Literal["SG", "MY", "ID", "PH", "TH", "VN", "HK", "TW", "CN", "IN", "JP", "AE", "GB", "NZ", "AU", "BR", "CA", "CL", "KZ", "MN", "MX", "RU", "US"]],
    "holidays": NotRequired[list[SessionUpdateEventSessionTaviaHolidays]],
    "closures": NotRequired[list[SessionUpdateEventSessionTaviaClosures]],
    "hours": NotRequired[list[SessionUpdateEventSessionTaviaHours]],
    "guard": NotRequired[SessionUpdateEventSessionTaviaGuard],
    "notes": NotRequired[SessionUpdateEventSessionTaviaNotes],
    "voice_feedback": NotRequired[SessionUpdateEventSessionTaviaVoiceFeedback],
    "events": NotRequired[bool],
})

SessionUpdateEventSession = TypedDict("SessionUpdateEventSession", {
    "type": NotRequired[Literal["realtime"]],
    "instructions": NotRequired[str],
    "tools": NotRequired[list[SessionUpdateEventSessionTools]],
    "audio": NotRequired[SessionUpdateEventSessionAudio],
    "tavia": NotRequired[SessionUpdateEventSessionTavia],
})

SessionUpdateEvent = TypedDict("SessionUpdateEvent", {
    "type": Literal["session.update"],
    "event_id": NotRequired[str],
    "session": SessionUpdateEventSession,
})

InputAudioBufferAppendEvent = TypedDict("InputAudioBufferAppendEvent", {
    "type": Literal["input_audio_buffer.append"],
    "event_id": NotRequired[str],
    "audio": str,
})

ConversationItemCreateEventItemMessageContent = TypedDict("ConversationItemCreateEventItemMessageContent", {
    "type": Literal["input_text"],
    "text": str,
})

ConversationItemCreateEventItemMessage = TypedDict("ConversationItemCreateEventItemMessage", {
    "type": Literal["message"],
    "role": Literal["user", "system"],
    "content": list[ConversationItemCreateEventItemMessageContent],
})

ConversationItemCreateEventItemFunctionCallOutput = TypedDict("ConversationItemCreateEventItemFunctionCallOutput", {
    "type": Literal["function_call_output"],
    "call_id": str,
    "output": str,
})

ConversationItemCreateEvent = TypedDict("ConversationItemCreateEvent", {
    "type": Literal["conversation.item.create"],
    "event_id": NotRequired[str],
    "item": Union[ConversationItemCreateEventItemMessage, ConversationItemCreateEventItemFunctionCallOutput],
})

ConversationItemTruncateEvent = TypedDict("ConversationItemTruncateEvent", {
    "type": Literal["conversation.item.truncate"],
    "event_id": NotRequired[str],
    "item_id": str,
    "content_index": Literal[0],
    "audio_end_ms": int,
})

ResponseCreateEventResponse = TypedDict("ResponseCreateEventResponse", {
    "instructions": NotRequired[str],
    "metadata": NotRequired[dict[str, Any]],
    "conversation": NotRequired[Literal["auto"]],
    "output_modalities": NotRequired[list[Any]],
    "tool_choice": NotRequired[Literal["auto"]],
})

ResponseCreateEvent = TypedDict("ResponseCreateEvent", {
    "type": Literal["response.create"],
    "event_id": NotRequired[str],
    "response": NotRequired[ResponseCreateEventResponse],
})

InputAudioBufferCommitEvent = TypedDict("InputAudioBufferCommitEvent", {
    "type": Literal["input_audio_buffer.commit"],
    "event_id": NotRequired[str],
})

InputAudioBufferClearEvent = TypedDict("InputAudioBufferClearEvent", {
    "type": Literal["input_audio_buffer.clear"],
    "event_id": NotRequired[str],
})

ResponseCancelEvent = TypedDict("ResponseCancelEvent", {
    "type": Literal["response.cancel"],
    "event_id": NotRequired[str],
})

TaskStatusEvent = TypedDict("TaskStatusEvent", {
    "type": Literal["task.status"],
    "event_id": NotRequired[str],
    "call_id": str,
    "label": str,
})

ClientEvent = Union[
    SessionUpdateEvent,
    InputAudioBufferAppendEvent,
    ConversationItemCreateEvent,
    ConversationItemTruncateEvent,
    ResponseCreateEvent,
    InputAudioBufferCommitEvent,
    InputAudioBufferClearEvent,
    ResponseCancelEvent,
    TaskStatusEvent,
]

CLIENT_EVENT_CLASSES: dict[str, Any] = {
    "session.update": SessionUpdateEvent,
    "input_audio_buffer.append": InputAudioBufferAppendEvent,
    "conversation.item.create": ConversationItemCreateEvent,
    "conversation.item.truncate": ConversationItemTruncateEvent,
    "response.create": ResponseCreateEvent,
    "input_audio_buffer.commit": InputAudioBufferCommitEvent,
    "input_audio_buffer.clear": InputAudioBufferClearEvent,
    "response.cancel": ResponseCancelEvent,
    "task.status": TaskStatusEvent,
}

ToolDefinition = SessionConfigTools
KnowledgeConfig = SessionConfigKnowledge
VoiceFeedback = SessionConfigVoiceFeedback
Usage = SessionEndedEventUsage
