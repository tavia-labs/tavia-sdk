import { SURFACE, type Language, type TtsStyle, type VoiceId } from '../generated/spec.ts'
import { postJson, request, type HttpOptions } from '../transport/http.ts'
import { DEFAULT_URLS } from '../transport/urls.ts'

/** The render endpoint on the public API. */
export const TTS_RENDER_URL = DEFAULT_URLS.ttsRender
/** The voice list endpoint on the public API. */
export const VOICES_URL = DEFAULT_URLS.voices
const MAX_CHARS = SURFACE.tts.renderMaxChars

/** What to render with `tavia.tts.render`. */
export interface RenderOptions {
  /** The voice id; see `tavia.tts.voices()`. */
  voice: VoiceId
  /** The text to speak; at most the API's render character limit, or a RangeError is thrown. */
  text: string
  /** The text's language. */
  lang: Language
  /** An optional speaking style. */
  style?: TtsStyle
}

/** One sentence of a render; `audio_s` is its length in seconds. */
export interface RenderedSentence { audio_s: number, [key: string]: unknown }

/** A finished render. */
export interface TtsRender {
  /** The audio's sample rate in Hz. */
  sample_rate: number
  /** The audio's length in seconds. */
  audio_s: number
  /** A PCM16 mono WAV file. */
  wav: Uint8Array
  /** The text's sentences, in order. */
  sentences: RenderedSentence[]
}

/** A public voice and the languages it speaks. */
export interface VoiceInfo { id: string, name: string, description: string, languages: Language[] }
/** The public voices, the default voice id, and the fallback voice id for each language. */
export interface VoiceList { voices: VoiceInfo[], default: string, by_language: Record<string, string> }

interface RenderBody { sample_rate: number, audio_s: number, wav_base64: string, sentences: RenderedSentence[] }

function fromBase64(b64: string): Uint8Array {
  const bin = atob(b64)
  return Uint8Array.from(bin, (c) => c.charCodeAt(0))
}

/** One-shot speech: the whole text as one WAV. Throws a RangeError for text over the limit. */
export async function render(opts: HttpOptions & { url?: string }, r: RenderOptions): Promise<TtsRender> {
  if (r.text.length > MAX_CHARS) throw new RangeError(`render text is at most ${MAX_CHARS} characters`)
  const body = await postJson<RenderBody>(opts, opts.url ?? TTS_RENDER_URL, r)
  return { sample_rate: body.sample_rate, audio_s: body.audio_s, wav: fromBase64(body.wav_base64), sentences: body.sentences }
}

/** The public voices, each with the languages it speaks, the default and each language's fallback voice. */
export function listVoices(opts: HttpOptions & { url?: string }): Promise<VoiceList> {
  return request<VoiceList>(opts, opts.url ?? VOICES_URL)
}
