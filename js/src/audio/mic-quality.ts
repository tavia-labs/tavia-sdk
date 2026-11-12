// A meter level and a "you sound far away" cue from openMic's PCM16 frames. Pure math: no Web Audio needed.
const FULL_SCALE = 32768
const DEFAULT_RATE = 16000
const DEFAULT_WINDOW_MS = 4000
const SILENCE_DB = -100 // an all-zero frame
const LEVEL_FLOOR_DB = -60 // the meter's zero
/** The share of quietest frames taken as the room's noise floor. */
export const NOISE_PERCENTILE = 0.1
const VOICE_MIN_DB = -55 // never speech below this
const VOICE_OVER_NOISE_DB = 10 // speech stands this far above the room...
const VOICE_SURE_DB = -30 // ...or is simply this loud
const MIN_VOICED_MS = 1500 // no verdict on less speech than this
/** A median speech level below this (dBFS) sounds far away. */
export const QUIET_ON_DB = -38
const QUIET_OFF_DB = -34 // above this: close again; the gap stops flicker
// Reverb: 60-200 ms after a speech offset, a dry room has fallen well over TAIL_DROP_DB; a far speaker's tail has not.
const PEAK_PERCENTILE = 0.9
const OFFSET_DB = 3 // the offset is the run's last frame within this of its peak
const TAIL_START_MS = 60
const TAIL_END_MS = 200
const TAIL_DROP_DB = 12
const MIN_RUN_MS = 100
const MIN_SNR_DB = 20 // offsets nearer the room than this say nothing about it
const REVERB_MIN_OFFSETS = 3
const REVERB_ON_SHARE = 0.5
const REVERB_OFF_SHARE = 0.25

/** Options for {@link createMicQuality}. */
export interface MicQualityOptions {
  /** The frames' sample rate in Hz (default 16000). */
  sampleRate?: number
  /** How much recent audio the verdict looks at, in ms (default 4000). */
  windowMs?: number
}

/** The mic's current state. */
export interface MicQualityState {
  /** The last frame's level from 0 to 1, for a meter. */
  level: number
  /** The last frame sounds like speech. */
  speaking: boolean
  /** The caller sounds far from the mic: quiet or echoey speech. */
  farAway: boolean
}

/** A live mic meter, from {@link createMicQuality}. */
export interface MicQuality {
  /** Feeds one PCM16 frame from `openMic`. */
  feed: (pcm: Int16Array) => void
  /** The current state; cheap to call every frame. */
  state: () => MicQualityState
}

interface Frame { db: number, ms: number }
interface Reverb { offsets: number, slow: number }

const positive = (n: number | undefined, fallback: number): number => (n !== undefined && Number.isFinite(n) && n > 0 ? n : fallback)

/** A frame's RMS level in dBFS; -100 for silence, NaN for a frame that holds non-numbers. */
export function frameDb(pcm: ArrayLike<number>): number {
  let sum = 0
  for (let i = 0; i < pcm.length; i++) sum += (pcm[i] ?? 0) ** 2
  const rms = Math.sqrt(sum / pcm.length)
  if (!Number.isFinite(rms)) return Number.NaN
  return rms > 0 ? 20 * Math.log10(rms / FULL_SCALE) : SILENCE_DB
}

/** The `p` (0..1) percentile of `values`; -100 when empty. */
export function percentile(values: number[], p: number): number {
  const sorted = [...values].sort((a, b) => a - b)
  return sorted[Math.floor(p * (sorted.length - 1))] ?? SILENCE_DB
}

/** The level above which a frame counts as speech, given the room's noise floor in `frames`. */
export function voiceThreshold(frames: Array<{ db: number }>): number {
  const floor = percentile(frames.map((f) => f.db), NOISE_PERCENTILE)
  return Math.max(VOICE_MIN_DB, Math.min(floor + VOICE_OVER_NOISE_DB, VOICE_SURE_DB))
}

