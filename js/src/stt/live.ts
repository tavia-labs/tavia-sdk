import { TaviaError } from '../errors.ts'
import { CLOSE_CODE_BASE, LAYERS, LIMITS, SURFACE } from '../generated/spec.ts'
import { Emitter } from '../realtime/emitter.ts'
import { openSocket, sendOpen, type Auth, type SocketFactory, type SocketLike } from '../transport/socket.ts'
import { DEFAULT_URLS } from '../transport/urls.ts'

const FIN = '<fin>'
const AUDIO_FORMAT = 'pcm_s16le'

/** The live speech-to-text endpoint. */
export const STT_LIVE_URL = DEFAULT_URLS.sttLive

/** The recognizer to use: `general` for ordinary speech, `spell` for spelled-out input. */
export type SttDecoder = (typeof SURFACE.stt.decoders)[number]

/** A live stream's configuration: every field the server reads. `stt.stream` also takes `terms`, a shortcut for context.terms. */
export interface SttConfig {
  /** Always `pcm_s16le`, the default. */
  audio_format?: typeof AUDIO_FORMAT
  /** The audio's sample rate in Hz; defaults to the API's live rate. */
  sample_rate?: number
  /** Always 1: mono. */
  num_channels?: 1
  /** The recognizer to start with (default `general`). */
  decoder?: SttDecoder
  /** Hint words, such as names and product terms, the recognizer should expect. */
  context?: { terms: string[] }
  /** How many alternative transcripts each final carries. */
  nbest?: number
  /** true (default): each final also carries `formatted`, the readable transcript. */
  format?: boolean
  /** true: tokens also carry each hesitation in place as a `(um)` / `(um…)` marker token (the marked form). */
  include_fillers?: boolean
  /** Your own id for the stream. */
  client_reference_id?: string
}

/** One recognized token; times are in ms from the start of the stream. */
export interface SttToken {
  /** The token's text; the end-of-turn marker is `<fin>`. */
  text: string
  /** Where the token starts. */
  start_ms?: number
  /** Where the token ends. */
  end_ms?: number
  /** Final tokens will not change; others may be revised by the next partial. */
  is_final: boolean
  /** 0..1, on final tokens of the general decoder; may be absent. */
  confidence?: number
  /** Set on a marker token (include_fillers only): the hesitation it stands for. */
  filler?: SttFillerType
}

/** The kind of hesitation. */
export type SttFillerType = 'uh' | 'um'

/** A hesitation the decoder heard; never a word. `before` counts the turn's words ahead of it. */
export interface SttFiller { type: SttFillerType, start_ms: number, end_ms: number, is_final: boolean, before: number }

/** An interim transcript of the current turn; the next partial or the final may revise it. */
export interface SttPartial { tokens: SttToken[], text: string, total_audio_proc_ms: number, fillers: SttFiller[] }

/** The finished transcript of one turn. */
export interface SttFinal {
  /** The turn's tokens, ending with the end marker. */
  tokens: SttToken[]
  /** The words joined, without the end marker. */
  text: string
  /** How much audio the server has processed, in ms. */
  total_audio_proc_ms: number
  /** Alternative transcripts with their scores, when the config asked for them. */
  nbest: Array<[string, number]>
  /** The recognizer that produced it. */
  decoder: SttDecoder
  /** true when the turn has no words; still sent, one per finalize. */
  empty: boolean
  /** The readable transcript; absent when the config set format false. Never holds a filler marker. */
  formatted?: string
  /** The turn's hesitations, `[]` when none. */
  fillers: SttFiller[]
}

type SttEvents = { partial: [SttPartial], final: [SttFinal], finished: [], error: [TaviaError], close: [number] }

/** The full start config: defaults filled in, and `terms` moved to `context.terms`. */
export function sttConfig(opts: SttConfig & { terms?: string[] } = {}): SttConfig {
  const { terms, ...rest } = opts
  return {
    audio_format: AUDIO_FORMAT,
    sample_rate: LIMITS['stt.sampleRate'],
    ...rest,
    ...(terms ? { context: { terms } } : {}),
  }
}

// The server's own checks: a refused set_context ends the session, so refuse it here first.
function checkTerms(terms: string[]): void {
  const max = LIMITS['stt.terms']
  if (terms.length > max) throw new TypeError(`context.terms must hold at most ${max} terms`)
  const encoder = new TextEncoder()
  const bytes = terms.reduce((n, t) => n + encoder.encode(t).length, 0) + Math.max(terms.length - 1, 0)
  if (bytes > LIMITS['limits.termsBytes']) throw new TypeError(`context.terms must be at most ${LIMITS['limits.termsBytes']} bytes`)
}

