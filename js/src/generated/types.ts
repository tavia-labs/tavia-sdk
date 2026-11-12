// GENERATED from the API specification. Do not edit.

/** Every session option. The server accepts fields it adds before the SDK lists them; the SDK offers only these. */
export type SessionConfig = {
  instructions: string
  tools: Array<{
    type: 'function'
    name: string
    description?: string
    parameters?: Record<string, unknown>
    'x-effect'?: 'read' | 'write'
    'x-action'?: 'create' | 'cancel' | 'change' | 'send' | 'transfer' | 'log'
  }>
  voice: 'elaine' | 'wenhui' | 'gwen' | 'henry' | 'kai' | 'marcus' | 'ren' | 'mei'
  languages: Array<'en' | 'zh' | 'ms' | 'id'>
  turn_detection: {
    type: 'server_vad' | 'semantic_vad'
    create_response?: boolean
    /** Only true: the caller can always interrupt. */
    interrupt_response?: boolean
    eagerness?: 'low' | 'medium' | 'high' | 'auto'
    silence_duration_ms?: number
    audio_output?: 'speaker' | 'headset' | 'unknown'
  } | null
  input_audio_format: 'pcm16' | {
    type: 'audio/pcm'
    rate: 24000 | 16000
  }
  output_audio_format: 'pcm16' | {
    type: 'audio/pcm'
    rate: 24000
  }
  tool_auto_continue?: boolean
  default_tool_effect?: 'read' | 'write'
  knowledge?: {
    mode: 'prompt' | 'rag' | 'shadow'
    kb_id?: string
    plugin?: string
    deadline_ms?: number
  } | null
  emergency?: {
    country: string
    number: string
  } | null
  bound?: string
  timezone?: string
  country?: 'SG' | 'MY' | 'ID' | 'PH' | 'TH' | 'VN' | 'HK' | 'TW' | 'CN' | 'IN' | 'JP' | 'AE' | 'GB' | 'NZ' | 'AU' | 'BR' | 'CA' | 'CL' | 'KZ' | 'MN' | 'MX' | 'RU' | 'US'
  holidays?: Array<{
    date: string
    name: string
    aliases?: Array<string>
  }>
  closures?: Array<{
    date: string
    name: string
    aliases?: Array<string>
  }>
  hours?: Array<{
    day: 'mon' | 'tue' | 'wed' | 'thu' | 'fri' | 'sat' | 'sun'
    open: string
    close: string
  }>
  guard?: {
    mode: 'off' | 'shadow' | 'enforce'
  }
  notes?: {
    forbid?: Array<'nric' | 'card' | 'phone' | 'email'>
    mask?: Array<'nric' | 'card' | 'phone' | 'email'>
  }
  voice_feedback?: {
    acks?: boolean
    backchannels?: boolean
    register?: 'professional' | 'casual'
  }
}

export type SessionOption = keyof SessionConfig
export type Usage = SessionEndedEvent['usage']
export type KnowledgeConfig = NonNullable<SessionConfig['knowledge']>
export type VoiceFeedback = NonNullable<SessionConfig['voice_feedback']>

/** One tool parameter; the server reads its x-free-text and x-date marks. */
export interface ToolParameter {
  type?: string
  description?: string
  /** true: a write's read-back need not repeat this field word for word. */
  'x-free-text'?: boolean
  /** booking: checked against the clock; record: only checked to be a real date. */
  'x-date'?: 'booking' | 'record'
  [key: string]: unknown
}

export interface ToolParameters {
  type: 'object'
  properties?: Record<string, ToolParameter>
  required?: string[]
  [key: string]: unknown
}

export type ToolDefinition = Omit<SessionConfig['tools'][number], 'parameters'> & { parameters?: ToolParameters }

