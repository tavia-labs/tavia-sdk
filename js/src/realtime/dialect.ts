import { DIALECT } from '../generated/spec.ts'
import type { SessionConfig, WireSession } from '../generated/types.ts'

/**
 * The wire dialect of a realtime session. `ga` is the standard event names and session shape (the default);
 * `beta` keeps the earlier names and the flat session, for integrations written against it.
 */
export type Dialect = 'ga' | 'beta'

/** A `beta` server event type that has a different standard name. */
export type RenamedEventType = keyof typeof DIALECT.renames

const RENAMES: Readonly<Record<string, string>> = DIALECT.renames
const SESSION_PATHS: Readonly<Record<string, string>> = DIALECT.sessionPaths

/** The standard name of a server event type: `beta` names map to their standard ones, others are unchanged. */
export function standardType(type: string): string {
  return RENAMES[type] ?? type
}

/** The event with its type under its standard name. */
export function standardEvent<T extends { type: string }>(event: T): T {
  const type = standardType(event.type)
  return type === event.type ? event : { ...event, type }
}

const pathOf = (key: string): string[] => (SESSION_PATHS[key] ?? `${DIALECT.extrasKey}.${key}`).split('.')

function setAt(target: Record<string, unknown>, path: string[], value: unknown): void {
  let node = target
  for (const key of path.slice(0, -1)) node = (node[key] ??= {}) as Record<string, unknown>
  node[path[path.length - 1] as string] = value
}

/**
 * A session's options in the standard shape: audio settings under `audio`, Tavia's own options under `tavia`.
 * `withEvents` also asks for the turn events, which the friendly events are built from.
 */
export function wireSession(session: Partial<SessionConfig>, withEvents = false): WireSession {
  const out: Record<string, unknown> = { type: 'realtime' }
  for (const [key, value] of Object.entries(session)) setAt(out, pathOf(key), value)
  if (withEvents) setAt(out, [DIALECT.extrasKey, DIALECT.extrasField], true)
  return out as WireSession
}