const joined = (tokens: SttToken[]): string => tokens.filter((t) => t.text !== FIN).map((t) => t.text).join('').trim()

/**
 * One live transcription stream: binary audio in, partials and one final per turn out.
 * Events: `partial`, `final`, `finished`, `error` and `close`.
 *
 * @example
 * const stt = await tavia.stt.stream({ terms: ['Tavia'] })
 * stt.on('final', (f) => showText(f.formatted ?? f.text))
 * mic.onFrame((pcm) => stt.sendAudio(pcm))
 * // later: await stt.end()
 */
export class SttStream {
  private readonly events = new Emitter<SttEvents>()
  private finished: Promise<void>
  private closeCode: number | null = null

  /** Wraps an open socket; most apps use `tavia.stt.stream` instead. */
  constructor(private readonly socket: SocketLike) {
    socket.onmessage = (m) => { if (typeof m.data === 'string') this.receive(m.data) }
    this.finished = new Promise((resolve) => {
      this.events.on('finished', () => resolve())
      socket.onclose = (e) => { this.closeCode = e.code; this.events.emit('close', e.code); resolve() }
    })
  }

  /** Listens for an event; returns a function that stops listening. */
  on<K extends keyof SttEvents>(name: K, cb: (...args: SttEvents[K]) => void): () => void {
    return this.events.on(name, cb)
  }

  /** Sends PCM16 mono at the config's sample rate as one binary frame. */
  sendAudio(pcm: Int16Array | Uint8Array): void {
    sendOpen(this.socket, pcm, this.closeCode)
  }

  /** Ends the current turn now; the server always answers with a final. */
  finalize(): void {
    this.control({ type: 'finalize' })
  }

  /** Switches the recognizer, e.g. to `spell` while the caller spells something out. */
  setDecoder(decoder: SttDecoder): void {
    this.control({ type: 'set_decoder', decoder })
  }

  /** Replaces the hint words: now if no audio came since the last final, else from the next turn. Throws a TypeError over the limits. */
  setTerms(terms: string[]): void {
    checkTerms(terms)
    this.control({ type: 'set_context', context: { terms } })
  }

  /** Keeps an idle stream open while no audio is sent. */
  keepalive(): void {
    this.control({ type: 'keepalive' })
  }

  /** Ends the stream: the last turn's final (if it has words), then `finished`, then the server closes. */
  async end(): Promise<void> {
    sendOpen(this.socket, '', this.closeCode)
    await this.finished
  }

  /** Closes the socket at once, without waiting for a final. */
  close(): void {
    this.socket.close()
  }

  private control(msg: object): void {
    sendOpen(this.socket, JSON.stringify(msg), this.closeCode)
  }

  private receive(raw: string): void {
    const msg = JSON.parse(raw) as Record<string, unknown>
    if (typeof msg.error_code === 'number') {
      const http = msg.error_code
      this.events.emit('error', new TaviaError({ http, message: String(msg.error_message ?? ''), closeCode: CLOSE_CODE_BASE + http }))
    } else if (msg.finished === true) {
      this.events.emit('finished')
    } else {
      this.emitTranscript(msg)
    }
  }

  private emitTranscript(msg: Record<string, unknown>): void {
    const tokens = (msg.tokens ?? []) as SttToken[]
    const fillers = Array.isArray(msg.fillers) ? (msg.fillers as SttFiller[]) : []
    const base = { tokens, text: joined(tokens), total_audio_proc_ms: Number(msg.total_audio_proc_ms ?? 0), fillers }
    if (tokens.at(-1)?.text !== FIN) {
      this.events.emit('partial', base)
      return
    }
    const { nbest = [], decoder = 'general', empty = false, formatted } = msg as Partial<SttFinal>
    this.events.emit('final', { ...base, nbest, decoder, empty, ...(formatted === undefined ? {} : { formatted }) })
  }
}

/** Options for {@link openSttStream}. */
export interface SttStreamOptions {
  /** An API key (servers only) or a short-lived browser token. */
  auth: Auth
  /** The stream's configuration; `terms` is a shortcut for context.terms. */
  config?: SttConfig & { terms?: string[] }
  /** The live endpoint; defaults to the public API. */
  url?: string
  /** Opens the WebSocket; defaults to the browser's, or the `ws` package in Node. */
  socket?: SocketFactory
}

/** Opens a live transcription stream and sends its config; most apps use `tavia.stt.stream` instead. */
export async function openSttStream(opts: SttStreamOptions): Promise<SttStream> {
  const socket = await openSocket(opts.url ?? STT_LIVE_URL, LAYERS.stt.subprotocol, opts.auth, opts.socket)
  const stream = new SttStream(socket)
  socket.send(JSON.stringify(sttConfig(opts.config)))
  return stream
}
