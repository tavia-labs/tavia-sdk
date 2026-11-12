import { describe, expect, it } from 'vitest'

import {
  AuthenticationError, ConflictError, ServerError, TaviaError, errorForClose, errorForCode, errorForHttp,
} from '../src/errors.ts'
import { Tavia } from '../src/client.ts'
import { endpointUrls } from '../src/transport/urls.ts'
import { fakeFactory, fakeFetch } from './fakes.ts'

describe('errors', () => {
  it('codes_map_to_classes_by_status_with_the_spec_message', () => {
    const e = errorForCode('unauthorized')
    expect(e).toBeInstanceOf(AuthenticationError)
    expect(e).toBeInstanceOf(TaviaError)
    expect(e).toMatchObject({ code: 'unauthorized', http: 401, name: 'AuthenticationError' })
    expect(e.message).toBe('Sign in or use a valid key.')
    expect(errorForCode('link_expired')).toBeInstanceOf(ConflictError)
    expect(errorForCode('busy')).toBeInstanceOf(ServerError)
    expect(errorForCode('made_up')).toMatchObject({ code: 'made_up', http: null })
  })

  it('close_codes_name_the_code_when_only_one_has_that_status', () => {
    expect(errorForClose(1000)).toBeNull()
    expect(errorForClose(4402)).toMatchObject({ code: 'credit_exhausted', http: 402, closeCode: 4402 })
    expect(errorForClose(4429)).toMatchObject({ code: null, http: 429 })
  })

  it('http_bodies_in_both_shapes', () => {
    expect(errorForHttp(404, { error: 'not_found' })).toMatchObject({ code: 'not_found', http: 404 })
    expect(errorForHttp(429, { error: { code: 'rate_limited', message: 'slow' } })).toMatchObject({ code: 'rate_limited', message: 'slow' })
    expect(errorForHttp(502, 'bad gateway')).toBeInstanceOf(ServerError)
  })

  it('http_bodies_name_the_failing_param', () => {
    const body = { error: { code: 'bad_session', message: 'The session settings are not valid.', param: 'session.tools[1].name' } }
    expect(errorForHttp(400, body)).toMatchObject({ code: 'bad_session', param: 'session.tools[1].name' })
    expect(errorForHttp(404, { error: 'not_found' }).param).toBeNull()
  })
})

describe('Tavia client urls', () => {
  it('each_override_is_a_full_url_used_as_given', async () => {
    const socket = fakeFactory()
    const fetch = fakeFetch([[200, { voices: [], default: 'elaine', by_language: {} }]])
    const tavia = new Tavia({ apiKey: 'k', socket, fetch, urls: { realtime: 'ws://localhost:8080/rt', voices: 'http://localhost:9000/v' } })
    await tavia.realtime.connect()
    expect(socket.last?.url).toBe('ws://localhost:8080/rt?dialect=ga')
    await tavia.tts.voices()
    expect(fetch.calls[0]?.url).toBe('http://localhost:9000/v')
  })

  it('a_base_url_serves_every_path_under_it_and_an_override_still_wins', async () => {
    const socket = fakeFactory()
    const fetch = fakeFetch([[200, { voices: [], default: 'elaine', by_language: {} }]])
    const tavia = new Tavia({ apiKey: 'k', socket, fetch, baseURL: 'http://localhost:8080/v1/', urls: { ttsRender: 'http://x/r' } })
    await tavia.realtime.connect()
    expect(socket.last?.url).toBe('ws://localhost:8080/v1/realtime?dialect=ga')
    await tavia.tts.voices()
    expect(fetch.calls[0]?.url).toBe('http://localhost:8080/v1/voices')
    expect(endpointUrls('https://api.example.com/v1')).toEqual({
      sttLive: 'wss://stt.tavialabs.com/transcribe-websocket',
      realtime: 'wss://api.example.com/v1/realtime', sttFiles: 'https://api.example.com/v1/transcriptions',
      ttsStream: 'wss://api.example.com/v1/tts/stream', ttsRender: 'https://api.example.com/v1/tts/render',
      voices: 'https://api.example.com/v1/voices', tokens: 'https://api.example.com/v1/tokens',
    })
  })

  it('an_unknown_override_is_refused', () => {
    expect(() => new Tavia({ apiKey: 'k', urls: { stt: 'https://x' } as never })).toThrow(/stt/)
  })
})

describe('Tavia client', () => {
  it('one_auth_for_every_product', async () => {
    const socket = fakeFactory()
    const fetch = fakeFetch([[200, { voices: [], default: 'elaine', by_language: {} }]])
    const tavia = new Tavia({ apiKey: 'k', socket, fetch })
    await tavia.realtime.connect({ session: { voice: 'elaine' } })
    expect(socket.last?.headers).toEqual({ Authorization: 'Bearer k' })
    await tavia.tts.voices()
    expect(fetch.calls[0]?.init.headers).toMatchObject({ Authorization: 'Bearer k' })
    await tavia.stt.stream({ terms: ['Tavia'] })
    expect(socket.last?.sent[0]).toMatchObject({ context: { terms: ['Tavia'] } })
  })
})
