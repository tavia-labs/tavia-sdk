import { describe, expect, it } from 'vitest'

import { InvalidRequestError, SessionClosedError, UnsupportedMediaError, type TaviaError } from '../src/errors.ts'
import { LAYERS, TOKEN_SUBPROTOCOL_PREFIX, VOICES } from '../src/generated/spec.ts'
import { createToken } from '../src/tokens.ts'
import { TTS_RENDER_URL, listVoices, render } from '../src/tts/render.ts'
import { openTtsStream, parseAudioFrame, type TtsAudio, type TtsDone } from '../src/tts/stream.ts'
import { fakeFactory, fakeFetch } from './fakes.ts'

function audioFrame(contextId: string, samples: number[]): ArrayBuffer {
  const bytes = new Uint8Array(16 + samples.length * 2)
  bytes.set([...contextId].map((c) => c.charCodeAt(0)))
  new DataView(bytes.buffer).setInt16(16, samples[0] ?? 0, true)
  return bytes.buffer
}

describe('tts stream', () => {
  it('starts_with_the_voice_then_speaks_closes_and_cancels_contexts', async () => {
    const socket = fakeFactory()
    const stream = await openTtsStream({ auth: { token: 't' }, voice: 'elaine', sessionId: 's1', socket })
    stream.speak({ context_id: 'r1', text: 'Hello there.', lang: 'en', style: 'warm' })
    stream.closeContext('r1')
    stream.cancel('r2')
    expect(socket.last?.protocols).toEqual([LAYERS.tts.subprotocol, `${TOKEN_SUBPROTOCOL_PREFIX}t`])
    expect(socket.last?.sent).toEqual([
      { type: 'start', voice: 'elaine', session_id: 's1', sample_rate: 24000 },
      { type: 'speak', context_id: 'r1', text: 'Hello there.', lang: 'en', style: 'warm' },
      { type: 'close_context', context_id: 'r1' },
      { type: 'cancel', context_id: 'r2' },
    ])
    expect(() => stream.speak({ context_id: 'bad id!', text: 'x', lang: 'en' })).toThrow(/context_id/)
    expect(() => stream.speak({ context_id: 'r3', text: 'x', lang: 'en', style: 'shouty' as never })).toThrow(/style/)
  })

  it('routes_audio_done_and_context_errors', async () => {
    const socket = fakeFactory()
    const stream = await openTtsStream({ auth: { apiKey: 'k' }, voice: 'elaine', socket })
    const audio: TtsAudio[] = []
    const done: TtsDone[] = []
    const errors: TaviaError[] = []
    stream.on('audio', (a) => audio.push(a))
    stream.on('done', (d) => done.push(d))
    stream.on('error', (e) => errors.push(e))
    socket.last?.push(audioFrame('r1', [7]))
    socket.last?.push({ type: 'done', context_id: 'r1', audio_s: 1.2, first_audio_ms: 210, stopped: null })
    socket.last?.push({ type: 'error', code: 'unsupported_language', message: 'no', context_id: 'r2' })
    expect(audio[0]?.context_id).toBe('r1')
    expect([...audio[0]?.pcm ?? []]).toEqual([7])
    expect(done[0]).toMatchObject({ context_id: 'r1', stopped: null })
    expect(errors[0]).toBeInstanceOf(InvalidRequestError)
    expect(errors[0]).toMatchObject({ code: 'unsupported_language', contextId: 'r2' })
  })

  it('sending_on_a_closed_stream_throws', async () => {
    const socket = fakeFactory()
    const stream = await openTtsStream({ auth: { apiKey: 'k' }, voice: 'elaine', socket })
    socket.last?.close(4401)
    expect(() => stream.speak({ context_id: 'r1', text: 'Hi.', lang: 'en' })).toThrow(SessionClosedError)
    expect(() => stream.closeContext('r1')).toThrow(SessionClosedError)
    expect(() => stream.cancel('r1')).toThrow(SessionClosedError)
    await expect(stream.end()).rejects.toThrow(SessionClosedError)
  })

  it('header_is_the_full_16_bytes_when_unpadded', () => {
    expect(parseAudioFrame(new Uint8Array(audioFrame('abcdefghijklmnop', [1]))).context_id).toBe('abcdefghijklmnop')
  })

  it('end_after_an_error_close_raises_session_closed_with_the_code', async () => {
    const socket = fakeFactory()
    const stream = await openTtsStream({ auth: { apiKey: 'k' }, voice: 'elaine', socket })
    stream.on('error', () => undefined)
    const ended = stream.end()
    socket.last?.push({ type: 'error', code: 'internal', message: 'failed' })
    socket.last?.close(4500)
    await expect(ended).rejects.toThrow(SessionClosedError)
    await expect(ended).rejects.toMatchObject({ closeCode: 4500 })
  })

  it('end_after_a_fatal_error_then_a_normal_close_still_raises', async () => {
    const socket = fakeFactory()
    const stream = await openTtsStream({ auth: { apiKey: 'k' }, voice: 'elaine', socket })
    stream.on('error', () => undefined)
    const ended = stream.end()
    socket.last?.push({ type: 'error', code: 'internal', message: 'failed' })
    socket.last?.close(1000)
    await expect(ended).rejects.toMatchObject({ name: 'SessionClosedError', closeCode: 1000 })
  })

  it('end_waits_for_the_server_to_close', async () => {
    const socket = fakeFactory()
    const stream = await openTtsStream({ auth: { apiKey: 'k' }, voice: 'elaine', socket })
    const ended = stream.end()
    expect(socket.last?.sent.at(-1)).toEqual({ type: 'end' })
    socket.last?.close()
    await ended
  })
})

