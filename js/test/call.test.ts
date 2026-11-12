import { afterEach, describe, expect, it, vi } from 'vitest'

import { InvalidRequestError, RateLimitError, SessionClosedError, ToolError } from '../src/errors.ts'
import { LAYERS, LIMITS, PRESET_PARAM, TOKEN_SUBPROTOCOL_PREFIX } from '../src/generated/spec.ts'
import { Call } from '../src/realtime/call.ts'
import { connectCall } from '../src/realtime/connect.ts'
import { FRIENDLY_NAMES } from '../src/realtime/friendly.ts'
import { FakeSocket, fakeFactory, fakePlayer, openSocket } from './fakes.ts'

const flush = (): Promise<void> => new Promise((r) => setTimeout(r, 0))

function openCall(player = fakePlayer()): { call: Call, socket: FakeSocket, player: ReturnType<typeof fakePlayer> } {
  const socket = openSocket()
  return { call: new Call(socket, { player }), socket, player }
}

const delta = (item_id: string, samples: number): object => ({
  type: 'response.audio.delta', event_id: 'e', response_id: 'r', item_id, output_index: 0, content_index: 0,
  delta: Buffer.alloc(samples * 2).toString('base64'),
})

const argsDone = (name: string, args: string): object => ({
  type: 'response.function_call_arguments.done', event_id: 'e', response_id: 'r', output_index: 0, item_id: 'i',
  call_id: 'c1', name, arguments: args,
})

afterEach(() => { vi.unstubAllGlobals() })

describe('Call events', () => {
  it('unknown_event_goes_to_raw_only', () => {
    const { call, socket } = openCall()
    const raw = vi.fn()
    const friendly = vi.fn()
    call.onRaw(raw)
    for (const name of FRIENDLY_NAMES) call.on(name, friendly)
    socket.push('{"type":"made.up","event_id":"e1"}')
    expect(raw).toHaveBeenCalledWith(null, '{"type":"made.up","event_id":"e1"}')
    expect(friendly).not.toHaveBeenCalled()
  })

  it('error_events_arrive_as_typed_errors', () => {
    const { call, socket } = openCall()
    const errors: Error[] = []
    call.onError((e) => errors.push(e))
    socket.push({ type: 'error', event_id: 'e', error: { type: 'invalid_request_error', code: 'bad_session', message: 'no' } })
    socket.push({ type: 'error', event_id: 'e', error: { type: 'invalid_request_error', code: 'reply_limit', message: 'x' } })
    expect(errors[0]).toBeInstanceOf(InvalidRequestError)
    expect(errors[0]).toMatchObject({ code: 'bad_session', http: 400, message: 'no' })
    expect(errors[1]).toBeInstanceOf(RateLimitError)
  })

  it('close_reports_the_code_once_with_its_error', () => {
    const { call, socket } = openCall()
    const closed = vi.fn()
    call.onClose(closed)
    socket.close(4402)
    socket.onclose?.({ code: 4402 })
    expect(closed).toHaveBeenCalledTimes(1)
    expect(call.closeError).toMatchObject({ code: 'credit_exhausted', closeCode: 4402 })
  })
})

describe('Call sends', () => {
  it('update_sends_session_update_and_refuses_unknown_options', () => {
    const { call, socket } = openCall()
    const session = { voice: 'marcus', voice_feedback: { acks: true }, knowledge: { mode: 'rag', kb_id: 'kb1' } } as const
    call.update(session)
    expect(socket.sent).toEqual([{
      type: 'session.update',
      session: { type: 'realtime', audio: { output: { voice: 'marcus' } }, tavia: { voice_feedback: { acks: true }, knowledge: session.knowledge, events: true } },
    }])
    expect(() => call.update({ temperature: 1 } as never)).toThrow(/temperature/)
  })

  it('send_audio_appends_base64_pcm_split_at_the_audio_limit', () => {
    const { call, socket } = openCall()
    call.sendAudio(Int16Array.from([1]))
    expect(socket.sent).toEqual([{ type: 'input_audio_buffer.append', audio: 'AQA=' }])
    call.sendAudio(new Uint8Array(LIMITS['realtime.maxAudioBytes'] + 2))
    const sizes = socket.sent.slice(1).map((e) => Buffer.from((e as { audio: string }).audio, 'base64').length)
    expect(sizes).toEqual([LIMITS['realtime.maxAudioBytes'], 2])
  })

  it('text_tool_output_truncate_and_responses', () => {
    const { call, socket } = openCall()
    call.sendText('hello')
    call.sendToolOutput('c1', { ok: true })
    call.truncate('i1', 1234.4)
    call.createResponse()
    call.cancelResponse()
    call.commitAudio()
    call.clearAudio()
    expect(socket.sent).toEqual([
      { type: 'conversation.item.create', item: { type: 'message', role: 'user', content: [{ type: 'input_text', text: 'hello' }] } },
      { type: 'conversation.item.create', item: { type: 'function_call_output', call_id: 'c1', output: '{"ok":true}' } },
      { type: 'conversation.item.truncate', item_id: 'i1', content_index: 0, audio_end_ms: 1234 },
      { type: 'response.create' },
      { type: 'response.cancel' },
      { type: 'input_audio_buffer.commit' },
      { type: 'input_audio_buffer.clear' },
    ])
  })

  it('tool_handler_answers_its_calls', async () => {
    const { call, socket } = openCall()
    call.tool('check_slots', async (args) => ({ slots: ['10:00'], day: args.day }))
    const off = call.tool('broken', () => { throw new Error('down') })
    socket.push(argsDone('check_slots', '{"day":"mon"}'))
    socket.push(argsDone('broken', '{}'))
    off()
    socket.push(argsDone('broken', '{}'))
    socket.push(argsDone('unregistered', '{}'))
    await flush()
    expect(socket.sent).toEqual([
      { type: 'conversation.item.create', item: { type: 'function_call_output', call_id: 'c1', output: '{"error":"tool_failed"}' } },
      { type: 'conversation.item.create', item: { type: 'function_call_output', call_id: 'c1', output: '{"slots":["10:00"],"day":"mon"}' } },
    ])
  })

  it('tool_errors_reach_the_agent_only_as_tool_error_or_on_opt_in', async () => {
    const { call, socket } = openCall()
    const logged = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    call.tool('book', () => { throw new ToolError('That day is fully booked.') })
    call.tool('debug', () => { throw new Error('db at 10.0.0.5 refused') }, { exposeErrors: true })
    call.tool('quiet', () => { throw new Error('db at 10.0.0.5 refused') })
    for (const name of ['book', 'debug', 'quiet']) socket.push(argsDone(name, '{}'))
    await flush()
    const errors = socket.sent.map((e) => JSON.parse((e as { item: { output: string } }).item.output).error)
    expect(errors).toEqual(['That day is fully booked.', 'db at 10.0.0.5 refused', 'tool_failed'])
    expect(logged).toHaveBeenCalledTimes(2)
  })

  it('interrupt_cancels_flushes_and_truncates_at_the_heard_point', () => {
    const { call, socket, player } = openCall()
    socket.push(delta('a1', 24000)) // 1 s queued
    player.played = 400
    call.interrupt()
    expect(socket.sent).toEqual([
      { type: 'response.cancel' },
      { type: 'conversation.item.truncate', item_id: 'a1', content_index: 0, audio_end_ms: 400 },
    ])
    expect(player.flushes).toBe(1)
  })

  it('interrupt_after_playback_finished_only_cancels', () => {
    const { call, socket, player } = openCall()
    socket.push(delta('a1', 2400))
    player.played = 100
    call.interrupt()
    expect(socket.sent).toEqual([{ type: 'response.cancel' }])
  })

})