/** A session.update's session as sent on the wire: the standard shape, Tavia's own options under `tavia`. */
export type WireSession = {
  type?: 'realtime'
  instructions?: string
  tools?: Array<{
    type: 'function'
    name: string
    description?: string
    parameters?: Record<string, unknown>
    'x-effect'?: 'read' | 'write'
    'x-action'?: 'create' | 'cancel' | 'change' | 'send' | 'transfer' | 'log'
  }>
  audio?: {
    input?: {
      format?: 'pcm16' | {
        type: 'audio/pcm'
        rate: 24000 | 16000
      }
      turn_detection?: {
        type: 'server_vad' | 'semantic_vad'
        create_response?: boolean
        /** Only true: the caller can always interrupt. */
        interrupt_response?: boolean
        eagerness?: 'low' | 'medium' | 'high' | 'auto'
        silence_duration_ms?: number
        audio_output?: 'speaker' | 'headset' | 'unknown'
      } | null
    }
    output?: {
      format?: 'pcm16' | {
        type: 'audio/pcm'
        rate: 24000
      }
      voice?: 'elaine' | 'wenhui' | 'gwen' | 'henry' | 'kai' | 'marcus' | 'ren' | 'mei'
    }
  }
  tavia?: {
    languages?: Array<'en' | 'zh' | 'ms' | 'id'>
    tool_auto_continue?: boolean
    default_tool_effect?: 'read' | 'write'
    knowledge?: {
      mode: 'prompt' | 'rag' | 'shadow'
      kb_id?: string
      plugin?: string
      deadline_ms?: number
    } | null
    emergency?: {
      country: string
      number: string
    } | null
    bound?: string
    timezone?: string
    country?: 'SG' | 'MY' | 'ID' | 'PH' | 'TH' | 'VN' | 'HK' | 'TW' | 'CN' | 'IN' | 'JP' | 'AE' | 'GB' | 'NZ' | 'AU' | 'BR' | 'CA' | 'CL' | 'KZ' | 'MN' | 'MX' | 'RU' | 'US'
    holidays?: Array<{
      date: string
      name: string
      aliases?: Array<string>
    }>
    closures?: Array<{
      date: string
      name: string
      aliases?: Array<string>
    }>
    hours?: Array<{
      day: 'mon' | 'tue' | 'wed' | 'thu' | 'fri' | 'sat' | 'sun'
      open: string
      close: string
    }>
    guard?: {
      mode: 'off' | 'shadow' | 'enforce'
    }
    notes?: {
      forbid?: Array<'nric' | 'card' | 'phone' | 'email'>
      mask?: Array<'nric' | 'card' | 'phone' | 'email'>
    }
    voice_feedback?: {
      acks?: boolean
      backchannels?: boolean
      register?: 'professional' | 'casual'
    }
    events?: boolean
  }
}

export type SessionCreatedEvent = {
  type: 'session.created'
  event_id: string
  session: {
    type: 'realtime'
    object: string
    id: string | null
    instructions: string
    tools: Array<{
      [key: string]: unknown
    }>
    audio: {
      input: {
        [key: string]: unknown
      }
      output: {
        [key: string]: unknown
      }
      [key: string]: unknown
    }
    /** Tavia session fields: preset, languages, knowledge and the rest. */
    tavia: {
      [key: string]: unknown
    }
    [key: string]: unknown
  }
  [key: string]: unknown
}

export type SessionUpdatedEvent = {
  type: 'session.updated'
  event_id: string
  session: {
    type: 'realtime'
    object: string
    id: string | null
    instructions: string
    tools: Array<{
      [key: string]: unknown
    }>
    audio: {
      input: {
        [key: string]: unknown
      }
      output: {
        [key: string]: unknown
      }
      [key: string]: unknown
    }
    /** Tavia session fields: preset, languages, knowledge and the rest. */
    tavia: {
      [key: string]: unknown
    }
    [key: string]: unknown
  }
  [key: string]: unknown
}

export type SessionEndedEvent = {
  type: 'session.ended'
  event_id: string
  session_id: string
  duration_ms: number
  usage: {
    voice_seconds: number
    model_tokens_in: number
    model_tokens_out: number
    amount_micros: number
  }
  /** With the guard on: fires per rule in this call. */
  guard?: Record<string, unknown>
  /** With call notes on: the notes as the call ended. */
  notes?: Record<string, unknown>
  /** With async tools on: the task ledger as the call ended. */
  tasks?: Array<{
    id: string
    label: string
    kind: 'read' | 'write'
    state: 'running' | 'done' | 'failed' | 'not_confirmed' | 'timed_out' | 'superseded' | 'cancelled'
    age_ms: number
    /** The agent has given the caller its result. */
    told: boolean
    /** A short summary of the result, once in. */
    summary?: string
    /** Your latest task.status label while it runs. */
    status_label?: string
  }>
  [key: string]: unknown
}

