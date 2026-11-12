import { base64ToPcm16, pcm16ToBase64 } from '../audio/pcm.ts'
import type { Player } from '../audio/player.ts'
import { SessionClosedError, TOOL_FAILED, ToolError, errorForClose, errorForCode, type TaviaError } from '../errors.ts'
import { DIALECT, LIMITS, SERVER_EVENT_TYPES, SESSION_OPTIONS, type FriendlyName } from '../generated/spec.ts'
import type { ClientEvent, ServerEvent, ServerEventMap, SessionConfig } from '../generated/types.ts'
import { sendOpen, type SocketLike } from '../transport/socket.ts'
import { standardEvent, standardType, wireSession, type Dialect, type RenamedEventType } from './dialect.ts'
import { Emitter } from './emitter.ts'
import { toFriendly, type FriendlyData } from './friendly.ts'

export type { SocketLike } from '../transport/socket.ts'

const MAX_AUDIO_BYTES = LIMITS['realtime.maxAudioBytes']
const OUT_SAMPLES_PER_MS = LIMITS['realtime.outputRates'][0] / 1000
const KNOWN_OPTIONS = new Set<string>(SESSION_OPTIONS)
const SERVER_TYPES = new Set<string>(SERVER_EVENT_TYPES)

/** Every server event type, for {@link Call.onEvent}. */
export type ServerEventType = keyof ServerEventMap
/** Who a text message is from: the caller (`user`) or an instruction to the agent (`system`). */
export type MessageRole = 'user' | 'system'
/** Runs a client tool: gets the parsed arguments, returns (or resolves to) the output sent to the agent. */
export type ToolHandler = (args: Record<string, unknown>) => unknown

/** Options for a {@link Call} built on an open socket. */
export interface CallOptions {
  /** Plays the agent's audio as it arrives; `interrupt()` then also stops it at the point the caller heard. */
  player?: Player
  /** The wire dialect the socket was opened with (`ga` unless the URL asked for `beta`). */
  dialect?: Dialect
}

/** Options for {@link Call.tool}. */
export interface ToolOptions {
  /** Send any exception's message to the agent; off by default, since it may hold internals. */
  exposeErrors?: boolean
}

type FriendlyEvents = { [N in FriendlyName]: [FriendlyData[N]] }
type CallEvents = FriendlyEvents & { raw: [ServerEvent | null, string], close: [number], failure: [TaviaError] }
type WireEvents = { [T in ServerEventType]: [ServerEventMap[T]] }

// The reply audio item now playing and where it starts in the player's timeline, to truncate it on interrupt.
interface Playing { itemId: string, startMs: number }

const asBytes = (pcm: Int16Array | Uint8Array): Uint8Array =>
  pcm instanceof Uint8Array ? pcm : new Uint8Array(pcm.buffer, pcm.byteOffset, pcm.byteLength)

const outputText = (output: unknown): string => (typeof output === 'string' ? output : JSON.stringify(output ?? null))

// Null for anything that is not JSON or not a known event type: those go to onRaw only.
function parse(raw: string): ServerEvent | null {
  try {
    const value = JSON.parse(raw) as { type?: unknown } | null
    if (typeof value?.type !== 'string') return null
    const event = standardEvent(value as { type: string })
    return SERVER_TYPES.has(event.type) ? event as ServerEvent : null
  } catch {
    return null
  }
}

function toolErrorText(name: string, err: unknown, expose: boolean): string {
  if (err instanceof ToolError) return err.message
  console.error(`tavia: tool ${name} failed`, err)
  return expose ? (err instanceof Error ? err.message : String(err)) : TOOL_FAILED
}

/**
 * One realtime session: typed events out; session updates, audio, text, tool outputs and interrupts in.
 * Get one from `tavia.realtime.connect`. Every send throws SessionClosedError once the socket has closed.
 *
 * @example
 * const call = await tavia.realtime.connect({ session: { voice: 'elaine', instructions: 'Be brief.' } })
 * call.on('transcript', (t) => { if (t.final) showLine(t.role, t.text) })
 * call.tool('find_order', async ({ order_id }) => ({ status: 'shipped', order_id }))
 * const mic = await openMic({ sampleRate: 24000 })
 * mic.onFrame((pcm) => call.sendAudio(pcm))
 */