describe('Call on a closed session', () => {
  it('every_send_throws_session_closed_with_the_close_code', () => {
    const { call, socket } = openCall()
    socket.close(4402)
    const sends = [
      () => call.update({ voice: 'marcus' }), () => call.sendAudio(new Int16Array(4)), () => call.sendText('hi'),
      () => call.sendToolOutput('c1', {}), () => call.truncate('i1', 10), () => call.createResponse(),
      () => call.cancelResponse(), () => call.interrupt(),
    ]
    for (const send of sends) {
      expect(send).toThrow(SessionClosedError)
      try { send() } catch (err) { expect((err as SessionClosedError).closeCode).toBe(4402) }
    }
    expect(socket.sent).toEqual([])
  })

  it('a_closing_socket_counts_as_closed', () => {
    const { call, socket } = openCall()
    socket.readyState = 2
    expect(() => call.sendText('hi')).toThrow(SessionClosedError)
  })

  it('a_tool_result_after_close_is_logged_not_thrown', async () => {
    const { call, socket } = openCall()
    const log = vi.spyOn(console, 'warn').mockImplementation(() => undefined)
    call.tool('slow', async () => { socket.close(1000); return { ok: true } })
    socket.push({ type: 'response.function_call_arguments.done', event_id: 'e', response_id: 'r', output_index: 0, item_id: 'i', call_id: 'c1', name: 'slow', arguments: '{}' })
    await flush()
    expect(log).toHaveBeenCalled()
    log.mockRestore()
  })
})

describe('connectCall', () => {
  it('offers_the_layer_and_token_subprotocols_and_the_preset', async () => {
    const socket = fakeFactory()
    await connectCall({ url: 'wss://example.test/v1/realtime', auth: { token: 'abc' }, preset: 'clinic', session: { voice: 'ren' }, socket })
    expect(socket.last?.url).toBe(`wss://example.test/v1/realtime?dialect=ga&${PRESET_PARAM}=clinic`)
    expect(socket.last?.protocols).toEqual([LAYERS.voice.subprotocol, `${TOKEN_SUBPROTOCOL_PREFIX}abc`])
    expect(socket.last?.sent).toEqual([{ type: 'session.update', session: { type: 'realtime', audio: { output: { voice: 'ren' } }, tavia: { events: true } } }])
  })

  it('api_key_rides_as_a_bearer_header_to_the_public_api', async () => {
    const socket = fakeFactory()
    await connectCall({ auth: { apiKey: 'tv_test_k' }, socket })
    expect(socket.last?.url).toBe('wss://api.tavialabs.com/v1/realtime?dialect=ga')
    expect(socket.last?.protocols).toEqual([LAYERS.voice.subprotocol])
    expect(socket.last?.headers).toEqual({ Authorization: 'Bearer tv_test_k' })
  })

  it('rejects_with_a_typed_error_when_the_socket_closes_before_open', async () => {
    let made: FakeSocket | undefined
    const pending = connectCall({ url: 'wss://x.test/v1/realtime', auth: { token: 't' }, socket: (u, p) => (made = new FakeSocket(u, p)) })
    made?.onclose?.({ code: 4401 })
    await expect(pending).rejects.toMatchObject({ closeCode: 4401, code: null, http: 401, name: 'ConnectError' })
  })

  it('api_key_refused_in_browser_env', async () => {
    vi.stubGlobal('window', {})
    await expect(connectCall({ url: 'wss://x.test', auth: { apiKey: 'tv_test_x' } })).rejects.toThrow(/server/)
  })
})
