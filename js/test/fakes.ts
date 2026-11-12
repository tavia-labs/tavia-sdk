import type { Player } from '../src/audio/player.ts'
import type { Fetch } from '../src/transport/http.ts'
import type { SocketData, SocketFactory, SocketLike } from '../src/transport/socket.ts'

const OPEN = 1

// A socket double: records what the SDK sends (JSON parsed, binary as bytes), and lets a test play the server.
export class FakeSocket implements SocketLike {
  readyState = 0
  binaryType?: string
  sent: unknown[] = []
  onopen: (() => void) | null = null
  onmessage: ((e: { data: unknown }) => void) | null = null
  onclose: ((e: { code: number }) => void) | null = null
  onerror: (() => void) | null = null
  constructor(readonly url = '', readonly protocols: string[] = [], readonly headers?: Record<string, string>) {}
  send(data: SocketData): void {
    if (typeof data !== 'string') this.sent.push(new Uint8Array(ArrayBuffer.isView(data) ? data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength) : data))
    else this.sent.push(data === '' ? '' : JSON.parse(data))
  }
  close(code = 1000): void { this.readyState = 3; this.onclose?.({ code }) }
  open(): void { this.readyState = OPEN; this.onopen?.() }
  push(data: unknown): void { this.onmessage?.({ data: typeof data === 'object' && !(data instanceof ArrayBuffer) ? JSON.stringify(data) : data }) }
}

// A factory whose sockets open on the next tick; `last` is the newest socket.
export function fakeFactory(): SocketFactory & { last?: FakeSocket } {
  const make = ((url: string, protocols: string[], headers?: Record<string, string>) => {
    const s = new FakeSocket(url, protocols, headers)
    make.last = s
    queueMicrotask(() => s.open())
    return s
  }) as SocketFactory & { last?: FakeSocket }
  return make
}

export function openSocket(): FakeSocket {
  const s = new FakeSocket()
  s.readyState = OPEN
  return s
}

export function fakePlayer(): Player & { chunks: number, flushes: number, played: number } {
  const p = {
    chunks: 0, flushes: 0, played: 0,
    enqueue: () => { p.chunks++ },
    flush: () => { p.flushes++ },
    playedMs: () => p.played,
    close: async () => undefined,
  }
  return p
}

export interface Request { url: string, init: RequestInit }

// A fetch double: answers each call from `answers` in order and records the requests. An Error answer is a
// network failure; a third element gives response headers.
export type FakeAnswer = [number, unknown, Record<string, string>?] | Error

export function fakeFetch(answers: FakeAnswer[]): Fetch & { calls: Request[] } {
  const calls: Request[] = []
  const f = (async (url: string, init: RequestInit = {}) => {
    calls.push({ url, init })
    const answer = answers.shift() ?? [500, null]
    if (answer instanceof Error) throw answer
    const [status, body, headers] = answer
    return new Response(body === null ? null : JSON.stringify(body), { status, headers })
  }) as Fetch & { calls: Request[] }
  f.calls = calls
  return f
}
