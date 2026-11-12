import { describe, expect, it } from 'vitest'

import { createPipeline, CUTOFF_RATIO, lowpassTaps, Resampler, TAPS, tapsFor } from '../src/audio/resample.ts'

// Ported from the old playground's audio tests; the output rate is now a parameter (16 kHz STT, 24 kHz voice).
function blocks(rate: number, seconds: number, f: (t: number) => number): Float32Array[] {
  const out: Float32Array[] = []
  const total = Math.round(rate * seconds)
  for (let start = 0; start < total; start += 128) {
    const b = new Float32Array(Math.min(128, total - start))
    for (let i = 0; i < b.length; i++) b[i] = f((start + i) / rate)
    out.push(b)
  }
  return out
}

const rms = (a: number[]): number => Math.sqrt(a.reduce((t, x) => t + x * x, 0) / a.length)
const db = (x: number): number => 20 * Math.log10(x / Math.SQRT1_2)

function toneOut(inRate: number, hz: number, outRate = 16000): number[] {
  const r = new Resampler(inRate, outRate)
  return blocks(inRate, 1, (t) => Math.sin(2 * Math.PI * hz * t)).flatMap((b) => [...r.process(b)]).slice(200)
}

describe('resample', () => {
  it('a_48k_input_becomes_20ms_pcm16_frames', () => {
    const pipe = createPipeline(48000, 16000)
    const frames = blocks(48000, 1, () => 0.5).flatMap((b) => pipe(b))
    expect(frames.length).toBeGreaterThanOrEqual(49)
    expect(frames.length).toBeLessThanOrEqual(50)
    for (const f of frames) expect(f.length).toBe(320)
    expect(Math.abs((frames[1]?.[0] ?? 0) - 16384)).toBeLessThanOrEqual(1)
  })

  it('a_24k_pipeline_frames_480_samples', () => {
    const frames = blocks(48000, 1, () => 0.1).flatMap(createPipeline(48000, 24000))
    expect(frames[0]?.length).toBe(480)
    expect(frames.length).toBeGreaterThanOrEqual(49)
  })

  it('keeps_the_pitch_of_a_1khz_tone_across_block_edges', () => {
    const r = new Resampler(48000, 16000)
    const out = blocks(48000, 1, (t) => Math.sin(2 * Math.PI * 1000 * t)).flatMap((b) => [...r.process(b)])
    expect(Math.abs(out.length - 16000)).toBeLessThanOrEqual(1)
    let crossings = 0
    for (let i = 1; i < out.length; i++) if (((out[i - 1] ?? 0) < 0) !== ((out[i] ?? 0) < 0)) crossings++
    expect(Math.abs(crossings - 2000)).toBeLessThanOrEqual(4)
  })

  it('44_1k_and_16k_devices_give_the_right_sample_count', () => {
    for (const rate of [44100, 16000]) {
      const r = new Resampler(rate, 16000)
      const n = blocks(rate, 1, () => 0.1).reduce((s, b) => s + r.process(b).length, 0)
      expect(Math.abs(n - 16000)).toBeLessThanOrEqual(1)
    }
  })

  it('samples_are_clipped_not_wrapped', () => {
    expect(createPipeline(16000, 16000)(new Float32Array(320).fill(2))[0]?.[0]).toBe(32767)
    expect(createPipeline(16000, 16000)(new Float32Array(320).fill(-2))[0]?.[0]).toBe(-32768)
  })

  it('the_low_pass_has_unity_dc_gain_and_scales_with_rate', () => {
    expect(lowpassTaps(48000, 16000).length).toBe(TAPS)
    expect(Math.abs(lowpassTaps(48000, 16000).reduce((a, b) => a + b, 0) - 1)).toBeLessThan(1e-9)
    expect(tapsFor(44100)).toBe(44)
    expect(tapsFor(96000)).toBe(96)
    expect(CUTOFF_RATIO).toBeCloseTo(0.45)
  })

  it('an_aliasing_tone_comes_out_40db_down', () => {
    expect(db(rms(toneOut(48000, 12000)))).toBeLessThanOrEqual(-40)
    expect(db(rms(toneOut(44100, 11000)))).toBeLessThanOrEqual(-40)
    expect(db(rms(toneOut(48000, 16000, 24000)))).toBeLessThanOrEqual(-40)
  })

  it('a_1khz_tone_passes_within_1db', () => {
    for (const rate of [48000, 44100]) expect(Math.abs(db(rms(toneOut(rate, 1000))))).toBeLessThanOrEqual(1)
  })

  it('block_wise_output_equals_one_shot_output', () => {
    const sig = blocks(48000, 0.5, (t) => Math.sin(2 * Math.PI * 440 * t))
    const whole = new Float32Array(sig.reduce((n, b) => n + b.length, 0))
    let o = 0
    for (const b of sig) { whole.set(b, o); o += b.length }
    const oneShot = [...new Resampler(48000, 16000).process(whole)]
    const r = new Resampler(48000, 16000)
    const sizes = [1, 7, 128, 333, 2]
    const blockwise: number[] = []
    for (let i = 0, k = 0; i < whole.length; k++) {
      const n = sizes[k % sizes.length] ?? 1
      blockwise.push(...r.process(whole.subarray(i, i + n)))
      i += n
    }
    expect(blockwise).toEqual(oneShot)
  })
})
