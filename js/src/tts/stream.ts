import { SessionClosedError, errorForClose, errorForCode, type TaviaError } from '../errors.ts'
import { LAYERS, LIMITS, SURFACE, TTS_STYLES, type Language, type TtsStyle } from '../generated/spec.ts'
import { Emitter } from '../realtime/emitter.ts'
import { openSocket, sendOpen, toBytes, type Auth, type SocketFactory, type SocketLike } from '../transport/socket.ts'
import { DEFAULT_URLS } from '../transport/urls.ts'

/** The text-to-speech stream endpoint on the public API. */
export const TTS_STREAM_URL = DEFAULT_URLS.ttsStream
const HEADER_BYTES = SURFACE.tts.headerBytes
const CONTEXT_ID = new RegExp(LIMITS['ttsStream.contextIdRegex'])
const STYLES = new Set<string>(TTS_STYLES)

/** Why a speak stopped early (`length`, `cap`, `timeout` or `cancelled`), or null when it finished normally. */
export type TtsStopped = (typeof SURFACE.tts.stopped)[number] | null

/** One piece of text to speak, for {@link TtsStream.speak}. */
export interface SpeakOptions {
  /** The context (one reply) this text belongs to; a short id the API accepts, or a TypeError is thrown. */
  context_id: string
  /** The text to speak. */
  text: string
  /** The text's language. */
  lang: Language
  /** An optional speaking style; an unknown style throws a TypeError. */
  style?: TtsStyle
}

/** A chunk of PCM16 mono audio for one context. */
export interface TtsAudio { context_id: string, pcm: Int16Array }
/** One per speak, in order: its audio length in seconds, time to first audio in ms, and why it stopped early, if it did. */
export interface TtsDone { context_id: string, audio_s: number, first_audio_ms: number, stopped: TtsStopped }

type TtsEvents = { audio: [TtsAudio], done: [TtsDone], error: [TaviaError], close: [number] }

/** Splits a binary audio frame: a 16-byte header holding the context id as ASCII, NUL-padded, then PCM16. */
export function parseAudioFrame(bytes: Uint8Array): TtsAudio {
  const head = bytes.subarray(0, HEADER_BYTES)
  const end = head.indexOf(0)
  const context_id = String.fromCharCode(...head.subarray(0, end < 0 ? HEADER_BYTES : end))
  const body = bytes.slice(HEADER_BYTES)
  return { context_id, pcm: new Int16Array(body.buffer, 0, body.length >> 1) }
}

/**
 * One streaming text-to-speech session: speaks in, audio per context out. A context is one agent reply.
 * Events: `audio`, `done`, `error` and `close`. An error with a `contextId` replaces that speak's `done` and the
 * session goes on; one without ends it.
 *
 * @example
 * const tts = await tavia.tts.stream('elaine')
 * tts.on('audio', ({ pcm }) => player.enqueue(pcm))
 * tts.speak({ context_id: 'reply1', text: 'Hello there!', lang: 'en' })
 * tts.closeContext('reply1')
 * await tts.end()
 */
export class TtsStream {
  private readonly events = new Emitter<TtsEvents>()
  private readonly closed: Promise<void>
  private closeCode: number | null = null
  private fatal = false

  /** Wraps an open socket; most apps use `tavia.tts.stream` instead. */
  constructor(private readonly socket: SocketLike) {
    socket.onmessage = (m) => this.receive(m.data)
    this.closed = new Promise((resolve) => {
      socket.onclose = (e) => { this.closeCode = e.code; this.events.emit('close', e.code); resolve() }
    })
  }

  /** Listens for an event; returns a function that stops listening. */
  on<K extends keyof TtsEvents>(name: K, cb: (...args: TtsEvents[K]) => void): () => void {
    return this.events.on(name, cb)
  }

  /** Queues text to speak in a context. Throws a TypeError for a bad context id or style. */
  speak(opts: SpeakOptions): void {
    if (!CONTEXT_ID.test(opts.context_id)) throw new TypeError(`context_id must match ${CONTEXT_ID}`)
    if (opts.style !== undefined && !STYLES.has(opts.style)) throw new TypeError(`unknown style ${opts.style}`)
    this.send({ type: 'speak', ...opts })
  }

  /** Says the reply is complete: no more text for this context; its queued speaks still play. */
  closeContext(contextId: string): void {
    this.send({ type: 'close_context', context_id: contextId })
  }

  /** Drops the running speak and every queued speak of the context: send it on barge-in. */
  cancel(contextId: string): void {
    this.send({ type: 'cancel', context_id: contextId })
  }

  /**
   * No more speaks: queued speaks finish, then the server closes. A session that ended on an error rejects
   * with SessionClosedError and the close code.
   */
  async end(): Promise<void> {
    this.send({ type: 'end' })
    await this.closed
    const code = this.closeCode ?? 0
    if (this.fatal || errorForClose(code)) throw new SessionClosedError(code)
  }

  /** Closes the socket at once, dropping anything queued. */
  close(): void {
    this.socket.close()
  }

  /** Sends one JSON frame; throws SessionClosedError once the socket has closed. */
  send(frame: object): void {
    sendOpen(this.socket, JSON.stringify(frame), this.closeCode)
  }

  private receive(data: unknown): void {
    const bytes = toBytes(data)
    if (bytes) {
      this.events.emit('audio', parseAudioFrame(bytes))
      return
    }
    const msg = JSON.parse(String(data)) as Record<string, unknown>
    if (msg.type === 'done') this.events.emit('done', msg as unknown as TtsDone)
    else if (msg.type === 'error') this.emitError(msg)
  }

  private emitError(msg: Record<string, unknown>): void {
    const contextId = typeof msg.context_id === 'string' ? msg.context_id : null
    if (contextId === null) this.fatal = true
    this.events.emit('error', errorForCode(String(msg.code), String(msg.message ?? ''), { contextId }))
  }
}

/** Options for {@link openTtsStream}. */
export interface TtsStreamOptions {
  /** An API key (servers only) or a short-lived browser token. */
  auth: Auth
  /** The voice id for the whole stream. */
  voice: string
  /** Your id for the session; defaults to a random one. */
  sessionId?: string
  /** The stream endpoint; defaults to the public API. */
  url?: string
  /** Opens the WebSocket; defaults to the browser's, or the `ws` package in Node. */
  socket?: SocketFactory
}

/** Opens a text-to-speech stream and sends its start frame; most apps use `tavia.tts.stream` instead. */
export async function openTtsStream(opts: TtsStreamOptions): Promise<TtsStream> {
  const socket = await openSocket(opts.url ?? TTS_STREAM_URL, LAYERS.tts.subprotocol, opts.auth, opts.socket)
  const stream = new TtsStream(socket)
  const session_id = opts.sessionId ?? crypto.randomUUID().replace(/-/g, '')
  stream.send({ type: 'start', voice: opts.voice, session_id, sample_rate: SURFACE.tts.sampleRate })
  return stream
}
