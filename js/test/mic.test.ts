import { readFileSync } from 'node:fs'
import { describe, expect, it, vi } from 'vitest'

import { CAPTURE_PROCESSOR, looksBluetooth, micConstraints, openMic } from '../src/audio/mic.ts'

describe('mic', () => {
  // Bench split-5 (11-04): echo cancellation alone keeps the echo gain (-16 WER) and at 1-2.5 m beats the full
  // chain (noise suppression + AGC cost 1.4-1.6 WER and 1.5-3 name points), so those two stay off.
  it('browser_processing_is_echo_cancellation_only_by_default', () => {
    expect(micConstraints()).toEqual({
      audio: { channelCount: 1, echoCancellation: true, noiseSuppression: false, autoGainControl: false },
    })
    expect(micConstraints('dev1').audio).toMatchObject({ echoCancellation: true, deviceId: { exact: 'dev1' } })
  })

  it('processing_false_opts_out_for_raw_capture', () => {
    expect(micConstraints('dev1', false).audio).toEqual({
      channelCount: 1, echoCancellation: false, noiseSuppression: false, autoGainControl: false, deviceId: { exact: 'dev1' },
    })
  })

  it('bluetooth_headsets_are_recognised_by_label', () => {
    expect(looksBluetooth('AirPods Pro (Bluetooth)')).toBe(true)
    expect(looksBluetooth('Hands-Free AG Audio')).toBe(true)
    expect(looksBluetooth('MacBook Pro Microphone')).toBe(false)
  })

  it('the_worklet_registers_the_processor_the_mic_opens', () => {
    const src = readFileSync(new URL('../src/audio/capture-worklet.js', import.meta.url), 'utf8')
    expect(src).toContain(`registerProcessor('${CAPTURE_PROCESSOR}'`)
  })
})

interface ContextRecord { rate?: number, closed: boolean, resumed: boolean }

// Only what openMic touches; records each context's requested rate and lifecycle.
function stubBrowser(contexts: ContextRecord[], asked: MediaStreamConstraints[]): void {
  class FakeContext {
    state = 'suspended'
    sampleRate: number
    audioWorklet = { addModule: async (): Promise<void> => undefined }
    rec: ContextRecord
    constructor(opts?: { sampleRate?: number }) {
      this.sampleRate = opts?.sampleRate ?? 48000
      this.rec = { rate: opts?.sampleRate, closed: false, resumed: false }
      contexts.push(this.rec)
    }

    createMediaStreamSource(): { connect: () => void } { return { connect: () => undefined } }
    async resume(): Promise<void> { this.rec.resumed = true; this.state = 'running' }
    async close(): Promise<void> { this.rec.closed = true }
  }
  const stream = { getAudioTracks: () => [{ label: 'MacBook Pro Microphone' }], getTracks: () => [] }
  vi.stubGlobal('AudioContext', FakeContext)
  vi.stubGlobal('AudioWorkletNode', class { port = { onmessage: null } })
  vi.stubGlobal('navigator', { mediaDevices: { getUserMedia: async (c: MediaStreamConstraints) => { asked.push(c); return stream } } })
}

// the production browser test call works on laptop speakers with Chrome's full APM and one AudioContext for capture and
// playback (ui/src/core/realtime/voice-stream.ts); echoProfile 'browser' copies both.
describe('mic echoProfile browser', () => {
  it('turns_on_echo_cancellation_noise_suppression_and_agc', () => {
    expect(micConstraints(undefined, true, 'browser')).toEqual({
      audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true },
    })
    expect(micConstraints('dev1', true, 'browser').audio).toMatchObject({ noiseSuppression: true, deviceId: { exact: 'dev1' } })
  })

  it('opens_one_24k_context_and_shares_it_for_playback', async () => {
    const contexts: ContextRecord[] = []
    const asked: MediaStreamConstraints[] = []
    stubBrowser(contexts, asked)
    try {
      const shared = await openMic({ sampleRate: 16000, echoProfile: 'browser' })
      expect(asked[0]?.audio).toMatchObject({ echoCancellation: true, noiseSuppression: true, autoGainControl: true })
      expect(contexts).toEqual([{ rate: 24000, closed: false, resumed: true }])
      expect(shared.context).toBeDefined()
      shared.stop()
      expect(contexts[0]?.closed).toBe(true)
    } finally {
      vi.unstubAllGlobals()
    }
  })

  it('without_the_profile_nothing_changes', async () => {
    const contexts: ContextRecord[] = []
    const asked: MediaStreamConstraints[] = []
    stubBrowser(contexts, asked)
    try {
      const plain = await openMic({ sampleRate: 16000 })
      expect(plain.context).toBeUndefined()
      expect(contexts).toEqual([{ rate: undefined, closed: false, resumed: false }])
      expect(asked[0]?.audio).toMatchObject({ noiseSuppression: false, autoGainControl: false })
    } finally {
      vi.unstubAllGlobals()
    }
  })
})
