import { BASE_PATH, BASE_URL, LAYERS, PATHS, SURFACE } from '../generated/spec.ts'

type Camel<S extends string> = S extends `${infer A}_${infer B}` ? `${A}${Capitalize<Camel<B>>}` : S

/** An endpoint the client can point elsewhere with the `urls` option. */
export type UrlKey = Camel<(typeof SURFACE.urls.keys)[number]>
/** A full URL for every endpoint. */
export type Urls = Record<UrlKey, string>

const camel = (s: string): string => s.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase())
const URL_KEYS: ReadonlySet<string> = new Set(SURFACE.urls.keys.map(camel))
const SOCKETS: ReadonlySet<string> = new Set(['realtime', 'ttsStream'])
const PATH_OF: Readonly<Record<string, string>> = { ...PATHS, tokens: SURFACE.tokens.path }

// The live speech-to-text socket is not served under the base URL; it keeps its own host.
const STT_LIVE_URL = `wss://${LAYERS.stt.host}${PATHS.sttLive}`

/** Every endpoint's URL with `baseURL` (e.g. https://api.tavialabs.com/v1) in front of its path. */
export function endpointUrls(baseURL: string = BASE_URL): Urls {
  const base = baseURL.replace(/\/+$/, '')
  const out: Record<string, string> = { sttLive: STT_LIVE_URL }
  for (const [key, path] of Object.entries(PATH_OF)) {
    if (!path.startsWith(`${BASE_PATH}/`)) continue
    const url = base + path.slice(BASE_PATH.length)
    out[key] = SOCKETS.has(key) ? url.replace(/^http/, 'ws') : url
  }
  return out as Urls
}

/** The endpoints on the public API. */
export const DEFAULT_URLS: Readonly<Urls> = endpointUrls()

/** Throws a TypeError naming any key that is not an endpoint. */
export function checkUrlKeys(urls: object): void {
  const unknown = Object.keys(urls).filter((k) => !URL_KEYS.has(k))
  if (unknown.length) throw new TypeError(`unknown url override: ${unknown.join(', ')}; allowed: ${[...URL_KEYS].join(', ')}`)
}
