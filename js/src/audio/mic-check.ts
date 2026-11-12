// A pre-call check: is the caller heard, close enough, in a quiet room, and does the speaker reach the mic?
// Advice only; nothing here may stop a call. Pure math on openMic's frames plus the device labels.
import { looksBluetooth } from './mic.ts'
import { createMicQuality, frameDb, NOISE_PERCENTILE, percentile, QUIET_ON_DB, voiceThreshold } from './mic-quality.ts'

const DEFAULT_RATE = 16000
const WINDOW_MS = 12000 // the whole check, not the call meter's 4 s
const MIN_HEARD_MS = 500
const ECHO_RISE_DB = 6 // the chime lifts the mic this far over the room: the speaker reaches it
const MIN_SNR_DB = 15 // voice under this over the room: noisy
const NOISY_ROOM_DB = -45 // no voice heard, and the room alone is this loud
// Headset first: a label like "Headphones (USB Audio)" names headphones, not the sound card's speaker.
const HEADSET_LABEL = /head(phone|set)|earphone|ear ?buds?|earpods|airpods|buds|hands-?free|bluetooth/i
const SPEAKER_LABEL = /speaker|built-?in|internal|laptop|macbook|display audio/i

/** What plays the agent's audio, judged from the device label. */
export type AudioOutputKind = 'speaker' | 'headset' | 'unknown'
/** One piece of advice for the caller; a result lists the most important first. */
export type MicAdvice = 'not_heard' | 'use_earphones' | 'move_closer' | 'quieter_room' | 'avoid_bluetooth'

/** The device labels a check judges by: the mic's track label and the playback device's label. */
export interface MicCheckDevices { micLabel?: string, outputLabel?: string }

/** What a mic check found. */
export interface MicCheckResult {
  /** Enough speech was heard (at least half a second). */
  heard: boolean
  /** The caller sounds far from the mic. */
  farAway: boolean
  /** The room is loud next to the voice, or loud on its own when no voice was heard. */
  noisy: boolean
  /** The chime reached the mic through the speaker; undefined when no chime was played. */
  echo: boolean | undefined
  /** What plays the agent's audio; `speaker` whenever the chime echoed. */
  output: AudioOutputKind
  /** The mic looks like a Bluetooth headset, whose narrowband mic hurts recognition. */
  bluetooth: boolean
  /** Voice over the room in dB, when heard: a page can tell a borderline room from a loud one. */
  snrDb: number | undefined
  /** What to tell the caller, most important first; `[]` means good to go. */
  advice: MicAdvice[]
}

/** A running mic check, from {@link createMicCheck}. */
export interface MicCheck {
  /** Feeds one PCM16 frame from `openMic`. */
  feed: (pcm: Int16Array) => void
  /** Marks when a chime plays: frames fed meanwhile measure echo, not the room. */
  tone: (on: boolean) => void
  /** The verdict on everything fed so far. */
  result: (devices?: MicCheckDevices) => MicCheckResult
}

/** Guesses a playback device's kind from its label; headset labels win over speaker labels. */
export function outputKind(label: string): AudioOutputKind {
  if (HEADSET_LABEL.test(label)) return 'headset'
  return SPEAKER_LABEL.test(label) ? 'speaker' : 'unknown'
}

/** The default playback device and its kind by label; browsers that list no output devices give `unknown`, never an error. */
export async function detectAudioOutput(
  md: Pick<MediaDevices, 'enumerateDevices'> | undefined = globalThis.navigator?.mediaDevices,
): Promise<{ kind: AudioOutputKind, label: string }> {
  try {
    const outs = (await (md as Pick<MediaDevices, 'enumerateDevices'>).enumerateDevices()).filter((d) => d.kind === 'audiooutput')
    const label = (outs.find((d) => d.deviceId === 'default') ?? outs[0])?.label ?? ''
    return { kind: outputKind(label), label }
  } catch {
    return { kind: 'unknown', label: '' }
  }
}

interface Frame { db: number, ms: number }

function adviceFor(r: Omit<MicCheckResult, 'advice'>): MicAdvice[] {
  const out: MicAdvice[] = []
  if (!r.heard) out.push('not_heard')
  if (r.output === 'speaker') out.push('use_earphones')
  if (r.farAway) out.push('move_closer')
  if (r.noisy) out.push('quieter_room')
  if (r.bluetooth) out.push('avoid_bluetooth')
  return out
}

/**
 * Starts a pre-call mic check over up to 12 s of audio. Feed every frame; mark a chime with tone(true/false).
 * `sampleRate` (default 16000) must match the frames. Bad input is ignored, never thrown.
 */
export function createMicCheck(opts: { sampleRate?: number } = {}): MicCheck {
  const rate = opts.sampleRate !== undefined && opts.sampleRate > 0 ? opts.sampleRate : DEFAULT_RATE
  const quality = createMicQuality({ sampleRate: rate, windowMs: WINDOW_MS })
  const room: Frame[] = []
  const chime: number[] = []
  let toneOn = false

  const feed = (pcm: Int16Array): void => {
    if (!ArrayBuffer.isView(pcm) || pcm.length === 0) return
    const db = frameDb(pcm)
    if (Number.isNaN(db)) return
    if (toneOn) { chime.push(db); return }
    room.push({ db, ms: (pcm.length / rate) * 1000 })
    quality.feed(pcm)
  }

  const result = (devices: MicCheckDevices = {}): MicCheckResult => {
    const threshold = voiceThreshold(room)
    const voiced = room.filter((f) => f.db >= threshold)
    const heard = voiced.reduce((ms, f) => ms + f.ms, 0) >= MIN_HEARD_MS
    const floor = percentile(room.map((f) => f.db), NOISE_PERCENTILE)
    const median = percentile(voiced.map((f) => f.db), 0.5)
    const echo = chime.length ? percentile(chime, 0.5) - floor >= ECHO_RISE_DB : undefined
    const r = {
      heard,
      farAway: heard && (quality.state().farAway || median < QUIET_ON_DB),
      noisy: heard ? median - floor < MIN_SNR_DB : floor > NOISY_ROOM_DB,
      echo,
      output: echo ? 'speaker' as const : outputKind(devices.outputLabel ?? ''),
      bluetooth: looksBluetooth(devices.micLabel ?? ''),
      snrDb: heard ? Math.round(median - floor) : undefined,
    }
    return { ...r, advice: adviceFor(r) }
  }

  return { feed, tone: (on) => { toneOn = on }, result }
}