export type ErrorEvent = {
  type: 'error'
  event_id: string
  error: {
    type: 'invalid_request_error' | 'server_error'
    code: string
    message: string
    event_id?: string
    issue?: string
    tool?: string
    param: string | null
    [key: string]: unknown
  }
  [key: string]: unknown
}

export type InputAudioBufferSpeechStartedEvent = {
  type: 'input_audio_buffer.speech_started'
  event_id: string
  audio_start_ms: number
  item_id: string
  [key: string]: unknown
}

export type InputAudioBufferSpeechStoppedEvent = {
  type: 'input_audio_buffer.speech_stopped'
  event_id: string
  audio_end_ms: number
  item_id: string
  [key: string]: unknown
}

export type InputAudioBufferCommittedEvent = {
  type: 'input_audio_buffer.committed'
  event_id: string
  item_id: string
  previous_item_id: null
  [key: string]: unknown
}

export type InputAudioBufferClearedEvent = {
  type: 'input_audio_buffer.cleared'
  event_id: string
  [key: string]: unknown
}

export type ConversationItemAddedEvent = {
  type: 'conversation.item.added'
  event_id: string
  item: {
    id: string
    type: string
    [key: string]: unknown
  }
  previous_item_id?: string | null
  [key: string]: unknown
}

export type ConversationItemDoneEvent = {
  type: 'conversation.item.done'
  event_id: string
  item: {
    id: string
    type: string
    [key: string]: unknown
  }
  [key: string]: unknown
}

export type ConversationItemTruncatedEvent = {
  type: 'conversation.item.truncated'
  event_id: string
  item_id: string
  content_index: number
  audio_end_ms: number
  [key: string]: unknown
}

export type ConversationItemInputAudioTranscriptionDeltaEvent = {
  type: 'conversation.item.input_audio_transcription.delta'
  event_id: string
  item_id: string
  content_index: number
  /** Text appended since the previous partial when the new partial extends it, else empty. */
  delta: string
  /** The whole current caller partial; a later partial may revise it. */
  transcript: string
  [key: string]: unknown
}

export type ConversationItemInputAudioTranscriptionCompletedEvent = {
  type: 'conversation.item.input_audio_transcription.completed'
  event_id: string
  item_id: string
  content_index: number
  transcript: string
  /** Hesitations (um, uh) the caller made in this turn, in order. Absent when there were none; never in transcript. */
  fillers?: Array<{
    /** How many of the turn's words came before it (each CJK character is one word). */
    before: number
    /** How long the hesitation lasted. */
    duration_ms: number
    [key: string]: unknown
  }>
  usage?: {
    type: 'duration'
    seconds: number
  }
  [key: string]: unknown
}

export type ResponseCreatedEvent = {
  type: 'response.created'
  event_id: string
  /** metadata.turn_id names the caller turn this reply answers; metadata.kind marks a filler or backchannel. */
  response: {
    id: string
    metadata?: {
      kind?: 'filler' | 'backchannel'
      /** The caller turn this reply answers: the turn_id on its turn.tool and turn.timing events. Absent when it answers no caller turn (a greeting, a holding line); those events then carry the response id as turn_id. */
      turn_id?: string | null
      [key: string]: unknown
    }
    [key: string]: unknown
  }
  [key: string]: unknown
}

export type ResponseDoneEvent = {
  type: 'response.done'
  event_id: string
  response: {
    id: string
    object: string
    status: string
    output: Array<{
      [key: string]: unknown
    }>
    metadata?: {
      kind?: 'filler' | 'backchannel'
      /** The caller turn this reply answers: the turn_id on its turn.tool and turn.timing events. Absent when it answers no caller turn (a greeting, a holding line); those events then carry the response id as turn_id. */
      turn_id?: string | null
      [key: string]: unknown
    }
    [key: string]: unknown
  }
  [key: string]: unknown
}

export type ResponseOutputAudioDeltaEvent = {
  type: 'response.output_audio.delta'
  event_id: string
  response_id: string
  item_id: string
  output_index: number
  content_index: number
  delta: string
  [key: string]: unknown
}

export type ResponseOutputAudioDoneEvent = {
  type: 'response.output_audio.done'
  event_id: string
  response_id: string
  item_id: string
  output_index: number
  content_index: number
  [key: string]: unknown
}