describe('tts render, voices and tokens', () => {
  it('render_decodes_the_wav_and_refuses_long_text', async () => {
    const fetch = fakeFetch([[200, { sample_rate: 24000, audio_s: 0.5, wav_base64: 'UklGRg==', sentences: [{ audio_s: 0.5 }] }]])
    const out = await render({ auth: { apiKey: 'k' }, fetch }, { voice: 'elaine', text: 'Hi.', lang: 'en' })
    expect([...out.wav]).toEqual([82, 73, 70, 70])
    expect(fetch.calls[0]?.url).toBe(TTS_RENDER_URL)
    expect(JSON.parse(String(fetch.calls[0]?.init.body))).toEqual({ voice: 'elaine', text: 'Hi.', lang: 'en' })
    await expect(render({ auth: { apiKey: 'k' }, fetch }, { voice: 'elaine', text: 'x'.repeat(501), lang: 'en' })).rejects.toThrow(/500/)
  })

  it('render_errors_are_typed', async () => {
    const fetch = fakeFetch([[415, { error: { code: 'unsupported_audio', message: 'no' } }]])
    await expect(render({ auth: { apiKey: 'k' }, fetch }, { voice: 'elaine', text: 'x', lang: 'en' })).rejects.toBeInstanceOf(UnsupportedMediaError)
  })

  it('voices_lists_each_voice_with_its_languages', async () => {
    const body = { voices: VOICES.public, default: VOICES.default, by_language: VOICES.byLanguage }
    const out = await listVoices({ auth: { token: 't' }, fetch: fakeFetch([[200, body]]) })
    expect(out.voices.find((v) => v.id === 'kai')?.languages).toEqual(['en', 'zh'])
  })

  it('tokens_post_product_and_origin_with_the_key', async () => {
    const reply = { token: 'tok', url: 'wss://x', subprotocols: ['tavia-voice', 'tavia-token.tok'], expires_at: '2026-10-30T10:00:00Z' }
    const fetch = fakeFetch([[200, reply]])
    expect(await createToken({ auth: { apiKey: 'k' }, fetch }, 'voice', 'https://app.example.com')).toEqual(reply)
    expect(fetch.calls[0]?.url).toBe('https://api.tavialabs.com/v1/tokens')
    expect(fetch.calls[0]?.init.headers).toMatchObject({ Authorization: 'Bearer k' })
    expect(JSON.parse(String(fetch.calls[0]?.init.body))).toEqual({ product: 'voice', origin: 'https://app.example.com' })
  })

  it('tokens_may_bind_a_voice_session_and_return_its_string', async () => {
    const bound = '{"instructions":"You are the front desk."}'
    const reply = { token: 'tok', url: 'wss://x', subprotocols: ['tavia-voice', 'tavia-token.tok'], expires_at: '2026-10-30T10:00:00Z', session: bound }
    const fetch = fakeFetch([[200, reply]])
    const out = await createToken({ auth: { apiKey: 'k' }, fetch }, 'voice', 'https://app.example.com', { instructions: 'You are the front desk.' })
    expect(out.session).toBe(bound)
    expect(JSON.parse(String(fetch.calls[0]?.init.body))).toEqual({
      product: 'voice', origin: 'https://app.example.com', session: { instructions: 'You are the front desk.' },
    })
  })

  it('tokens_refuse_a_browser_token_a_bad_product_or_origin_and_clear_text', () => {
    const origin = 'https://app.example.com'
    expect(() => createToken({ auth: { token: 't' } }, 'voice', origin)).toThrow(/API key/)
    expect(() => createToken({ auth: { apiKey: 'k' } }, 'billing' as never, origin)).toThrow(/product/)
    expect(() => createToken({ auth: { apiKey: 'k' } }, 'voice', 'https://app.example.com/path')).toThrow(/origin/)
    expect(() => createToken({ auth: { apiKey: 'k' }, url: 'http://localhost/v1/tokens' }, 'voice', origin)).toThrow(/https/)
  })
})