export class Call {
  private readonly events = new Emitter<CallEvents>()
  private readonly wire = new Emitter<WireEvents>()
  private readonly tools = new Map<string, { handler: ToolHandler, exposeErrors: boolean }>()
  private queuedMs = 0
  private playing: Playing | null = null
  private ended = false
  private eventsAsked = false
  /** The socket's close code, once it has closed. */
  closeCode: number | null = null
  /** The error the close reports, or null for a normal close or while still open. */
  closeError: TaviaError | null = null

  /** Wraps an open socket; most apps get a Call from `tavia.realtime.connect` instead. */
  constructor(private readonly socket: SocketLike, private readonly opts: CallOptions = {}) {
    socket.onmessage = (m) => { if (typeof m.data === 'string') this.receive(m.data) }
    socket.onclose = (e) => this.finish(e.code)
  }

  /** Listens for a friendly event, such as `transcript`, `turn` or `ended`; returns a function that stops listening. */
  on<N extends FriendlyName>(name: N, cb: (data: FriendlyData[N]) => void): () => void {
    return this.events.on(name, cb as (...args: CallEvents[N]) => void)
  }

  /** @deprecated This event was renamed: subscribe to its standard name (see `DIALECT.renames`). */
  onEvent<T extends RenamedEventType>(type: T, cb: (event: ServerEventMap[(typeof DIALECT.renames)[T]]) => void): () => void
  /** Listens for one server event type, as sent on the wire; returns a function that stops listening. */
  onEvent<T extends ServerEventType>(type: T, cb: (event: ServerEventMap[T]) => void): () => void
  onEvent(type: string, cb: (event: never) => void): () => void {
    const standard = standardType(type)
    if (standard !== type) console.warn(`tavia: the '${type}' event is now '${standard}'; subscribe to the new name`)
    return this.wire.on(standard as ServerEventType, cb as (...args: WireEvents[ServerEventType]) => void)
  }

  /** Every message, parsed or not; unknown ones arrive as null with the raw text. */
  onRaw(cb: (event: ServerEvent | null, raw: string) => void): () => void {
    return this.events.on('raw', cb)
  }

  /** Each `error` event as a typed error; the session goes on unless the socket closes. */
  onError(cb: (err: TaviaError) => void): () => void {
    return this.events.on('failure', cb)
  }

  /** Called once when the socket closes, with its close code. */
  onClose(cb: (code: number) => void): () => void {
    return this.events.on('close', cb)
  }

  /** Changes session options mid-call. Throws a TypeError naming any unknown option. */
  update(session: Partial<SessionConfig>): void {
    const unknown = Object.keys(session).filter((k) => !KNOWN_OPTIONS.has(k))
    if (unknown.length) throw new TypeError(`unknown session option: ${unknown.join(', ')}`)
    if (this.opts.dialect === 'beta') {
      sendOpen(this.socket, JSON.stringify({ type: 'session.update', session }), this.closeCode)
      return
    }
    this.send({ type: 'session.update', session: wireSession(session, !this.eventsAsked) })
    this.eventsAsked = true
  }

  /** Sends caller audio: PCM16 mono at the session's input rate, split so no event passes the server's size limit. */
  sendAudio(pcm: Int16Array | Uint8Array): void {
    const bytes = asBytes(pcm)
    for (let at = 0; at < bytes.length; at += MAX_AUDIO_BYTES) {
      const chunk = bytes.slice(at, at + MAX_AUDIO_BYTES)
      this.send({ type: 'input_audio_buffer.append', audio: pcm16ToBase64(new Int16Array(chunk.buffer, 0, chunk.length >> 1)) })
    }
  }

  /** Adds a text message to the conversation; call {@link Call.createResponse} for a reply to it. */
  sendText(text: string, role: MessageRole = 'user'): void {
    this.send({ type: 'conversation.item.create', item: { type: 'message', role, content: [{ type: 'input_text', text }] } })
  }

  /** A client-run tool's result. The reply goes on by itself unless the session set tool_auto_continue false. */
  sendToolOutput(callId: string, output: unknown): void {
    this.send({ type: 'conversation.item.create', item: { type: 'function_call_output', call_id: callId, output: outputText(output) } })
  }

  /** A deferred tool's short status while it runs (async tools), e.g. 'checking stock'; send the output when done. */
  sendTaskStatus(callId: string, label: string): void {
    this.send({ type: 'task.status', call_id: callId, label })
  }