export type ResponseOutputAudioTranscriptDeltaEvent = {
  type: 'response.output_audio_transcript.delta'
  event_id: string
  response_id: string
  item_id: string
  output_index: number
  content_index: number
  delta: string
  /** Offset of this clause in the reply audio. */
  audio_start_ms: number
  [key: string]: unknown
}

export type ResponseOutputAudioTranscriptDoneEvent = {
  type: 'response.output_audio_transcript.done'
  event_id: string
  response_id: string
  item_id: string
  output_index: number
  content_index: number
  transcript: string
  [key: string]: unknown
}

export type ResponseContentPartAddedEvent = {
  type: 'response.content_part.added'
  event_id: string
  response_id: string
  item_id: string
  output_index: number
  content_index: number
  part: {
    type: 'audio'
    transcript: string
  }
  [key: string]: unknown
}

export type ResponseContentPartDoneEvent = {
  type: 'response.content_part.done'
  event_id: string
  response_id: string
  item_id: string
  output_index: number
  content_index: number
  part: {
    type: 'audio'
    transcript: string
  }
  [key: string]: unknown
}

export type ResponseFunctionCallArgumentsDeltaEvent = {
  type: 'response.function_call_arguments.delta'
  event_id: string
  response_id: string
  output_index: number
  item_id: string
  call_id: string
  delta: string
  [key: string]: unknown
}

export type ResponseFunctionCallArgumentsDoneEvent = {
  type: 'response.function_call_arguments.done'
  event_id: string
  response_id: string
  output_index: number
  item_id: string
  call_id: string
  name: string
  arguments: string
  [key: string]: unknown
}

export type ResponseOutputItemAddedEvent = {
  type: 'response.output_item.added'
  event_id: string
  response_id: string
  output_index: number
  item: {
    id: string
    type: string
    [key: string]: unknown
  }
  [key: string]: unknown
}

export type ResponseOutputItemDoneEvent = {
  type: 'response.output_item.done'
  event_id: string
  response_id: string
  output_index: number
  item: {
    id: string
    type: string
    [key: string]: unknown
  }
  [key: string]: unknown
}

export type TurnTimingEvent = {
  type: 'turn.timing'
  event_id: string
  turn_id: string
  mark: 'heard' | 'speech_start' | 'end_of_turn' | 'barge_in' | 'reply_start' | 'first_audio' | 'speech_end' | 'stt_final' | 'model_request' | 'first_token' | 'first_clause' | 'tts_request' | 'ack_audio'
  at_ms: number
  from_end_of_turn_ms: number | null
  /** end_of_turn with the turn model on or in shadow: what ended the turn (the model or the silence rule). */
  by?: 'model' | 'fallback'
  /** end_of_turn with the turn model: its end-of-turn score then. */
  p_eot?: number | null
  [key: string]: unknown
}

export type TurnBackchannelEvent = {
  type: 'turn.backchannel'
  event_id: string
  turn_id: string
  transcript: string
  at_ms: number
  [key: string]: unknown
}

export type TurnToolEvent = {
  type: 'turn.tool'
  event_id: string
  turn_id: string
  call_id: string
  name: string
  arguments: string
  output: string
  at_ms: number
  duration_ms?: number
  runs?: 'client' | 'webhook' | 'demo' | 'platform'
  /** A write: the caller item whose yes to the read-back allowed it. */
  confirmed_by?: string
  [key: string]: unknown
}

export type TurnWarningEvent = {
  type: 'turn.warning'
  event_id: string
  turn_id: string | null
  code: 'speech_clause_dropped' | 'speech_backup_voice' | 'tool_call_refused' | 'tool_timeout' | 'tool_effect_defaulted' | 'reply_retried' | 'unbacked_value_blocked' | 'knowledge_unavailable' | 'knowledge_late' | 'claim_held' | 'lang_mismatch' | 'reply_cut' | 'emergency_rendered' | 'not_allowed_now' | 'emergency_unconfigured_country'
  reason?: string
  message: string
  at_ms: number
  /** The tool a tool warning is about. */
  tool?: string
  /** Why, in words: the refusal details. */
  detail?: string
  [key: string]: unknown
}

