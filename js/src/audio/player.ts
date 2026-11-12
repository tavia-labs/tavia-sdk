// Plays reply audio chunk after chunk; flush() stops it at once for a barge-in.

const MS_PER_S = 1000
const PCM16_SCALE = 32768

/** The part of an AudioContext the player uses; pass your own to drive the clock in tests. */
export interface PlayerContext {
  readonly currentTime: number
  readonly destination: AudioNode
  createBuffer: (channels: number, length: number, rate: number) => AudioBuffer
  createBufferSource: () => AudioBufferSourceNode
  close: () => Promise<void>
}

/** Plays PCM16 audio, from {@link createPlayer} or {@link createPlayerOn}. */
export interface Player {
  /** Queues a chunk of PCM16 mono to play right after the previous one. */
  enqueue: (pcm: Int16Array) => void
  /** Stops playback at once and drops everything queued. */
  flush: () => void
  /** How much audio has played so far, in ms, across every chunk. */
  playedMs: () => number
  /** Stops playback and closes the AudioContext. */
  close: () => Promise<void>
}

/** Options for {@link createPlayer}. */
export interface PlayerOptions {
  /**
   * Jitter cushion in ms: audio that starts from silence (the first chunk, or after an underrun) starts this much
   * later, so one late network chunk does not cut the speech. 0 (default) plays at once.
   */
  leadMs?: number
}

/**
 * Plays the agent's audio chunk after chunk in a new AudioContext at `sampleRate`; flush() stops it at once.
 * Pass it as `player` when connecting so `call.interrupt()` also stops playback.
 *
 * @example
 * const player = createPlayer(24000)
 * const call = await tavia.realtime.connect({ player, session: { voice: 'elaine' } })
 */
export function createPlayer(sampleRate: number, makeContext: () => PlayerContext = () => new AudioContext({ sampleRate }),
  opts: PlayerOptions = {}): Player {
  const ctx = makeContext()
  const leadS = Math.max(0, opts.leadMs ?? 0) / MS_PER_S
  let sources: AudioBufferSourceNode[] = []
  let doneS = 0 // played before the current run of back-to-back chunks
  let runStart = 0
  let nextAt = 0

  const runPlayedS = (): number => Math.min(Math.max(ctx.currentTime - runStart, 0), nextAt - runStart)

  function enqueue(pcm: Int16Array): void {
    if (nextAt <= ctx.currentTime) {
      doneS += nextAt - runStart
      runStart = nextAt = ctx.currentTime + leadS
    }
    const buffer = ctx.createBuffer(1, pcm.length, sampleRate)
    const data = buffer.getChannelData(0)
    pcm.forEach((v, i) => { data[i] = v / PCM16_SCALE })
    const src = ctx.createBufferSource()
    src.buffer = buffer
    src.connect(ctx.destination)
    src.start(nextAt)
    src.onended = () => { sources = sources.filter((s) => s !== src) }
    sources.push(src)
    nextAt += buffer.duration
  }

  function flush(): void {
    for (const s of sources) s.stop()
    sources = []
    doneS += runPlayedS()
    runStart = nextAt = ctx.currentTime
  }

  return {
    enqueue,
    flush,
    playedMs: () => (doneS + runPlayedS()) * MS_PER_S,
    close: () => { flush(); return ctx.close() },
  }
}

/** A player in an AudioContext it does not own (the mic's, with echoProfile 'browser'): close() only stops playback. */
export function createPlayerOn(ctx: AudioContext, sampleRate: number, opts: PlayerOptions = {}): Player {
  return createPlayer(sampleRate, () => ({
    get currentTime(): number { return ctx.currentTime },
    destination: ctx.destination,
    createBuffer: (channels, length, rate) => ctx.createBuffer(channels, length, rate),
    createBufferSource: () => ctx.createBufferSource(),
    close: async () => undefined,
  }), opts)
}
