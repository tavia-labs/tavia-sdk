// GENERATED from the API specification. Do not edit.
import { CONSTANTS } from './checker-spec.ts'

const S = CONSTANTS.realtime.toolSchema
const PROPERTIES = 'properties'
const PATTERN = 'pattern'
// RE2 runs in linear time, so it has no lookaround or backreferences; JS would accept them.
const NOT_LINEAR = /\(\?<?[=!]|\\[1-9]|\\k</
const SUBSET = S.patternSubset
const HEX = /^[0-9a-fA-F]{2}$/
const SHORTHAND =
  'patterns cannot use \\d, \\w, \\s or \\b (they match differently across engines); write the class, such as [0-9]'

// Keys in sort order (UTF-16 code units, as the Python checker sorts them): JS would list integer-like keys first.
export const sortedKeys = (node: Record<string, unknown>): string[] => Object.keys(node).sort()

// Why a pattern leaves the syntax that means the same in JS, Python and the server.
function subsetProblem(p: string): string | undefined {
  for (let i = 0; i < p.length; i++) {
    const ch = p[i]
    const next = p[i + 1] ?? ''
    if (ch === '\\') {
      if (next && SUBSET.shorthand.includes(next)) return SHORTHAND
      if (next === 'x' && HEX.test(p.slice(i + 2, i + 4))) { i += 3; continue }
      if (!next || !SUBSET.escapes.includes(next)) return `pattern escape \\${next} is not supported`
      i += 1
    } else if (ch === '(' && next === '?' && p[i + 2] !== ':') {
      return 'patterns can only group with ( or (?:'
    } else if (ch === '{' && next === ',') {
      return 'patterns cannot use {,n}; write {0,n}'
    }
  }
  return undefined
}

const QUANT = /\{([0-9]+)(?:(,)([0-9]*))?\}/y
const REPEAT =
  `patterns cannot repeat more than ${SUBSET.maxRepeat} times ({n}, {n,} and {n,m} take at most ${SUBSET.maxRepeat})`
const EXPANDED = `a pattern is over ${SUBSET.maxExpandedChars} characters with its repeats written out`

// Where a class opening at i ends: after the first unescaped ] (the JS reading, so [] closes at once).
function classEnd(p: string, i: number): number {
  let j = p[i + 1] === '^' ? i + 2 : i + 1
  while (j < p.length) {
    if (p[j] === '\\') j += 2
    else if (p[j] === ']') return j + 1
    else j += 1
  }
  return p.length
}

// A quantifier at i: its repeat bound ({n,} counts n+1, {0} counts 1) and end, a repeat problem, or undefined.
function quantifier(p: string, i: number): { bound: number, end: number } | string | undefined {
  const ch = p[i]
  if (ch === '*' || ch === '+' || ch === '?') return { bound: 1, end: i + 1 }
  if (ch !== '{') return undefined
  QUANT.lastIndex = i
  const m = QUANT.exec(p)
  if (!m) return undefined
  const lo = Number(m[1])
  const hi = m[3] ? Number(m[3]) : undefined
  if (lo > SUBSET.maxRepeat || (hi !== undefined && hi > SUBSET.maxRepeat)) return REPEAT
  return { bound: Math.max(1, hi ?? (m[2] ? lo + 1 : lo)), end: i + m[0].length }
}

// The atom at i (a class, an escape or one code point): its length in UTF-16 units and its end.
function atomAt(p: string, i: number): [number, number] {
  let end = i + ((p.codePointAt(i) ?? 0) > 0xffff ? 2 : 1)
  if (p[i] === '[') end = classEnd(p, i)
  if (p[i] === '\\') end = Math.min(p.length, i + (p[i + 1] === 'x' && HEX.test(p.slice(i + 2, i + 4)) ? 4 : 2))
  return [end - i, end]
}

// Counted repeats against spec patternSubset: maxRepeat per repeat, maxExpandedChars written out.
function repeatProblem(p: string): string | undefined {
  const frames: Array<[total: number, last: number]> = [[0, 0]]
  let i = 0
  while (i < p.length) {
    const top = frames[frames.length - 1] as [number, number]
    const q = quantifier(p, i)
    if (typeof q === 'string') return q
    if (q) {
      top[0] += top[1] * (q.bound - 1)
      top[1] *= q.bound
      i = q.end
    } else if (p[i] === '(') {
      const open = p.startsWith('(?:', i) ? 3 : 1
      frames.push([open, 0])
      i += open
    } else {
      let atom: number
      if (p[i] === ')' && frames.length > 1) {
        frames.pop()
        atom = top[0] + 1
        i += 1
      } else {
        [atom, i] = atomAt(p, i)
      }
      const f = frames[frames.length - 1] as [number, number]
      f[0] += atom
      f[1] = atom
    }
    if (frames.reduce((s, f) => s + f[0], 0) > SUBSET.maxExpandedChars) return EXPANDED
  }
  return undefined
}

export interface SchemaWalk {
  problem?: string // why the server would refuse these parameters
  pattern?: boolean // the problem is a pattern, not the size
  patterns: number
}

export function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v)
}