// Mean level 60-200 ms after frame `at`; undefined when the window ends first or a new word starts in it.
function tailDb(frames: Frame[], at: number, ceiling: number): number | undefined {
  let elapsed = 0
  const tail: number[] = []
  for (let j = at + 1; j < frames.length && elapsed < TAIL_END_MS; j++) {
    const f = frames[j] as Frame
    if (elapsed >= TAIL_START_MS) tail.push(f.db)
    elapsed += f.ms
  }
  if (elapsed < TAIL_END_MS || tail.length === 0 || Math.max(...tail) >= ceiling) return undefined
  return tail.reduce((a, b) => a + b, 0) / tail.length
}

// Whether one voiced run [start, end] ends in a slow tail; undefined when it cannot tell.
function slowOffset(frames: Frame[], start: number, end: number, floor: number): boolean | undefined {
  const run = frames.slice(start, end + 1)
  if (run.reduce((ms, f) => ms + f.ms, 0) < MIN_RUN_MS) return undefined
  const peak = percentile(run.map((f) => f.db), PEAK_PERCENTILE)
  if (peak - floor < MIN_SNR_DB) return undefined
  let at = end
  while (at > start && (frames[at] as Frame).db < peak - OFFSET_DB) at--
  const tail = tailDb(frames, at, peak - OFFSET_DB)
  return tail === undefined ? undefined : peak - tail < TAIL_DROP_DB
}

function reverb(frames: Frame[], voiced: boolean[], floor: number): Reverb {
  const out = { offsets: 0, slow: 0 }
  let start = -1
  for (let i = 0; i < frames.length; i++) {
    if (voiced[i] && start < 0) start = i
    if (voiced[i] || start < 0) continue
    const slow = slowOffset(frames, start, i - 1, floor)
    start = -1
    if (slow === undefined) continue
    out.offsets++
    if (slow) out.slow++
  }
  return out
}

// undefined = not enough speech yet: keep the last answer. The on/off gaps are the hysteresis.
function verdict(frames: Frame[], farAway: boolean): boolean | undefined {
  const threshold = voiceThreshold(frames)
  const voiced = frames.map((f) => f.db >= threshold)
  const speech = frames.filter((_, i) => voiced[i])
  if (speech.reduce((ms, f) => ms + f.ms, 0) < MIN_VOICED_MS) return undefined
  const median = percentile(speech.map((f) => f.db), 0.5)
  const r = reverb(frames, voiced, percentile(frames.map((f) => f.db), NOISE_PERCENTILE))
  const share = r.offsets >= REVERB_MIN_OFFSETS ? r.slow / r.offsets : 0
  if (!farAway) return median < QUIET_ON_DB || share >= REVERB_ON_SHARE
  return !(median > QUIET_OFF_DB && share < REVERB_OFF_SHARE)
}

/** Starts a live mic meter with a "you sound far away" cue. Feed every frame; bad input is ignored, never thrown. */
export function createMicQuality(opts: MicQualityOptions = {}): MicQuality {
  const rate = positive(opts.sampleRate, DEFAULT_RATE)
  const windowMs = positive(opts.windowMs, DEFAULT_WINDOW_MS)
  const frames: Frame[] = []
  let windowTotal = 0
  let current: MicQualityState = { level: 0, speaking: false, farAway: false }

  const feed = (pcm: Int16Array): void => {
    if (!ArrayBuffer.isView(pcm) || pcm.length === 0) return
    const db = frameDb(pcm)
    if (Number.isNaN(db)) return
    const ms = (pcm.length / rate) * 1000
    frames.push({ db, ms })
    windowTotal += ms
    while (windowTotal > windowMs && frames.length > 1) windowTotal -= (frames.shift() as Frame).ms
    const level = Math.min(1, Math.max(0, (db - LEVEL_FLOOR_DB) / -LEVEL_FLOOR_DB))
    const farAway = verdict(frames, current.farAway) ?? current.farAway
    current = { level, speaking: db >= voiceThreshold(frames), farAway }
  }

  return { feed, state: () => current }
}