export type TurnKnowledgeEvent = {
  type: 'turn.knowledge'
  event_id: string
  turn_id: string
  mode: 'prompt' | 'rag' | 'shadow'
  status: 'prompt' | 'skipped' | 'empty' | 'warm' | 'appended' | 'rebuilt' | 'cold' | 'prefetched' | 'pending' | 'injected' | 'unavailable' | 'unsure'
  passages: Array<{
    /** The passage label in the block the agent saw (K1, K2 ...); never spoken. */
    ref: string
    /** Your passage id. */
    id: string
    score: number | null
    [key: string]: unknown
  }>
  cited: Array<{
    ref: string
    id: string
    /** Spoken values this passage backed. */
    values: Array<string>
    [key: string]: unknown
  }>
  searches: number
  prewarms: number
  prewarm_tokens: number
  /** Wait for the end-of-turn search; null when none ran. */
  final_check_ms: number | null
  /** Time the knowledge step added after the end of turn. */
  added_ms: number
  at_ms: number
  [key: string]: unknown
}

export type TurnGuardEvent = {
  type: 'turn.guard'
  event_id: string
  turn_id: string
  response_id: string
  mode: 'shadow' | 'enforce'
  fires: Array<{
    rule: 'write' | 'claim' | 'fact' | 'name' | 'emergency' | 'lang' | 'length' | 'scope'
    code: string
    action: string
    [key: string]: unknown
  }>
  clauses: number
  calls: number
  /** Time the clause and call checks took in this reply. */
  gate_ms: number
  [key: string]: unknown
}

export type NotesUpdatedEvent = {
  type: 'notes.updated'
  event_id: string
  turn_id: string
  notes: Record<string, unknown>
  /** Keys set or overwritten. */
  set: Array<string>
  /** Keys deleted by the agent or evicted over the cap. */
  removed: Array<string>
  at_ms: number
  [key: string]: unknown
}

export type ToolStartedEvent = {
  type: 'tool.started'
  event_id: string
  turn_id: string
  call_id: string
  name: string
  /** A booking or change: never superseded. */
  write: boolean
  at_ms: number
  [key: string]: unknown
}

export type ToolResultEvent = {
  type: 'tool.result'
  event_id: string
  turn_id: string
  call_id: string
  name: string
  status: 'ok' | 'error' | 'timeout' | 'late' | 'superseded' | 'cancelled'
  output: string
  at_ms: number
  duration_ms: number
  [key: string]: unknown
}

export type TasksUpdatedEvent = {
  type: 'tasks.updated'
  event_id: string
  /** The whole ledger after the change, oldest first. */
  tasks: Array<{
    id: string
    label: string
    kind: 'read' | 'write'
    state: 'running' | 'done' | 'failed' | 'not_confirmed' | 'timed_out' | 'superseded' | 'cancelled'
    age_ms: number
    /** The agent has given the caller its result. */
    told: boolean
    /** A short summary of the result, once in. */
    summary?: string
    /** Your latest task.status label while it runs. */
    status_label?: string
  }>
  at_ms: number
  [key: string]: unknown
}

export type ResultDeliveredEvent = {
  type: 'result.delivered'
  event_id: string
  turn_id: string
  /** The reply that spoke the result. */
  response_id: string
  call_id: string
  name: string
  at_ms: number
  /** From the result landing to the reply that spoke it completing. */
  wait_ms: number
  [key: string]: unknown
}

export type TurnInterruptedEvent = {
  type: 'turn.interrupted'
  event_id: string
  turn_id: string
  response_id: string
  item_id: string
  audio_end_ms: number
  heard_text: string
  [key: string]: unknown
}

export type ServerEvent = SessionCreatedEvent | SessionUpdatedEvent | SessionEndedEvent | ErrorEvent | InputAudioBufferSpeechStartedEvent | InputAudioBufferSpeechStoppedEvent | InputAudioBufferCommittedEvent | InputAudioBufferClearedEvent | ConversationItemAddedEvent | ConversationItemDoneEvent | ConversationItemTruncatedEvent | ConversationItemInputAudioTranscriptionDeltaEvent | ConversationItemInputAudioTranscriptionCompletedEvent | ResponseCreatedEvent | ResponseDoneEvent | ResponseOutputAudioDeltaEvent | ResponseOutputAudioDoneEvent | ResponseOutputAudioTranscriptDeltaEvent | ResponseOutputAudioTranscriptDoneEvent | ResponseContentPartAddedEvent | ResponseContentPartDoneEvent | ResponseFunctionCallArgumentsDeltaEvent | ResponseFunctionCallArgumentsDoneEvent | ResponseOutputItemAddedEvent | ResponseOutputItemDoneEvent | TurnTimingEvent | TurnBackchannelEvent | TurnToolEvent | TurnWarningEvent | TurnKnowledgeEvent | TurnGuardEvent | NotesUpdatedEvent | ToolStartedEvent | ToolResultEvent | TasksUpdatedEvent | ResultDeliveredEvent | TurnInterruptedEvent

