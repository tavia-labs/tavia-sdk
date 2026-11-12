import { postJson, type HttpOptions } from './transport/http.ts'
import { DEFAULT_URLS } from './transport/urls.ts'

/** The token endpoint on the public API. */
export const TOKENS_URL = DEFAULT_URLS.tokens

/** The product a browser token is for: realtime voice, speech-to-text or text-to-speech. */
export type TokenProduct = 'voice' | 'stt' | 'tts'
const PRODUCTS: readonly string[] = ['voice', 'stt', 'tts'] satisfies TokenProduct[]
const ORIGIN = /^https:\/\/[a-z0-9.-]+(:[0-9]+)?$/

/** A short-lived token for one browser page, as returned by {@link createToken}. */
export interface BrowserToken {
  /** The token itself; pass it to the client as `{ token }`. */
  token: string
  /** The endpoint the token is for. */
  url: string
  /** The exact list for `new WebSocket(url, subprotocols)`. */
  subprotocols: string[]
  /** When the token stops working, as an ISO 8601 timestamp. */
  expires_at: string
  /** A bound session's string: pass it unchanged to `realtime.connect({ boundSession })`. */
  session?: string
}

/**
 * Mints a short-lived token for a page on `origin` (one of your organisation's allowed origins). Run it on your
 * server: it needs an API key. A voice token may bind `session`; the page then cannot change those fields.
 * Throws a TypeError for a bad product, origin or session, and a `TaviaError` when the API refuses.
 *
 * @example
 * const tavia = new Tavia({ apiKey: process.env.TAVIA_API_KEY! })
 * const { token } = await tavia.tokens.create('voice', 'https://app.example.com')
 */
export function createToken(
  opts: HttpOptions & { url?: string }, product: TokenProduct, origin: string, session?: Record<string, unknown>,
): Promise<BrowserToken> {
  if (!('apiKey' in opts.auth)) throw new TypeError('creating a token needs an API key')
  if (!PRODUCTS.includes(product)) throw new TypeError(`product must be one of ${PRODUCTS.join(', ')}`)
  if (!ORIGIN.test(origin)) throw new TypeError('origin must be a bare https origin, such as https://app.example.com')
  const url = opts.url ?? TOKENS_URL
  if (!url.startsWith('https://')) throw new TypeError('the tokens url must be https: the API key never goes out in clear text')
  if (session !== undefined && (typeof session !== 'object' || session === null || Array.isArray(session))) {
    throw new TypeError('session must be an object of session fields')
  }
  return postJson<BrowserToken>(opts, url, { product, origin, ...(session === undefined ? {} : { session }) })
}
