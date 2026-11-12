import { describe, expect, it } from 'vitest'

import { NotFoundError, RateLimitError, SessionClosedError, TaviaError } from '../src/errors.ts'
import { LAYERS, LIMITS } from '../src/generated/spec.ts'
import { STT_FILES_URL, createJob, deleteJob, getJob, transcribe } from '../src/stt/files.ts'
import { openSttStream, sttConfig, type SttFinal, type SttPartial } from '../src/stt/live.ts'
import { fakeFactory, fakeFetch } from './fakes.ts'

const FINAL = {
  tokens: [{ text: 'my', start_ms: 1, end_ms: 2, is_final: true }, { text: ' name', is_final: true }, { text: '<fin>', is_final: true }],
  total_audio_proc_ms: 900, nbest: [], decoder: 'general', empty: false, formatted: 'My name',
}
const FILES_URL = STT_FILES_URL

async function openStream(config = {}): Promise<{ stream: Awaited<ReturnType<typeof openSttStream>>, socket: ReturnType<typeof fakeFactory> }> {
  const socket = fakeFactory()
  const stream = await openSttStream({ auth: { apiKey: 'k' }, config, socket })
  return { stream, socket }
}

describe('stt live', () => {
  it('config_defaults_to_the_spec_format_and_maps_terms', () => {
    expect(sttConfig({ terms: ['Tavia'], format: false })).toEqual({
      audio_format: 'pcm_s16le', sample_rate: LIMITS['stt.sampleRate'], format: false, context: { terms: ['Tavia'] },
    })
  })

  it('sends_the_config_first_then_audio_and_control_messages', async () => {
    const { stream, socket } = await openStream({ decoder: 'spell', nbest: 3 })
    stream.sendAudio(Int16Array.from([1, 2]))
    stream.finalize()
    stream.setDecoder('general')
    stream.keepalive()
    expect(socket.last?.protocols).toEqual([LAYERS.stt.subprotocol])
    expect(socket.last?.sent).toEqual([
      { audio_format: 'pcm_s16le', sample_rate: 16000, decoder: 'spell', nbest: 3 },
      new Uint8Array([1, 0, 2, 0]),
      { type: 'finalize' }, { type: 'set_decoder', decoder: 'general' }, { type: 'keepalive' },
    ])
  })

  it('set_terms_sends_a_set_context_frame', async () => {
    const { stream, socket } = await openStream()
    stream.setTerms(['Dr Ong', 'Raffles'])
    stream.setTerms([])
    expect(socket.last?.sent.slice(1)).toEqual([
      { type: 'set_context', context: { terms: ['Dr Ong', 'Raffles'] } }, { type: 'set_context', context: { terms: [] } },
    ])
  })

  it('set_terms_refuses_over_the_limits_before_sending', async () => {
    const { stream, socket } = await openStream()
    const tooMany = Array.from({ length: LIMITS['stt.terms'] + 1 }, (_, i) => `t${i}`)
    expect(() => stream.setTerms(tooMany)).toThrow(`context.terms must hold at most ${LIMITS['stt.terms']} terms`)
    expect(() => stream.setTerms(['é'.repeat(4096), 'x'.repeat(8192)])).toThrow(`context.terms must be at most ${LIMITS['limits.termsBytes']} bytes`)
    expect(socket.last?.sent).toHaveLength(1)
  })

  it('final_tokens_keep_their_confidence', async () => {
    const { stream, socket } = await openStream()
    const finals: SttFinal[] = []
    stream.on('final', (f) => finals.push(f))
    socket.last?.push({ ...FINAL, tokens: [{ text: 'my', start_ms: 1, end_ms: 2, is_final: true, confidence: 0.93 }, { text: '<fin>', is_final: true }] })
    expect(finals[0]?.tokens[0]?.confidence).toBe(0.93)
  })

  it('parses_partials_finals_with_formatted_and_empty', async () => {
    const { stream, socket } = await openStream()
    const partials: SttPartial[] = []
    const finals: SttFinal[] = []
    stream.on('partial', (p) => partials.push(p))
    stream.on('final', (f) => finals.push(f))
    socket.last?.push({ tokens: [{ text: 'my', is_final: false }], total_audio_proc_ms: 10 })
    socket.last?.push(FINAL)
    socket.last?.push({ tokens: [{ text: '<fin>', is_final: true }], total_audio_proc_ms: 20, nbest: [], decoder: 'general', empty: true, formatted: '' })
    expect(partials[0]).toMatchObject({ text: 'my' })
    expect(finals[0]).toMatchObject({ text: 'my name', formatted: 'My name', empty: false, decoder: 'general' })
    expect(finals[1]).toMatchObject({ text: '', formatted: '', empty: true })
  })

  it('include_fillers_is_sent_and_turns_carry_the_fillers', async () => {
    const { stream, socket } = await openStream({ include_fillers: true })
    expect(socket.last?.sent[0]).toEqual({ audio_format: 'pcm_s16le', sample_rate: 16000, include_fillers: true })
    const partials: SttPartial[] = []
    const finals: SttFinal[] = []
    stream.on('partial', (p) => partials.push(p))
    stream.on('final', (f) => finals.push(f))
    const filler = { type: 'uh', start_ms: 400, end_ms: 900, is_final: true, before: 1 }
    socket.last?.push({ tokens: [{ text: 'my', is_final: false }, { text: ' (um…)', is_final: false, filler: 'uh' }], total_audio_proc_ms: 10, fillers: [{ ...filler, is_final: false }] })
    socket.last?.push({ ...FINAL, fillers: [filler] })
    socket.last?.push(FINAL)
    expect(partials[0]?.fillers).toEqual([{ ...filler, is_final: false }])
    expect(partials[0]?.tokens[1]?.filler).toBe('uh')
    expect(finals[0]?.fillers).toEqual([filler])
    expect(finals[1]?.fillers).toEqual([])
  })

  it('end_sends_an_empty_frame_and_waits_for_finished', async () => {
    const { stream, socket } = await openStream()
    const done = stream.end()
    expect(socket.last?.sent.at(-1)).toBe('')
    socket.last?.push({ finished: true })
    await done
  })

  it('sending_on_a_closed_stream_throws', async () => {
    const { stream, socket } = await openStream()
    socket.last?.close(1000)
    for (const send of [() => stream.sendAudio(new Int16Array(2)), () => stream.finalize(), () => stream.setDecoder('spell'), () => stream.setTerms(['x']), () => stream.keepalive()]) {
      expect(send).toThrow(SessionClosedError)
    }
    await expect(stream.end()).rejects.toThrow(SessionClosedError)
  })

  it('errors_carry_the_http_status', async () => {
    const { stream, socket } = await openStream()
    const errors: TaviaError[] = []
    stream.on('error', (e) => errors.push(e))
    socket.last?.push({ error_code: 400, error_message: 'bad config' })
    expect(errors[0]).toMatchObject({ http: 400, message: 'bad config', closeCode: 4400 })
  })
})