export interface ServerEventMap {
  'session.created': SessionCreatedEvent
  'session.updated': SessionUpdatedEvent
  'session.ended': SessionEndedEvent
  'error': ErrorEvent
  'input_audio_buffer.speech_started': InputAudioBufferSpeechStartedEvent
  'input_audio_buffer.speech_stopped': InputAudioBufferSpeechStoppedEvent
  'input_audio_buffer.committed': InputAudioBufferCommittedEvent
  'input_audio_buffer.cleared': InputAudioBufferClearedEvent
  'conversation.item.added': ConversationItemAddedEvent
  'conversation.item.done': ConversationItemDoneEvent
  'conversation.item.truncated': ConversationItemTruncatedEvent
  'conversation.item.input_audio_transcription.delta': ConversationItemInputAudioTranscriptionDeltaEvent
  'conversation.item.input_audio_transcription.completed': ConversationItemInputAudioTranscriptionCompletedEvent
  'response.created': ResponseCreatedEvent
  'response.done': ResponseDoneEvent
  'response.output_audio.delta': ResponseOutputAudioDeltaEvent
  'response.output_audio.done': ResponseOutputAudioDoneEvent
  'response.output_audio_transcript.delta': ResponseOutputAudioTranscriptDeltaEvent
  'response.output_audio_transcript.done': ResponseOutputAudioTranscriptDoneEvent
  'response.content_part.added': ResponseContentPartAddedEvent
  'response.content_part.done': ResponseContentPartDoneEvent
  'response.function_call_arguments.delta': ResponseFunctionCallArgumentsDeltaEvent
  'response.function_call_arguments.done': ResponseFunctionCallArgumentsDoneEvent
  'response.output_item.added': ResponseOutputItemAddedEvent
  'response.output_item.done': ResponseOutputItemDoneEvent
  'turn.timing': TurnTimingEvent
  'turn.backchannel': TurnBackchannelEvent
  'turn.tool': TurnToolEvent
  'turn.warning': TurnWarningEvent
  'turn.knowledge': TurnKnowledgeEvent
  'turn.guard': TurnGuardEvent
  'notes.updated': NotesUpdatedEvent
  'tool.started': ToolStartedEvent
  'tool.result': ToolResultEvent
  'tasks.updated': TasksUpdatedEvent
  'result.delivered': ResultDeliveredEvent
  'turn.interrupted': TurnInterruptedEvent
}

/** @deprecated Renamed: use ResponseOutputAudioDeltaEvent ('response.output_audio.delta'). */
export type ResponseAudioDeltaEvent = ResponseOutputAudioDeltaEvent

/** @deprecated Renamed: use ResponseOutputAudioDoneEvent ('response.output_audio.done'). */
export type ResponseAudioDoneEvent = ResponseOutputAudioDoneEvent

/** @deprecated Renamed: use ResponseOutputAudioTranscriptDeltaEvent ('response.output_audio_transcript.delta'). */
export type ResponseAudioTranscriptDeltaEvent = ResponseOutputAudioTranscriptDeltaEvent

/** @deprecated Renamed: use ResponseOutputAudioTranscriptDoneEvent ('response.output_audio_transcript.done'). */
export type ResponseAudioTranscriptDoneEvent = ResponseOutputAudioTranscriptDoneEvent