export function patternProblem(pattern: unknown): string | undefined {
  if (typeof pattern !== 'string') return 'a pattern must be a string'
  if (pattern.length > S.maxPatternChars) return `a pattern is over ${S.maxPatternChars} characters`
  if (NOT_LINEAR.test(pattern)) return 'patterns cannot use lookaround or backreferences'
  const subset = subsetProblem(pattern) ?? repeatProblem(pattern)
  if (subset) return subset
  try {
    new RegExp(pattern)
  } catch {
    return `pattern ${pattern} does not compile`
  }
  return undefined
}

type Entry = [node: unknown, parentKey: string | number | undefined, depth: number]

function keyProblem(node: Record<string, unknown>): string | undefined {
  const long = Object.keys(node).find((k) => k.length > S.maxKeyChars)
  return long === undefined ? undefined : `a key is over ${S.maxKeyChars} characters`
}

// Same walk and caps as the server's session.update check: iterative, so a huge schema cannot blow the stack.
export function walkSchema(schema: unknown): SchemaWalk {
  const stack: Entry[] = [[schema, undefined, 1]]
  let nodes = 0
  let patterns = 0
  while (stack.length) {
    const [node, parentKey, depth] = stack.pop() as Entry
    nodes += 1
    if (nodes > S.maxNodes) return { problem: `over ${S.maxNodes} schema nodes`, patterns }
    if (depth > S.maxDepth) return { problem: `nested over ${S.maxDepth} levels`, patterns }
    if (Array.isArray(node)) node.forEach((v, i) => stack.push([v, i, depth + 1]))
    if (!isRecord(node)) continue
    const problem = keyProblem(node)
    if (problem) return { problem, patterns }
    for (const k of sortedKeys(node)) {
      const v = node[k]
      if (k === PATTERN && parentKey !== PROPERTIES) {
        patterns += 1
        const why = patternProblem(v)
        if (why) return { problem: why, pattern: true, patterns }
      } else {
        stack.push([v, k, depth + 1])
      }
    }
  }
  return { patterns }
}

export interface Field {
  path: string
  schema: Record<string, unknown>
}

// Every named field in a parameters schema, depth first in sorted key order; array items keep their parent's name.
export function fieldsOf(schema: Record<string, unknown>, prefix = ''): Field[] {
  const props = schema[PROPERTIES]
  if (!isRecord(props)) return []
  return sortedKeys(props).flatMap((name) => {
    const field = props[name]
    if (!isRecord(field)) return []
    const path = prefix ? `${prefix}.${name}` : name
    const items = field.items
    return [{ path, schema: field }, ...fieldsOf(field, path), ...(isRecord(items) ? fieldsOf(items, `${path}[]`) : [])]
  })
}
