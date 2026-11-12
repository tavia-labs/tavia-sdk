import { ConnectError, errorForHttp } from '../errors.ts'
import { authHeaders, type Auth } from './socket.ts'

/** A `fetch`-compatible function. */
export type Fetch = (input: string, init?: RequestInit) => Promise<Response>

/** How an HTTP request authenticates and retries. */
export interface HttpOptions {
  /** An API key (servers only) or a short-lived browser token. */
  auth: Auth
  /** The fetch to use; defaults to the global one. */
  fetch?: Fetch
  /** Extra attempts after a rate limit, an unavailable server or a network failure (default 2). */
  maxRetries?: number
}

/** Retries after a rate limit, an unavailable server or a network failure, unless `maxRetries` says otherwise. */
export const DEFAULT_MAX_RETRIES = 2
const RETRY_STATUSES: ReadonlySet<number> = new Set([429, 503])
const BACKOFF_MS = 500
const MAX_BACKOFF_MS = 8000

async function bodyOf(res: Response): Promise<unknown> {
  const text = await res.text()
  try {
    return text ? JSON.parse(text) : null
  } catch {
    return text
  }
}

// Retry-After in seconds when the server sends it, else exponential backoff.
function retryDelayMs(res: Response | null, attempt: number): number {
  const after = Number(res?.headers.get('retry-after'))
  if (res?.headers.has('retry-after') && Number.isFinite(after)) return Math.min(after * 1000, MAX_BACKOFF_MS)
  return Math.min(BACKOFF_MS * 2 ** attempt, MAX_BACKOFF_MS)
}

const shouldRetry = (res: Response): boolean =>
  RETRY_STATUSES.has(res.status) && res.headers.get('x-should-retry') !== 'false'

const sleep = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms))

// One attempt: the response, or the network failure as a ConnectError.
async function send(opts: HttpOptions, url: string, init: RequestInit): Promise<Response> {
  try {
    return await (opts.fetch ?? globalThis.fetch)(url, init)
  } catch (err) {
    throw new ConnectError(null, { cause: err })
  }
}

/** One authenticated request, retried as `maxRetries` allows; a non-2xx answer throws its typed error. */
export async function request<T>(opts: HttpOptions, url: string, init: RequestInit = {}): Promise<T> {
  const headers = { ...authHeaders(opts.auth), ...(init.headers as Record<string, string> | undefined) }
  const retries = opts.maxRetries ?? DEFAULT_MAX_RETRIES
  for (let attempt = 0; ; attempt++) {
    let res: Response | null = null
    try {
      res = await send(opts, url, { ...init, headers })
    } catch (err) {
      if (attempt >= retries) throw err
    }
    if (res?.ok) return await bodyOf(res) as T
    if (res && (attempt >= retries || !shouldRetry(res))) throw errorForHttp(res.status, await bodyOf(res))
    await sleep(retryDelayMs(res, attempt))
  }
}

/** POSTs `payload` as JSON with {@link request} and returns the parsed answer. */
export function postJson<T>(opts: HttpOptions, url: string, payload: unknown): Promise<T> {
  return request<T>(opts, url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
}
