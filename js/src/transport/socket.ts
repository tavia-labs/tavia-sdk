import { ConnectError, SessionClosedError } from '../errors.ts'
import { TOKEN_SUBPROTOCOL_PREFIX } from '../generated/spec.ts'

const OPEN = 1

/** Data a socket can send: text or binary. */
export type SocketData = string | ArrayBuffer | ArrayBufferView

/** The part of a WebSocket the SDK uses: the browser's, the `ws` package's, or a test double. */
export interface SocketLike {
  /** The WebSocket ready state; 1 is open. */
  readonly readyState: number
  /** Set to `arraybuffer` by the SDK so binary frames arrive as ArrayBuffers. */
  binaryType?: string
  /** Sends one frame. */
  send: (data: SocketData) => void
  /** Closes the socket. */
  close: (code?: number) => void
  /** Called once the socket opens. */
  onopen: (() => void) | null
  /** Called for each frame received. */
  onmessage: ((e: { data: unknown }) => void) | null
  /** Called once the socket closes, with the close code. */
  onclose: ((e: { code: number }) => void) | null
  /** Called on a socket error; a close always follows. */
  onerror: (() => void) | null
}

/** Opens a WebSocket; `headers` is set only when connecting with an API key (servers). */
export type SocketFactory = (url: string, protocols: string[], headers?: Record<string, string>) => SocketLike

/** How the SDK authenticates: a server holds an API key; a browser holds a short-lived token. */
export type Auth = { apiKey: string } | { token: string }

/** Whether the socket is open. */
export const isOpen = (s: SocketLike): boolean => s.readyState === OPEN

/** Sends, or throws SessionClosedError: nothing sent on a closed or closing socket is dropped silently. */
export function sendOpen(socket: SocketLike, data: SocketData, closeCode: number | null = null): void {
  if (!isOpen(socket)) throw new SessionClosedError(closeCode)
  socket.send(data)
}

const inBrowser = (): boolean => typeof window !== 'undefined'

/** Throws when an API key would be used in a browser, where anyone could read it; pages use a short-lived token. */
export function assertKeyOnServer(auth: Auth): void {
  if ('apiKey' in auth && inBrowser()) {
    throw new TypeError('API keys are for your server only; in a browser, connect with a token from tokens.create')
  }
}

/** The `Authorization` header for an API key or token. */
export function authHeaders(auth: Auth): Record<string, string> {
  return { Authorization: `Bearer ${'apiKey' in auth ? auth.apiKey : auth.token}` }
}

const browserSocket: SocketFactory = (url, protocols) => new WebSocket(url, protocols) as unknown as SocketLike

// Node has no WebSocket that sends headers: the optional `ws` package does.
async function nodeSocket(): Promise<SocketFactory> {
  const name = 'ws'
  const mod = await import(/* @vite-ignore */ name).catch(() => {
    throw new Error('install the ws package, or pass a socket factory, to connect with an API key')
  }) as { default: new (u: string, p: string[], o: object) => SocketLike }
  return (url, protocols, headers) => new mod.default(url, protocols, { headers })
}

function waitOpen(socket: SocketLike): Promise<void> {
  return new Promise((resolve, reject) => {
    socket.onopen = () => resolve()
    socket.onclose = (e) => reject(new ConnectError(e.code))
  })
}

/**
 * Opens a socket and waits for it: an API key rides as a Bearer header, a token as the second subprotocol.
 * Rejects with ConnectError when the socket closes before it opens.
 */
export async function openSocket(url: string, subprotocol: string, auth: Auth, factory?: SocketFactory): Promise<SocketLike> {
  let socket: SocketLike
  assertKeyOnServer(auth)
  if ('apiKey' in auth) {
    socket = (factory ?? await nodeSocket())(url, [subprotocol], authHeaders(auth))
  } else {
    socket = (factory ?? browserSocket)(url, [subprotocol, `${TOKEN_SUBPROTOCOL_PREFIX}${auth.token}`])
  }
  socket.binaryType = 'arraybuffer'
  await waitOpen(socket)
  return socket
}

/** A binary frame's bytes, or null for a text frame. */
export function toBytes(data: unknown): Uint8Array | null {
  if (data instanceof ArrayBuffer) return new Uint8Array(data)
  if (ArrayBuffer.isView(data)) return new Uint8Array(data.buffer, data.byteOffset, data.byteLength)
  return null
}
