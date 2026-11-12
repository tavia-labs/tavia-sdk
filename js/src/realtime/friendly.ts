import { FRIENDLY_EVENTS, type FriendlyName, type WarningCode } from '../generated/spec.ts'
import type { ServerEvent, ServerEventMap, TurnTimingEvent, Usage } from '../generated/types.ts'

/** A turn's phase. End of turn and first audio are not phases: they arrive as `timing` events. */
export type TurnPhase = 'speech_started' | 'speech_stopped' | 'reply_start'

/** The data each friendly event carries, by event name (see {@link Call.on}). */
export type FriendlyData = {
  /** Caller partials carry the whole current partial, which may revise the previous one; agent partials are clauses. */
  transcript: { role: 'caller' | 'agent', text: string, final: boolean, audio_start_ms?: number }
  /** A turn phase; on reply_start, `turn_id` is the caller turn the reply answers, as on its tool_call and timing events. */
  turn: { phase: TurnPhase, turn_id?: string }
  /** The caller talked over the agent: what they heard of the reply, and where it stopped. */
  interruption: { heard_text: string, audio_end_ms: number }
  /** A short acknowledgement from the caller, such as "uh-huh", that did not take the turn. */
  backchannel: { text: string }
  /** A tool the agent ran, with its arguments and output (both JSON text). */
  tool_call: { turn_id?: string, name: string, arguments: string, output: string, duration_ms?: number }
  /** Latency marks for a turn. */
  timing: Omit<TurnTimingEvent, 'type' | 'event_id'>
  /** Something the server noticed that did not stop the session. */
  warning: { turn_id: string | null, code: WarningCode, message: string }
  /** An error the server reported; the session goes on unless the socket closes. */
  error: { code: string, message: string }
  /** A chunk of the agent's audio: base64 PCM16 mono at the output rate. */
  audio: { pcm: string }
  /** The session ended: its id, length and usage. Sent once. */
  ended: { session_id: string, duration_ms: number, usage: Usage }
}

/** Every friendly event name. */
export const FRIENDLY_NAMES = [...new Set(Object.values(FRIENDLY_EVENTS))] as FriendlyName[]

type Mapped = keyof typeof FRIENDLY_EVENTS
type Mappers = { [T in Mapped]: (e: ServerEventMap[T]) => FriendlyData[(typeof FRIENDLY_EVENTS)[T]] }

const caller = (text: string, final: boolean): FriendlyData['transcript'] => ({ role: 'caller', text, final })

// One mapper per server event type that has a friendly event.
const MAPPERS: Mappers = {
  'conversation.item.input_audio_transcription.delta': (e) => caller(e.transcript, false),
  'conversation.item.input_audio_transcription.completed': (e) => caller(e.transcript, true),
  'response.output_audio_transcript.delta': (e) => ({ role: 'agent', text: e.delta, final: false, audio_start_ms: e.audio_start_ms }),
  'response.output_audio_transcript.done': (e) => ({ role: 'agent', text: e.transcript, final: true }),
  'input_audio_buffer.speech_started': () => ({ phase: 'speech_started' }),
  'input_audio_buffer.speech_stopped': () => ({ phase: 'speech_stopped' }),
  'response.created': (e) => {
    const turnId = e.response.metadata?.turn_id
    return turnId ? { phase: 'reply_start', turn_id: turnId } : { phase: 'reply_start' }
  },
  'turn.interrupted': (e) => ({ heard_text: e.heard_text, audio_end_ms: e.audio_end_ms }),
  'turn.backchannel': (e) => ({ text: e.transcript }),
  'turn.tool': (e) => ({
    turn_id: e.turn_id, name: e.name, arguments: e.arguments, output: e.output,
    ...(e.duration_ms === undefined ? {} : { duration_ms: e.duration_ms }),
  }),
  'turn.timing': ({ type: _t, event_id: _id, ...rest }) => rest,
  'turn.warning': (e) => ({ turn_id: e.turn_id, code: e.code, message: e.message }),
  error: (e) => ({ code: e.error.code, message: e.error.message }),
  'response.output_audio.delta': (e) => ({ pcm: e.delta }),
  'session.ended': (e) => ({ session_id: e.session_id, duration_ms: e.duration_ms, usage: e.usage }),
}

/** A friendly event: its name and data. */
export type FriendlyEvent = { [N in FriendlyName]: { name: N, data: FriendlyData[N] } }[FriendlyName]

/** The friendly event for a server event, or null when it has none. */
export function toFriendly(e: ServerEvent): FriendlyEvent | null {
  if (!Object.hasOwn(MAPPERS, e.type)) return null
  const type = e.type as Mapped
  const map = MAPPERS[type] as (ev: ServerEvent) => FriendlyEvent['data']
  return { name: FRIENDLY_EVENTS[type], data: map(e) } as FriendlyEvent
}
