import { describe, expect, it, vi } from 'vitest'

import { Call } from '../src/realtime/call.ts'
import { connectCall } from '../src/realtime/connect.ts'
import { fakeFactory, fakePlayer, openSocket } from './fakes.ts'

const URL_BASE = 'wss://api.example.test/v1/realtime'
const bound = '{"instructions":"You are the front desk."}'

const audioDelta = (type: string): object => ({
  type, event_id: 'e', response_id: 'r', item_id: 'a1', output_index: 0, content_index: 0, delta: 'AAAA',
})

describe('the standard dialect on the wire', () => {
  it('connect_asks_for_it_and_turns_tavia_events_on', async () => {
    const socket = fakeFactory()
    await connectCall({ url: URL_BASE, auth: { token: 't' }, preset: 'clinic', socket })
    expect(socket.last?.url).toBe(`${URL_BASE}?dialect=ga&preset=clinic`)
    expect(socket.last?.sent).toEqual([{ type: 'session.update', session: { type: 'realtime', tavia: { events: true } } }])
  })

  it('connect_sends_the_session_in_the_standard_shape', async () => {
    const socket = fakeFactory()
    await connectCall({ url: URL_BASE, auth: { token: 't' }, session: { voice: 'ren', languages: ['en'] }, socket })
    expect(socket.last?.sent).toEqual([{
      type: 'session.update',
      session: { type: 'realtime', audio: { output: { voice: 'ren' } }, tavia: { languages: ['en'], events: true } },
    }])
  })

  it('a_bound_session_goes_first_unchanged_then_the_session', async () => {
    const socket = fakeFactory()
    await connectCall({ url: URL_BASE, auth: { token: 't' }, boundSession: bound, session: { languages: ['en'] }, socket })
    expect(socket.last?.sent).toEqual([
      { type: 'session.update', session: { type: 'realtime', tavia: { bound, events: true } } },
      { type: 'session.update', session: { type: 'realtime', tavia: { languages: ['en'] } } },
    ])
  })

  it('update_nests_audio_fields_and_puts_tavia_options_under_tavia_and_the_first_asks_for_events', () => {
    const socket = openSocket()
    new Call(socket).update({
      instructions: 'Be brief.', voice: 'marcus', turn_detection: null, input_audio_format: 'pcm16',
      output_audio_format: 'pcm16', knowledge: { mode: 'rag', kb_id: 'kb1' },
    })
    expect(socket.sent).toEqual([{
      type: 'session.update',
      session: {
        type: 'realtime', instructions: 'Be brief.',
        audio: { input: { turn_detection: null, format: 'pcm16' }, output: { voice: 'marcus', format: 'pcm16' } },
        tavia: { knowledge: { mode: 'rag', kb_id: 'kb1' }, events: true },
      },
    }])
  })

  it('standard_audio_plays_and_its_transcript_is_a_friendly_event', () => {
    const socket = openSocket()
    const player = fakePlayer()
    const call = new Call(socket, { player })
    const said: string[] = []
    call.on('transcript', (t) => said.push(`${t.role}:${t.text}:${t.final}`))
    socket.push(audioDelta('response.output_audio.delta'))
    socket.push({ ...audioDelta('response.output_audio_transcript.done'), delta: undefined, transcript: 'Hello.' })
    expect(player.chunks).toBe(1)
    expect(said).toEqual(['agent:Hello.:true'])
  })

  it('beta_names_from_the_server_are_read_as_their_standard_names', () => {
    const socket = openSocket()
    const player = fakePlayer()
    const call = new Call(socket, { player })
    const types: string[] = []
    call.onEvent('response.output_audio.delta', (e) => types.push(e.type))
    socket.push(audioDelta('response.audio.delta'))
    expect(types).toEqual(['response.output_audio.delta'])
    expect(player.chunks).toBe(1)
  })

  it('a_deprecated_event_name_still_subscribes_to_its_renamed_event', () => {
    const socket = openSocket()
    const call = new Call(socket)
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => undefined)
    const seen: string[] = []
    call.onEvent('response.audio.delta', (e) => seen.push(e.type))
    socket.push(audioDelta('response.output_audio.delta'))
    expect(seen).toEqual(['response.output_audio.delta'])
    expect(warn).toHaveBeenCalledTimes(1)
    warn.mockRestore()
  })
})

describe('the beta dialect', () => {
  it('is_an_explicit_opt_in_that_keeps_the_flat_session', async () => {
    const socket = fakeFactory()
    await connectCall({ url: URL_BASE, auth: { token: 't' }, dialect: 'beta', session: { voice: 'ren' }, socket })
    expect(socket.last?.url).toBe(`${URL_BASE}?dialect=beta`)
    expect(socket.last?.sent).toEqual([{ type: 'session.update', session: { voice: 'ren' } }])
  })
})
