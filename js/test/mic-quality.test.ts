import { describe, expect, it } from 'vitest'

import { createMicQuality, type MicQuality } from '../src/audio/mic-quality.ts'
import * as sdk from '../src/index.ts'

const RATE = 16000
const FRAME = 320 // 20 ms at 16 kHz
const NOISE_DB = -62

// A 20 ms frame at a given dBFS (a constant signal: its RMS is its amplitude).
const frameAt = (db: number): Int16Array => new Int16Array(FRAME).fill(Math.round(32768 * 10 ** (db / 20)))

function feedAll(q: MicQuality, dbs: number[]): void {
  for (const db of dbs) q.feed(frameAt(db))
}

// `cycles` of speech at `speechDb` that stops dead into room noise: a close, dry speaker.
function dry(speechDb: number, cycles: number, speech = 25, gap = 15): number[] {
  const one = [...Array<number>(speech).fill(speechDb), ...Array<number>(gap).fill(NOISE_DB)]
  return Array.from({ length: cycles }, () => one).flat()
}

// Loud speech whose offsets fade 1 dB per 20 ms (a reverberant room) before dropping to noise.
function reverberant(cycles: number): number[] {
  const tail = Array.from({ length: 15 }, (_, i) => -16 - (i + 1))
  const one = [...Array<number>(15).fill(-16), ...tail, ...Array<number>(10).fill(NOISE_DB)]
  return Array.from({ length: cycles }, () => one).flat()
}

describe('createMicQuality', () => {
  it('is_exported_from_the_package', () => {
    expect(typeof sdk.createMicQuality).toBe('function')
  })

  it('starts_silent_and_close', () => {
    expect(createMicQuality().state()).toEqual({ level: 0, speaking: false, farAway: false })
  })

  it('level_follows_the_last_frame_on_a_0_to_1_scale', () => {
    const q = createMicQuality({ sampleRate: RATE })
    q.feed(frameAt(-30))
    expect(q.state().level).toBeCloseTo(0.5, 1)
    q.feed(frameAt(-3))
    expect(q.state().level).toBeGreaterThan(0.9)
    q.feed(new Int16Array(FRAME))
    expect(q.state().level).toBe(0)
  })

  it('speaking_is_true_on_voice_and_false_on_room_noise', () => {
    const q = createMicQuality({ sampleRate: RATE })
    feedAll(q, Array<number>(20).fill(NOISE_DB))
    feedAll(q, [-20, -20, -20])
    expect(q.state().speaking).toBe(true)
    feedAll(q, Array<number>(5).fill(NOISE_DB))
    expect(q.state().speaking).toBe(false)
  })

  it('quiet_speech_far_from_the_mic_is_far_away', () => {
    const q = createMicQuality({ sampleRate: RATE })
    feedAll(q, dry(-41, 5))
    expect(q.state().farAway).toBe(true)
  })

  it('a_slow_reverberant_tail_is_far_away_even_when_loud', () => {
    const q = createMicQuality({ sampleRate: RATE })
    feedAll(q, reverberant(6))
    expect(q.state().farAway).toBe(true)
  })

  it('loud_close_speech_is_not_far_away', () => {
    const q = createMicQuality({ sampleRate: RATE })
    feedAll(q, dry(-10, 5))
    expect(q.state().farAway).toBe(false)
  })

  it('never_says_far_away_before_enough_speech', () => {
    const q = createMicQuality({ sampleRate: RATE })
    feedAll(q, dry(-41, 1)) // 0.5 s of quiet speech
    expect(q.state().farAway).toBe(false)
  })

  it('moving_closer_clears_it', () => {
    const q = createMicQuality({ sampleRate: RATE })
    feedAll(q, dry(-41, 5))
    expect(q.state().farAway).toBe(true)
    feedAll(q, dry(-10, 6))
    expect(q.state().farAway).toBe(false)
  })

  it('silence_after_far_speech_keeps_the_hint_instead_of_flickering', () => {
    const q = createMicQuality({ sampleRate: RATE })
    feedAll(q, dry(-41, 5))
    feedAll(q, Array<number>(250).fill(NOISE_DB))
    expect(q.state().farAway).toBe(true)
  })

  it('a_level_between_the_thresholds_keeps_the_last_answer', () => {
    const wasFar = createMicQuality({ sampleRate: RATE })
    feedAll(wasFar, dry(-41, 5))
    feedAll(wasFar, dry(-36, 6))
    expect(wasFar.state().farAway).toBe(true)

    const wasClose = createMicQuality({ sampleRate: RATE })
    feedAll(wasClose, dry(-10, 5))
    feedAll(wasClose, dry(-36, 6))
    expect(wasClose.state().farAway).toBe(false)
  })

  it('the_window_is_configurable', () => {
    const q = createMicQuality({ sampleRate: RATE, windowMs: 1000 })
    feedAll(q, dry(-41, 5))
    expect(q.state().farAway).toBe(false) // never 1.5 s of speech inside 1 s
  })

  it('never_throws_on_empty_or_odd_input', () => {
    const q = createMicQuality({ sampleRate: 0, windowMs: Number.NaN })
    expect(() => {
      q.feed(new Int16Array(0))
      q.feed(undefined as unknown as Int16Array)
      q.feed(new Int16Array(1).fill(-32768))
      q.feed(new Int16Array(7))
    }).not.toThrow()
    const s = q.state()
    expect(s.level).toBeGreaterThanOrEqual(0)
    expect(s.level).toBeLessThanOrEqual(1)
    expect(s.farAway).toBe(false)
  })
})