export type SessionUpdateEvent = {
  type: 'session.update'
  event_id?: string
  session: {
    type?: 'realtime'
    instructions?: string
    tools?: Array<{
      type: 'function'
      name: string
      description?: string
      parameters?: Record<string, unknown>
      'x-effect'?: 'read' | 'write'
      'x-action'?: 'create' | 'cancel' | 'change' | 'send' | 'transfer' | 'log'
    }>
    audio?: {
      input?: {
        format?: 'pcm16' | {
          type: 'audio/pcm'
          rate: 24000 | 16000
        }
        turn_detection?: {
          type: 'server_vad' | 'semantic_vad'
          create_response?: boolean
          /** Only true: the caller can always interrupt. */
          interrupt_response?: boolean
          eagerness?: 'low' | 'medium' | 'high' | 'auto'
          silence_duration_ms?: number
          audio_output?: 'speaker' | 'headset' | 'unknown'
        } | null
      }
      output?: {
        format?: 'pcm16' | {
          type: 'audio/pcm'
          rate: 24000
        }
        voice?: 'elaine' | 'wenhui' | 'gwen' | 'henry' | 'kai' | 'marcus' | 'ren' | 'mei'
      }
    }
    tavia?: {
      languages?: Array<'en' | 'zh' | 'ms' | 'id'>
      tool_auto_continue?: boolean
      default_tool_effect?: 'read' | 'write'
      knowledge?: {
        mode: 'prompt' | 'rag' | 'shadow'
        kb_id?: string
        plugin?: string
        deadline_ms?: number
      } | null
      emergency?: {
        country: string
        number: string
      } | null
      bound?: string
      timezone?: string
      country?: 'SG' | 'MY' | 'ID' | 'PH' | 'TH' | 'VN' | 'HK' | 'TW' | 'CN' | 'IN' | 'JP' | 'AE' | 'GB' | 'NZ' | 'AU' | 'BR' | 'CA' | 'CL' | 'KZ' | 'MN' | 'MX' | 'RU' | 'US'
      holidays?: Array<{
        date: string
        name: string
        aliases?: Array<string>
      }>
      closures?: Array<{
        date: string
        name: string
        aliases?: Array<string>
      }>
      hours?: Array<{
        day: 'mon' | 'tue' | 'wed' | 'thu' | 'fri' | 'sat' | 'sun'
        open: string
        close: string
      }>
      guard?: {
        mode: 'off' | 'shadow' | 'enforce'
      }
      notes?: {
        forbid?: Array<'nric' | 'card' | 'phone' | 'email'>
        mask?: Array<'nric' | 'card' | 'phone' | 'email'>
      }
      voice_feedback?: {
        acks?: boolean
        backchannels?: boolean
        register?: 'professional' | 'casual'
      }
      events?: boolean
    }
  }
}

export type InputAudioBufferAppendEvent = {
  type: 'input_audio_buffer.append'
  event_id?: string
  audio: string
}

export type ConversationItemCreateEvent = {
  type: 'conversation.item.create'
  event_id?: string
  item: {
    type: 'message'
    role: 'user' | 'system'
    content: Array<{
      type: 'input_text'
      text: string
    }>
  } | {
    type: 'function_call_output'
    call_id: string
    output: string
  }
}

export type ConversationItemTruncateEvent = {
  type: 'conversation.item.truncate'
  event_id?: string
  item_id: string
  content_index: 0
  audio_end_ms: number
}

export type ResponseCreateEvent = {
  type: 'response.create'
  event_id?: string
  response?: {
    instructions?: string
    metadata?: Record<string, unknown>
    conversation?: 'auto'
    output_modalities?: Array<unknown>
    tool_choice?: 'auto'
  }
}

export type InputAudioBufferCommitEvent = {
  type: 'input_audio_buffer.commit'
  event_id?: string
}

export type InputAudioBufferClearEvent = {
  type: 'input_audio_buffer.clear'
  event_id?: string
}

export type ResponseCancelEvent = {
  type: 'response.cancel'
  event_id?: string
}

export type TaskStatusEvent = {
  type: 'task.status'
  event_id?: string
  call_id: string
  label: string
}

export type ClientEvent = SessionUpdateEvent | InputAudioBufferAppendEvent | ConversationItemCreateEvent | ConversationItemTruncateEvent | ResponseCreateEvent | InputAudioBufferCommitEvent | InputAudioBufferClearEvent | ResponseCancelEvent | TaskStatusEvent

export interface ClientEventMap {
  'session.update': SessionUpdateEvent
  'input_audio_buffer.append': InputAudioBufferAppendEvent
  'conversation.item.create': ConversationItemCreateEvent
  'conversation.item.truncate': ConversationItemTruncateEvent
  'response.create': ResponseCreateEvent
  'input_audio_buffer.commit': InputAudioBufferCommitEvent
  'input_audio_buffer.clear': InputAudioBufferClearEvent
  'response.cancel': ResponseCancelEvent
  'task.status': TaskStatusEvent
}
