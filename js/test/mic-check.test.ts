import { describe, expect, it } from 'vitest'

import { createMicCheck, detectAudioOutput, outputKind, type MicCheck } from '../src/audio/mic-check.ts'
import * as sdk from '../src/index.ts'

const RATE = 16000
const FRAME = 320 // 20 ms
const ROOM_DB = -65

const frameAt = (db: number): Int16Array => new Int16Array(FRAME).fill(Math.round(32768 * 10 ** (db / 20)))

function feed(c: MicCheck, db: number, frames: number): void {
  for (let i = 0; i < frames; i++) c.feed(frameAt(db))
}

// "Hello, I'd like to book an appointment": ~2 s of speech in short runs over a quiet room.
function phrase(c: MicCheck, speechDb: number, roomDb = ROOM_DB): void {
  feed(c, roomDb, 25)
  for (let w = 0; w < 6; w++) { feed(c, speechDb, 18); feed(c, roomDb, 6) }
  feed(c, roomDb, 25)
}

// The check's chime: `rise` dB over the room while it plays (0 = the mic never hears it).
function chime(c: MicCheck, rise: number): void {
  c.tone(true)
  feed(c, ROOM_DB + rise, 40)
  c.tone(false)
}

const devices = (...outs: Array<[string, string]>): { enumerateDevices: () => Promise<MediaDeviceInfo[]> } => ({
  enumerateDevices: async () => outs.map(([deviceId, label]) => ({ kind: 'audiooutput', deviceId, label, groupId: '' } as MediaDeviceInfo)),
})

describe('outputKind', () => {
  it.each([
    ['Default - MacBook Pro Speakers (Built-in)', 'speaker'],
    ['Speakers (Realtek(R) Audio)', 'speaker'],
    ['Default - AirPods Pro', 'headset'],
    ['External Headphones', 'headset'],
    ['Headset Earphone (Jabra Evolve2)', 'headset'],
    ['Headphones (Realtek(R) Audio)', 'headset'],
    ['', 'unknown'],
    ['HDMI', 'unknown'],
  ])('%s_is_%s', (label, kind) => {
    expect(outputKind(label)).toBe(kind)
  })
})

describe('detectAudioOutput', () => {
  it('reads_the_default_output_device', async () => {
    const out = await detectAudioOutput(devices(['abc', 'External Headphones'], ['default', 'Default - MacBook Air Speakers']))
    expect(out).toEqual({ kind: 'speaker', label: 'Default - MacBook Air Speakers' })
  })

  it('is_unknown_when_the_browser_lists_no_outputs_or_throws', async () => {
    expect((await detectAudioOutput(devices())).kind).toBe('unknown')
    const broken = { enumerateDevices: async (): Promise<MediaDeviceInfo[]> => { throw new Error('no') } }
    expect((await detectAudioOutput(broken)).kind).toBe('unknown')
  })
})

describe('createMicCheck', () => {
  it('is_exported_from_the_package', () => {
    expect(typeof sdk.createMicCheck).toBe('function')
    expect(typeof sdk.detectAudioOutput).toBe('function')
  })

  it('a_close_clear_voice_on_earphones_needs_no_advice', () => {
    const c = createMicCheck({ sampleRate: RATE })
    chime(c, 0)
    phrase(c, -22)
    const r = c.result({ outputLabel: 'External Headphones' })
    expect(r).toMatchObject({ heard: true, farAway: false, noisy: false, echo: false, output: 'headset', advice: [] })
  })

  it('silence_is_not_heard', () => {
    const c = createMicCheck({ sampleRate: RATE })
    feed(c, ROOM_DB, 150)
    expect(c.result()).toMatchObject({ heard: false, advice: ['not_heard'] })
  })

  it('a_quiet_voice_says_move_closer', () => {
    const c = createMicCheck({ sampleRate: RATE })
    phrase(c, -44)
    const r = c.result()
    expect(r.heard && r.farAway).toBe(true)
    expect(r.advice).toContain('move_closer')
  })

  it('a_chime_the_mic_hears_means_speakers_and_says_use_earphones_first', () => {
    const c = createMicCheck({ sampleRate: RATE })
    chime(c, 20)
    phrase(c, -44)
    const r = c.result({ outputLabel: '' })
    expect(r.echo).toBe(true)
    expect(r.output).toBe('speaker')
    expect(r.advice[0]).toBe('use_earphones')
    expect(r.advice).toContain('move_closer')
  })

  it('speakers_by_name_say_use_earphones_even_when_the_echo_is_cancelled', () => {
    const c = createMicCheck({ sampleRate: RATE })
    chime(c, 1)
    phrase(c, -22)
    expect(c.result({ outputLabel: 'MacBook Pro Speakers' })).toMatchObject({ echo: false, output: 'speaker', advice: ['use_earphones'] })
  })

  it('no_chime_leaves_echo_unknown', () => {
    const c = createMicCheck({ sampleRate: RATE })
    phrase(c, -22)
    expect(c.result().echo).toBeUndefined()
  })

  it('a_noisy_room_says_find_a_quieter_spot', () => {
    const c = createMicCheck({ sampleRate: RATE })
    phrase(c, -30, -40)
    expect(c.result().advice).toContain('quieter_room')
  })

  it('a_normal_home_or_office_room_is_not_noisy_and_reports_its_margin', () => {
    for (const [speech, room] of [[-26, -55], [-28, -45]] as const) {
      const c = createMicCheck({ sampleRate: RATE })
      phrase(c, speech, room)
      const r = c.result({ outputLabel: 'Headphones' })
      expect(r.noisy, `${speech}/${room}`).toBe(false)
      expect(r.snrDb).toBeGreaterThanOrEqual(15)
    }
  })

  it('a_noisy_room_reports_its_margin_so_a_page_can_tell_borderline_from_loud', () => {
    const c = createMicCheck({ sampleRate: RATE })
    phrase(c, -29, -40)
    expect(c.result()).toMatchObject({ heard: true, noisy: true, snrDb: 11 })
    const quiet = createMicCheck({ sampleRate: RATE })
    feed(quiet, ROOM_DB, 100)
    expect(quiet.result().snrDb).toBeUndefined()
  })

  it('a_bluetooth_mic_says_so', () => {
    const c = createMicCheck({ sampleRate: RATE })
    phrase(c, -22)
    expect(c.result({ micLabel: 'AirPods Pro (Bluetooth)' }).advice).toContain('avoid_bluetooth')
  })

  it('bad_frames_are_ignored_never_thrown', () => {
    const c = createMicCheck({ sampleRate: RATE })
    expect(() => c.feed(new Int16Array(0))).not.toThrow()
    expect(() => c.feed('x' as unknown as Int16Array)).not.toThrow()
    expect(c.result().heard).toBe(false)
  })
})
