// Device rate -> server rate: a windowed-sinc low-pass evaluated only where linear interpolation needs it,
// then 20 ms PCM16 frames at any output rate.

/** Low-pass filter length at 48 kHz input; the length scales with the input rate (see {@link tapsFor}). */
export const TAPS = 48
/** The filter cutoff as a share of the output rate: under Nyquist, with room for the transition band. */
export const CUTOFF_RATIO = 0.45
/** The length of each output frame, in ms. */
export const FRAME_MS = 20
const REF_RATE = 48000
const MS_PER_S = 1000

/** The low-pass filter length for an input rate: {@link TAPS} scaled from 48 kHz, even, at least 2. */
export function tapsFor(inRate: number): number {
  return Math.max(2, 2 * Math.round((TAPS * inRate) / REF_RATE / 2))
}

/** Low-pass filter coefficients for a rate drop: a Blackman-windowed sinc with unity gain at DC. */
export function lowpassTaps(inRate: number, outRate: number, taps = tapsFor(inRate)): number[] {
  const fc = (CUTOFF_RATIO * outRate) / inRate
  const mid = (taps - 1) / 2
  const h = Array.from({ length: taps }, (_, n) => {
    const x = n - mid
    const sinc = x === 0 ? 2 * fc : Math.sin(2 * Math.PI * fc * x) / (Math.PI * x)
    const w = 0.42 - 0.5 * Math.cos((2 * Math.PI * n) / (taps - 1)) + 0.08 * Math.cos((4 * Math.PI * n) / (taps - 1))
    return sinc * w
  })
  const sum = h.reduce((a, b) => a + b, 0)
  return h.map((v) => v / sum)
}

/**
 * Converts float audio from one sample rate to another, low-passing first on a rate drop. It streams sample by
 * sample, so any split of the input into blocks gives the same output.
 */
export class Resampler {
  private readonly step: number
  private readonly h: number[]
  private readonly size: number
  private readonly ring: Float64Array
  private m = -1 // index of the newest input sample
  private t = 0 // next output position, in input samples
  private cacheAt = -1
  private cacheY = 0

  /** Rates in Hz. */
  constructor(inRate: number, outRate: number) {
    this.step = inRate / outRate
    // Only a rate drop can alias; otherwise samples go straight to the interpolator.
    this.h = inRate > outRate ? lowpassTaps(inRate, outRate) : [1]
    this.size = this.h.length + 1
    this.ring = new Float64Array(this.size)
  }

  private y(j: number): number {
    if (j === this.cacheAt) return this.cacheY
    const n = this.size
    let acc = 0
    for (let k = 0; k < this.h.length; k++) acc += (this.h[k] ?? 0) * (this.ring[(((j - k) % n) + n) % n] ?? 0)
    this.cacheAt = j
    this.cacheY = acc
    return acc
  }

  /** Resamples one block; returns the output samples it completes. */
  process(input: Float32Array): Float32Array {
    const out = new Float32Array(Math.ceil(input.length / this.step) + 2)
    let n = 0
    for (const sample of input) {
      const m = ++this.m
      this.ring[m % this.size] = sample
      for (;;) {
        const i = Math.floor(this.t)
        const f = this.t - i
        if (i > m || (i === m && f !== 0)) break
        const a = this.y(i)
        out[n++] = f === 0 ? a : a + (this.y(i + 1) - a) * f
        this.t += this.step
      }
    }
    return out.subarray(0, n)
  }
}

/** Cuts float samples into fixed-size PCM16 frames, clipped rather than wrapped. */
export class Framer {
  private buf: Int16Array
  private fill = 0

  /** `frameSamples` is the number of samples in each frame. */
  constructor(private readonly frameSamples: number) {
    this.buf = new Int16Array(frameSamples)
  }

  /** Adds samples; returns every frame they complete (possibly none). */
  push(samples: Float32Array): Int16Array[] {
    const frames: Int16Array[] = []
    for (const s of samples) {
      const c = Math.max(-1, Math.min(1, s))
      this.buf[this.fill] = c < 0 ? Math.round(c * 32768) : Math.round(c * 32767)
      if (++this.fill === this.frameSamples) {
        frames.push(this.buf)
        this.buf = new Int16Array(this.frameSamples)
        this.fill = 0
      }
    }
    return frames
  }
}

/** Resamples float blocks from `inRate` to `outRate` and cuts them into 20 ms PCM16 frames. */
export function createPipeline(inRate: number, outRate: number): (block: Float32Array) => Int16Array[] {
  const r = new Resampler(inRate, outRate)
  const f = new Framer((outRate * FRAME_MS) / MS_PER_S)
  return (block) => f.push(r.process(block))
}
