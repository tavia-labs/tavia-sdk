import { afterEach, describe, expect, it, vi } from 'vitest'

import { Tavia } from '../src/client.ts'
import { ConnectError, RateLimitError, ServerError, TaviaError } from '../src/errors.ts'
import { fakeFactory, fakeFetch } from './fakes.ts'

const VOICES = { voices: [] }
const now = { 'retry-after': '0' }

afterEach(() => { vi.unstubAllGlobals() })

describe('Tavia client', () => {
  it('uses_the_public_api_base_url_by_default', async () => {
    const socket = fakeFactory()
    const fetch = fakeFetch([[200, VOICES]])
    const tavia = new Tavia({ apiKey: 'k', socket, fetch })
    await tavia.realtime.connect()
    await tavia.tts.voices()
    expect(socket.last?.url).toBe('wss://api.tavialabs.com/v1/realtime?dialect=ga')
    expect(fetch.calls[0]?.url).toBe('https://api.tavialabs.com/v1/voices')
  })

  it('refuses_an_api_key_in_a_browser', () => {
    vi.stubGlobal('window', {})
    expect(() => new Tavia({ apiKey: 'k' })).toThrow(/server/)
    expect(() => new Tavia({ token: 't' })).not.toThrow()
  })
})

describe('HTTP requests', () => {
  it('retry_rate_limits_and_unavailable_answers_then_succeed', async () => {
    const fetch = fakeFetch([[429, { error: 'rate_limited' }, now], [503, null, now], [200, VOICES]])
    await expect(new Tavia({ apiKey: 'k', fetch }).tts.voices()).resolves.toEqual(VOICES)
    expect(fetch.calls).toHaveLength(3)
  })

  it('stop_after_max_retries_with_the_typed_error', async () => {
    const fetch = fakeFetch([[429, { error: 'rate_limited' }, now], [429, { error: 'rate_limited' }, now]])
    await expect(new Tavia({ apiKey: 'k', fetch, maxRetries: 1 }).tts.voices()).rejects.toBeInstanceOf(RateLimitError)
    expect(fetch.calls).toHaveLength(2)
  })

  it('do_not_retry_when_the_server_says_not_to', async () => {
    const fetch = fakeFetch([[503, { error: 'timeout' }, { 'x-should-retry': 'false' }], [200, VOICES]])
    await expect(new Tavia({ apiKey: 'k', fetch }).tts.voices()).rejects.toBeInstanceOf(ServerError)
    expect(fetch.calls).toHaveLength(1)
  })

  it('do_not_retry_other_errors', async () => {
    const fetch = fakeFetch([[500, null], [200, VOICES]])
    await expect(new Tavia({ apiKey: 'k', fetch }).tts.voices()).rejects.toBeInstanceOf(ServerError)
    expect(fetch.calls).toHaveLength(1)
  })

  it('a_network_failure_is_a_connect_error', async () => {
    const fetch = fakeFetch([new TypeError('fetch failed'), new TypeError('fetch failed'), new TypeError('fetch failed')])
    const err = await new Tavia({ apiKey: 'k', fetch, maxRetries: 2 }).tts.voices().catch((e: unknown) => e)
    expect(err).toBeInstanceOf(ConnectError)
    expect(err).toBeInstanceOf(TaviaError)
    expect(err).toMatchObject({ closeCode: null, http: null })
    expect(fetch.calls).toHaveLength(3)
  })
})
