import type { Player } from './audio/player.ts'
import type { SessionConfig } from './generated/types.ts'
import type { Call } from './realtime/call.ts'
import { connectCall } from './realtime/connect.ts'
import { createJob, deleteJob, getJob, transcribe, type AudioFile, type SttFileResult, type SttJob, type TranscribeOptions } from './stt/files.ts'
import { openSttStream, type SttConfig, type SttStream } from './stt/live.ts'
import { createToken, type BrowserToken, type TokenProduct } from './tokens.ts'
import type { Fetch, HttpOptions } from './transport/http.ts'
import { assertKeyOnServer, type Auth, type SocketFactory } from './transport/socket.ts'
import { checkUrlKeys, endpointUrls, type UrlKey } from './transport/urls.ts'
import { listVoices, render, type RenderOptions, type TtsRender, type VoiceList } from './tts/render.ts'
import { openTtsStream, type TtsStream } from './tts/stream.ts'

export type { UrlKey } from './transport/urls.ts'

/** Options for {@link Tavia}: an `apiKey` (servers) or a `token` (browsers), plus the fields below. */
export type TaviaOptions = Auth & {
  /** The API base URL; defaults to https://api.tavialabs.com/v1. The live speech-to-text socket keeps its host. */
  baseURL?: string
  /** Point single endpoints elsewhere, e.g. a test server: each value is a full URL, used as given. */
  urls?: Partial<Record<UrlKey, string>>
  /** Extra attempts after a rate limit, an unavailable server or a network failure (default 2). */
  maxRetries?: number
  /** Opens WebSockets; defaults to the browser's, or the `ws` package in Node. */
  socket?: SocketFactory
  /** The fetch to use; defaults to the global one. */
  fetch?: Fetch
}

/** Options for `tavia.realtime.connect`. */
export interface RealtimeConnectOptions {
  /** Session options sent as soon as the socket opens. */
  session?: Partial<SessionConfig>
  /** A saved agent configuration to start from. */
  preset?: string
  /** Plays the agent's audio. */
  player?: Player
  /** The `session` string `tokens.create` returned for a bound session. */
  boundSession?: string
}

/**
 * The Tavia client: realtime voice sessions, speech-to-text, text-to-speech and browser tokens.
 * Use an API key on your server; in a browser, use a short-lived token your server got from `tokens.create`.
 *
 * @example
 * const tavia = new Tavia({ apiKey: process.env.TAVIA_API_KEY! })
 * const call = await tavia.realtime.connect({ session: { voice: 'elaine', instructions: 'Be brief.' } })
 * call.on('transcript', (t) => { if (t.final) showLine(t.role, t.text) })
 */
export class Tavia {
  /** Realtime voice sessions. */
  readonly realtime: { connect: (opts?: RealtimeConnectOptions) => Promise<Call> }
  /** Speech-to-text: a live stream, or a file transcribed now or as a job. */
  readonly stt: {
    /** Opens a live transcription stream; `terms` are hint words for this stream. */
    stream: (config?: SttConfig & { terms?: string[] }) => Promise<SttStream>
    /** Uploads a file, waits for its transcript and returns it. */
    transcribe: (file: AudioFile, opts?: TranscribeOptions) => Promise<SttFileResult>
    /** Uploads a file for transcription and returns the job id. */
    createJob: (file: AudioFile, terms?: string[]) => Promise<string>
    /** A job's status, and its transcript once done. */
    getJob: (jobId: string) => Promise<SttJob>
    /** Deletes a job and its transcript from the server. */
    deleteJob: (jobId: string) => Promise<void>
  }
  /** Text-to-speech: a live stream, a one-off render, and the voice list. */
  readonly tts: {
    /** Opens a streaming session in `voice`; `sessionId` defaults to a random id. */
    stream: (voice: string, sessionId?: string) => Promise<TtsStream>
    /** Speaks a whole text and returns it as one WAV file. */
    render: (opts: RenderOptions) => Promise<TtsRender>
    /** The public voices and the default voice per language. */
    voices: () => Promise<VoiceList>
  }
  /** Short-lived browser tokens, minted on your server with your API key. */
  readonly tokens: {
    /** Mints a token for a page on `origin`; see {@link createToken}. */
    create: (product: TokenProduct, origin: string, session?: Record<string, unknown>) => Promise<BrowserToken>
  }

  /** Throws a TypeError when an API key is used in a browser or `urls` names an unknown endpoint. */
  constructor(opts: TaviaOptions) {
    const auth: Auth = 'apiKey' in opts ? { apiKey: opts.apiKey } : { token: opts.token }
    assertKeyOnServer(auth)
    checkUrlKeys(opts.urls ?? {})
    const u = { ...endpointUrls(opts.baseURL), ...opts.urls }
    const http = (url: string): HttpOptions & { url: string } => ({ auth, fetch: opts.fetch, maxRetries: opts.maxRetries, url })
    const files = http(u.sttFiles)
    this.realtime = { connect: (c = {}) => connectCall({ ...c, auth, url: u.realtime, socket: opts.socket }) }
    this.stt = {
      stream: (config) => openSttStream({ auth, config, url: u.sttLive, socket: opts.socket }),
      transcribe: (file, t) => transcribe(files, file, t),
      createJob: (file, terms) => createJob(files, file, terms),
      getJob: (id) => getJob(files, id),
      deleteJob: (id) => deleteJob(files, id),
    }
    this.tts = {
      stream: (voice, sessionId) => openTtsStream({ auth, voice, sessionId, url: u.ttsStream, socket: opts.socket }),
      render: (r) => render(http(u.ttsRender), r),
      voices: () => listVoices(http(u.voices)),
    }
    this.tokens = { create: (product, origin, session) => createToken(http(u.tokens), product, origin, session) }
  }
}
