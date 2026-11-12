import type { Player } from '../audio/player.ts'
import { DIALECT, LAYERS, PRESET_PARAM } from '../generated/spec.ts'
import type { SessionConfig } from '../generated/types.ts'
import { openSocket, type Auth, type SocketFactory } from '../transport/socket.ts'
import { DEFAULT_URLS } from '../transport/urls.ts'
import { Call } from './call.ts'
import type { Dialect } from './dialect.ts'

export { ConnectError } from '../errors.ts'
export type { SocketFactory } from '../transport/socket.ts'
/** How a realtime session authenticates: an API key (servers) or a short-lived token (browsers). */
export type CallAuth = Auth

/** The realtime endpoint on the public API. */
export const REALTIME_URL = DEFAULT_URLS.realtime

/** Options for {@link connectCall}. */
export interface ConnectOptions {
  /** An API key (servers only) or a short-lived browser token. */
  auth: Auth
  /** The realtime endpoint; defaults to the public API. */
  url?: string
  /** A saved agent configuration to start from. */
  preset?: string
  /** Session options sent as soon as the socket opens. */
  session?: Partial<SessionConfig>
  /** The `session` string `tokens.create` returned for a bound session: sent first, unchanged. */
  boundSession?: string
  /** Plays the agent's audio. */
  player?: Player
  /** Opens the WebSocket; defaults to the browser's, or the `ws` package in Node. */
  socket?: SocketFactory
  /** @deprecated Only for integrations written against the older event names; defaults to `ga`. */
  dialect?: Dialect
}

function sessionUrl(base: string, dialect: Dialect, preset?: string): string {
  const url = new URL(base)
  url.searchParams.set(DIALECT.param, dialect)
  if (preset) url.searchParams.set(PRESET_PARAM, preset)
  return url.toString()
}

/**
 * Opens a realtime session and sends its first session update. Most apps call `tavia.realtime.connect` instead.
 * Rejects with ConnectError when the server cannot be reached or refuses the session.
 *
 * @example
 * const call = await connectCall({ auth: { token }, session: { voice: 'elaine', instructions: 'Be brief.' } })
 */
export async function connectCall(opts: ConnectOptions): Promise<Call> {
  const dialect = opts.dialect ?? DIALECT.value
  const url = sessionUrl(opts.url ?? REALTIME_URL, dialect, opts.preset)
  const socket = await openSocket(url, LAYERS.voice.subprotocol, opts.auth, opts.socket)
  const call = new Call(socket, { player: opts.player, dialect })
  if (opts.boundSession !== undefined) call.update({ bound: opts.boundSession })
  if (opts.session) call.update(opts.session)
  // The friendly events need the server's turn events, which the first update turns on.
  if (dialect === 'ga' && opts.boundSession === undefined && !opts.session) call.update({})
  return call
}