describe('stt files', () => {
  it('create_get_delete_hit_the_spec_paths_with_the_key', async () => {
    const fetch = fakeFetch([[202, { job_id: 'j1' }], [200, { status: 'running', progress: 0.5 }], [204, null]])
    const opts = { auth: { apiKey: 'k' }, fetch }
    expect(await createJob(opts, new Uint8Array([1]), ['Tavia', 'Paxlovid'])).toBe('j1')
    expect(await getJob(opts, 'j1')).toEqual({ status: 'running', progress: 0.5 })
    await deleteJob(opts, 'j1')
    expect(fetch.calls.map((c) => [c.init.method ?? 'GET', c.url])).toEqual([
      ['POST', FILES_URL], ['GET', `${FILES_URL}/j1`], ['DELETE', `${FILES_URL}/j1`],
    ])
    const form = fetch.calls[0]?.init.body as FormData
    expect(form.get('terms')).toBe('Tavia\nPaxlovid')
    expect(fetch.calls[0]?.init.headers).toMatchObject({ Authorization: 'Bearer k' })
  })

  it('transcribe_polls_until_done_then_deletes', async () => {
    const result = { text: 'hello', duration_s: 1, decoder: 'general', segments: [] }
    const fetch = fakeFetch([[202, { job_id: 'j1' }], [200, { status: 'queued', progress: 0 }], [200, { status: 'done', progress: 1, result }], [204, null]])
    const out = await transcribe({ auth: { apiKey: 'k' }, fetch, sleep: async () => undefined }, new Blob(['x']))
    expect(out).toEqual(result)
    expect(fetch.calls.at(-1)?.init.method).toBe('DELETE')
  })

  it('a_failed_job_throws_its_code_and_is_still_deleted', async () => {
    const fetch = fakeFetch([[202, { job_id: 'j1' }], [200, { status: 'failed', progress: null, error: 'audio_too_long' }], [204, null]])
    await expect(transcribe({ auth: { apiKey: 'k' }, fetch }, new Uint8Array(2))).rejects.toMatchObject({ code: 'audio_too_long', http: 413 })
    expect(fetch.calls.at(-1)?.init.method).toBe('DELETE')
  })

  it('http_errors_are_typed', async () => {
    await expect(getJob({ auth: { apiKey: 'k' }, fetch: fakeFetch([[404, { error: 'not_found' }]]) }, 'x')).rejects.toBeInstanceOf(NotFoundError)
    const busy = fakeFetch([[429, { error: { code: 'active_job', message: 'wait' } }]])
    await expect(createJob({ auth: { apiKey: 'k' }, fetch: busy, maxRetries: 0 }, new Uint8Array(2))).rejects.toBeInstanceOf(RateLimitError)
  })
})