  /** Tells the server the caller heard only the first `audioEndMs` ms of a reply item. */
  truncate(itemId: string, audioEndMs: number): void {
    this.send({ type: 'conversation.item.truncate', item_id: itemId, content_index: 0, audio_end_ms: Math.max(0, Math.round(audioEndMs)) })
  }

  /** Asks the agent to reply now. */
  createResponse(): void {
    this.send({ type: 'response.create' })
  }

  /** Cancels the reply in progress, without stopping local playback (see {@link Call.interrupt}). */
  cancelResponse(): void {
    this.send({ type: 'response.cancel' })
  }

  /** Ends the caller turn now; with turn_detection null (push-to-talk), then call createResponse. */
  commitAudio(): void {
    this.send({ type: 'input_audio_buffer.commit' })
  }

  /** Drops the caller audio sent since the last turn. */
  clearAudio(): void {
    this.send({ type: 'input_audio_buffer.clear' })
  }

  /**
   * Runs `handler` for every call of tool `name` and sends its result. A ToolError's message goes to the agent;
   * any other throw is logged and sent as "tool_failed" unless exposeErrors is set. Returns a function that removes it.
   */
  tool(name: string, handler: ToolHandler, opts: ToolOptions = {}): () => void {
    const entry = { handler, exposeErrors: opts.exposeErrors === true }
    this.tools.set(name, entry)
    return () => { if (this.tools.get(name) === entry) this.tools.delete(name) }
  }

  /** Stops the reply now: cancel it, stop playback, and tell the server how much of the item the caller heard. */
  interrupt(): void {
    this.cancelResponse()
    const player = this.opts.player
    if (!player) return
    if (this.playing && player.playedMs() < this.queuedMs) this.truncate(this.playing.itemId, player.playedMs() - this.playing.startMs)
    this.flushPlayer()
  }

  /** Ends the session. */
  close(): void {
    this.socket.close()
  }

  private send(event: ClientEvent): void {
    sendOpen(this.socket, JSON.stringify(event), this.closeCode)
  }

  private receive(raw: string): void {
    const event = parse(raw)
    this.events.emit('raw', event, raw)
    if (!event) return
    this.wire.emit(event.type, event as never)
    this.handle(event)
    const friendly = toFriendly(event)
    if (!friendly) return
    if (friendly.name === 'ended') {
      if (this.ended) return
      this.ended = true
    }
    this.events.emit(friendly.name, friendly.data as never)
  }

  private handle(event: ServerEvent): void {
    if (event.type === 'response.output_audio.delta') this.play(event.item_id, event.delta)
    else if (event.type === 'turn.interrupted') this.flushPlayer()
    else if (event.type === 'error') this.events.emit('failure', errorForCode(event.error.code, event.error.message))
    else if (event.type === 'response.function_call_arguments.done') void this.runTool(event.name, event.call_id, event.arguments)
  }

  private play(itemId: string, b64: string): void {
    const player = this.opts.player
    if (!player) return
    const now = Math.max(this.queuedMs, player.playedMs())
    if (this.playing?.itemId !== itemId) this.playing = { itemId, startMs: now }
    const pcm = base64ToPcm16(b64)
    this.queuedMs = now + pcm.length / OUT_SAMPLES_PER_MS
    player.enqueue(pcm)
  }

  private flushPlayer(): void {
    this.opts.player?.flush()
    this.queuedMs = this.opts.player?.playedMs() ?? 0
    this.playing = null
  }

  private async runTool(name: string, callId: string, args: string): Promise<void> {
    const tool = this.tools.get(name)
    if (!tool) return
    let output: unknown
    try {
      output = await tool.handler(JSON.parse(args || '{}') as Record<string, unknown>)
    } catch (err) {
      output = { error: toolErrorText(name, err, tool.exposeErrors) }
    }
    try {
      this.sendToolOutput(callId, output)
    } catch (err) {
      if (!(err instanceof SessionClosedError)) throw err
      console.warn(`tavia: tool ${name} output not sent: ${err.message}`)
    }
  }

  private finish(code: number): void {
    if (this.closeCode !== null) return
    this.closeCode = code
    this.closeError = errorForClose(code)
    this.flushPlayer()
    this.events.emit('close', code)
  }
}
