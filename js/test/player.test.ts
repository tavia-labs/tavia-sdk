import { describe, expect, it } from 'vitest'

import { createPlayer, createPlayerOn, type PlayerContext } from '../src/audio/player.ts'

interface FakeSource { start: (at: number) => void, stop: () => void, startedAt: number, stopped: boolean, duration: number }

// A clock-driven stand-in for an AudioContext: only what the player touches.
function fakeContext(): PlayerContext & { now: number, sources: FakeSource[] } {
  const ctx = {
    now: 0,
    sources: [] as FakeSource[],
    get currentTime(): number { return ctx.now },
    destination: {},
    createBuffer: (_ch: number, length: number, rate: number) => ({ duration: length / rate, getChannelData: () => new Float32Array(length) }),
    createBufferSource: () => {
      const s = {
        buffer: null as { duration: number } | null,
        startedAt: -1,
        stopped: false,
        get duration(): number { return s.buffer?.duration ?? 0 },
        connect: () => undefined,
        start: (at: number) => { s.startedAt = at },
        stop: () => { s.stopped = true },
        onended: null,
      }
      ctx.sources.push(s)
      return s
    },
    close: async () => undefined,
  }
  return ctx as unknown as PlayerContext & { now: number, sources: FakeSource[] }
}

const chunk = (ms: number): Int16Array => new Int16Array((24000 * ms) / 1000)

describe('player', () => {
  it('a_run_from_silence_starts_after_the_lead_and_back_to_back_chunks_follow', () => {
    const ctx = fakeContext()
    const p = createPlayer(24000, () => ctx, { leadMs: 60 })
    p.enqueue(chunk(100))
    p.enqueue(chunk(100))
    ctx.now = 0.5 // underrun: the next chunk opens a new run with the lead again
    p.enqueue(chunk(100))
    const at = ctx.sources.map((s) => Math.round(s.startedAt * 1000))
    expect(at).toEqual([60, 160, 560])
  })

  it('played_ms_ignores_the_lead_before_playback', () => {
    const ctx = fakeContext()
    const p = createPlayer(24000, () => ctx, { leadMs: 60 })
    p.enqueue(chunk(100))
    ctx.now = 0.03
    expect(p.playedMs()).toBe(0)
    ctx.now = 0.11
    expect(p.playedMs()).toBeCloseTo(50)
  })

  it('queues_chunks_back_to_back', () => {
    const ctx = fakeContext()
    const p = createPlayer(24000, () => ctx)
    p.enqueue(chunk(100))
    p.enqueue(chunk(100))
    expect(ctx.sources.map((s) => s.startedAt)).toEqual([0, 0.1])
  })

  it('played_ms_counts_only_played_samples', () => {
    const ctx = fakeContext()
    const p = createPlayer(24000, () => ctx)
    p.enqueue(chunk(200))
    ctx.now = 0.05
    expect(p.playedMs()).toBeCloseTo(50)
    ctx.now = 5
    expect(p.playedMs()).toBeCloseTo(200)
  })

  it('player_flush_drops_queued_audio', () => {
    const ctx = fakeContext()
    const p = createPlayer(24000, () => ctx)
    p.enqueue(chunk(100))
    p.enqueue(chunk(100))
    ctx.now = 0.05
    p.flush()
    expect(ctx.sources.every((s) => s.stopped)).toBe(true)
    expect(p.playedMs()).toBeCloseTo(50)
    p.enqueue(chunk(100))
    expect(ctx.sources.at(-1)?.startedAt).toBeCloseTo(0.05)
  })

  // echoProfile 'browser': playback in the mic's own AudioContext, which the mic closes, never the player.
  it('a_player_on_a_shared_context_plays_there_and_never_closes_it', async () => {
    const ctx = fakeContext()
    let closed = false
    ctx.close = async () => { closed = true }
    const p = createPlayerOn(ctx as unknown as AudioContext, 24000)
    p.enqueue(chunk(100))
    p.enqueue(chunk(100))
    expect(ctx.sources.map((s) => s.startedAt)).toEqual([0, 0.1])
    ctx.now = 0.05
    expect(p.playedMs()).toBeCloseTo(50)
    await p.close()
    expect(ctx.sources.every((s) => s.stopped)).toBe(true)
    expect(closed).toBe(false)
  })
})
