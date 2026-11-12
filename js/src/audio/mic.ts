import { createPipeline } from './resample.ts'

/** The name the capture AudioWorklet processor registers under. */
export const CAPTURE_PROCESSOR = 'tavia-capture'
// ?no-inline: bundlers such as Vite would inline it as a data: script, which a strict script-src blocks.
const CAPTURE_URL = new URL('./capture-worklet.js?no-inline', import.meta.url)
// Device names a headset reports over Bluetooth; its narrowband mic hurts recognition, so the page warns.
const BLUETOOTH_LABEL = /bluetooth|airpods|hands-?free/i
/**
 * How the mic fights echo. `default`: echo cancellation only. `browser`: the browser's full processing (echo
 * cancellation, noise suppression, gain control) and one AudioContext for mic and playback; best on laptop speakers.
 */
export type EchoProfile = 'default' | 'browser'
const BROWSER_CONTEXT_RATE = 24000 // the agent's output rate, so the reply plays in it unresampled

/** Options for {@link openMic}. */
export interface MicOptions {
  /** The frame rate in Hz the server expects, e.g. 24000 or 16000 for realtime, 16000 for speech-to-text. */
  sampleRate: number
  /** The input device to use; defaults to the browser's choice. */
  deviceId?: string
  /** Echo cancellation and other browser processing (default true); false captures raw audio. */
  processing?: boolean
  /** How the mic fights echo (default `default`). */
  echoProfile?: EchoProfile
}

/** An open mic, from {@link openMic}. */
export interface MicStream {
  /** Calls `cb` with each 20 ms PCM16 frame; returns a function that stops it. */
  onFrame: (cb: (pcm: Int16Array) => void) => () => void
  /** Stops the mic and closes its AudioContext. */
  stop: () => void
  /** The mic's device label. */
  label: string
  /** The mic looks like a Bluetooth headset, whose narrowband mic hurts recognition. */
  isBluetooth: boolean
  /** With echoProfile `browser`: play the reply here (createPlayerOn); stop() closes it. */
  context?: AudioContext
}

/**
 * The getUserMedia constraints {@link openMic} uses. By default echo cancellation only: without it the reply echoes
 * back into recognition, while noise suppression and gain control slightly hurt it. processing:false is raw capture;
 * 'browser' turns all three on.
 */
export function micConstraints(deviceId?: string, processing = true, echoProfile: EchoProfile = 'default'): MediaStreamConstraints {
  const full = processing && echoProfile === 'browser'
  return {
    audio: {
      channelCount: 1,
      echoCancellation: processing,
      noiseSuppression: full,
      autoGainControl: full,
      ...(deviceId ? { deviceId: { exact: deviceId } } : {}),
    },
  }
}

/** Whether a device label looks like a Bluetooth headset. */
export function looksBluetooth(label: string): boolean {
  return BLUETOOTH_LABEL.test(label)
}

/**
 * Opens the browser mic and delivers 20 ms PCM16 mono frames at `opts.sampleRate`. Rejects with the browser's own
 * error, e.g. when the caller denies the mic.
 *
 * @example
 * const mic = await openMic({ sampleRate: 24000 })
 * const stop = mic.onFrame((pcm) => call.sendAudio(pcm))
 * // later: stop(); mic.stop()
 */
export async function openMic(opts: MicOptions): Promise<MicStream> {
  const shared = opts.echoProfile === 'browser'
  const stream = await navigator.mediaDevices.getUserMedia(micConstraints(opts.deviceId, opts.processing, opts.echoProfile))
  const audio = shared ? new AudioContext({ sampleRate: BROWSER_CONTEXT_RATE }) : new AudioContext()
  if (shared && audio.state === 'suspended') await audio.resume() // it plays the reply too
  await audio.audioWorklet.addModule(CAPTURE_URL)
  const node = new AudioWorkletNode(audio, CAPTURE_PROCESSOR)
  audio.createMediaStreamSource(stream).connect(node)
  const pipe = createPipeline(audio.sampleRate, opts.sampleRate)
  const listeners = new Set<(pcm: Int16Array) => void>()
  node.port.onmessage = (m: MessageEvent<Float32Array>) => {
    for (const frame of pipe(m.data)) for (const cb of listeners) cb(frame)
  }
  const label = stream.getAudioTracks()[0]?.label ?? ''
  return {
    label,
    isBluetooth: looksBluetooth(label),
    ...(shared ? { context: audio } : {}),
    onFrame: (cb) => { listeners.add(cb); return () => { listeners.delete(cb) } },
    stop: () => {
      node.port.onmessage = null
      for (const t of stream.getTracks()) t.stop()
      void audio.close()
    },
  }
}
