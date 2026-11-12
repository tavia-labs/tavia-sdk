// GENERATED from the API specification. Do not edit.
import { CONSTANTS } from './checker-spec.ts'
import { TOOL_CHECKER } from './checker-spec.ts'
import { TOOL_RULES, type ToolIssueCode, type ToolSeverity } from './rules.ts'
import { fieldsOf, isRecord, walkSchema, type Field } from './schema-walk.ts'
import { nameSimilarity, nameWords, textSimilarity } from './similarity.ts'

const { limits, realtime } = CONSTANTS
const EFFECT = realtime.toolEffect
const ACTION = realtime.toolAction
const ACTIONS = `${ACTION.values.slice(0, -1).join(', ')} or ${ACTION.values.at(-1)}`
const NAME_RE = new RegExp(limits.toolNameRegex)
const WRITE_HINTS: ReadonlySet<string> = new Set(TOOL_CHECKER.writeHints)
const FORMATS: ReadonlySet<string> = new Set(TOOL_CHECKER.formats)
const FORMAT_HINTS = Object.entries(TOOL_CHECKER.formatHints) as [string, readonly string[]][]
const COORDINATE_HINTS = Object.entries(TOOL_CHECKER.coordinateHints) as [string, { words: readonly string[], minimum: number, maximum: number }][]
const RESERVED = realtime.builtinTools.prefix
const NUMBER_TYPES: ReadonlySet<unknown> = new Set(['number', 'integer'])
const UTF8 = new TextEncoder()

export interface ToolIssue {
  code: ToolIssueCode
  severity: ToolSeverity
  tool?: string // the tool's name, or tools[i] when it has none
  path?: string // a parameter, as patient.phone or items[].sku
  message: string
}

export interface ToolReport {
  errors: ToolIssue[]
  warnings: ToolIssue[]
}

export interface CheckToolsOptions {
  maxTools?: number // the session's hard cap; browser-token sessions have a lower one
}

type Add = (code: ToolIssueCode, message: string, at?: { tool?: string, path?: string }) => void

interface Checked {
  name?: string
  description?: string
  patterns: number
}

function checkEffect(t: Record<string, unknown>, label: string, add: Add): void {
  const effect = t[EFFECT.key]
  if (effect === undefined) {
    add('effect_missing', `No ${EFFECT.key}, so it runs as ${EFFECT.default} and is confirmed before every call. Set read if it only looks things up.`, { tool: label })
  } else if (!(EFFECT.values as readonly unknown[]).includes(effect)) {
    add('effect_invalid', `${EFFECT.key} must be ${EFFECT.values.join(' or ')}.`, { tool: label })
  } else if (effect === 'read' && nameWords(label).some((w) => WRITE_HINTS.has(w))) {
    add('effect_read_looks_like_write', 'Marked read, but the name sounds like a change. If it changes anything, mark it write.', { tool: label })
  }
}

// A write's action class backs the guard's done-claims; an unknown one never would.
function checkAction(t: Record<string, unknown>, label: string, add: Add): void {
  const action = t[ACTION.key]
  if (action === undefined) return
  if (!(ACTION.values as readonly unknown[]).includes(action)) {
    add('action_invalid', `${ACTION.key} must be ${ACTIONS}.`, { tool: label })
  } else if (t[EFFECT.key] === 'read') {
    add('action_on_read', `Marked read, so ${ACTION.key} is ignored: a read only backs 'found'.`, { tool: label })
  }
}

function checkDescription(t: Record<string, unknown>, label: string, add: Add): string | undefined {
  const d = typeof t.description === 'string' ? t.description.trim() : ''
  if (!d) {
    add('description_missing', 'Add a description: what it does and when to call it.', { tool: label })
    return undefined
  }
  if (UTF8.encode(d).length < TOOL_CHECKER.minDescriptionBytes || nameWords(d).join(' ') === nameWords(label).join(' ')) {
    add('description_vague', 'Say what it does and when to call it, not just its name.', { tool: label })
  }
  return d
}

function formatFor(fieldName: string): string | undefined {
  const words = new Set(nameWords(fieldName))
  const hits = FORMAT_HINTS.filter(([, hints]) => hints.some((h) => words.has(h))).map(([f]) => f)
  return hits.includes('date') && hits.includes('time') ? 'date-time' : hits[0]
}

// A number named like a latitude or longitude should carry its range, so a misheard value is refused.
function checkCoordinate(path: string, schema: Record<string, unknown>, label: string, add: Add): void {
  if (!NUMBER_TYPES.has(schema.type) || (schema.minimum !== undefined && schema.maximum !== undefined)) return
  const words = new Set(nameWords(path.split('.').at(-1) ?? path))
  const hit = COORDINATE_HINTS.find(([, h]) => h.words.some((w) => words.has(w)))
  if (hit) {
    const [kind, { minimum, maximum }] = hit
    add('coordinates_unbounded', `Add "minimum": ${minimum} and "maximum": ${maximum} so an impossible ${kind} is refused.`, { tool: label, path })
  }
}

function checkField({ path, schema }: Field, label: string, add: Add): void {
  if (typeof schema.description !== 'string' || !schema.description.trim()) {
    add('param_description_missing', `Describe ${path}: what it holds and in what form.`, { tool: label, path })
  }
  checkCoordinate(path, schema, label, add)
  if (schema.format !== undefined) {
    if (!FORMATS.has(String(schema.format))) add('format_unknown', `Format ${String(schema.format)} is not enforced.`, { tool: label, path })
    return
  }
  const free = schema.pattern !== undefined || schema.enum !== undefined || (schema.type !== undefined && schema.type !== 'string')
  const want = free ? undefined : formatFor(path.split('.').at(-1) ?? path)
  if (want) add('format_missing', `Add "format": "${want}" so the value arrives in one form.`, { tool: label, path })
}

function checkRequired(schema: Record<string, unknown>, label: string, add: Add, path?: string): void {
  if (!Array.isArray(schema.required)) return
  const props = isRecord(schema.properties) ? schema.properties : {}
  for (const name of schema.required) {
    if (!Object.hasOwn(props, String(name))) add('required_unknown', `required lists ${String(name)}, which is not defined.`, { tool: label, path })
  }
}

function checkParameters(params: unknown, label: string, add: Add): number {
  if (params === undefined) return 0
  if (!isRecord(params) || (params.type !== undefined && params.type !== 'object') || (params.properties !== undefined && !isRecord(params.properties))) {
    add('parameters_invalid', 'parameters must be a JSON Schema object with type "object".', { tool: label })
    return 0
  }
  const walk = walkSchema(params)
  if (walk.problem) {
    add(walk.pattern ? 'pattern_invalid' : 'schema_too_large', `parameters: ${walk.problem}.`, { tool: label })
    return walk.patterns
  }
  if (walk.patterns > realtime.toolSchema.maxPatternsPerTool) {
    add('patterns_too_many', `More than ${realtime.toolSchema.maxPatternsPerTool} patterns in one tool.`, { tool: label })
  }
  checkRequired(params, label, add)
  for (const field of fieldsOf(params)) {
    checkField(field, label, add)
    checkRequired(field.schema, label, add, field.path)
  }
  return walk.patterns
}

function checkOne(t: unknown, i: number, seen: Set<string>, add: Add): Checked | undefined {
  if (!isRecord(t) || t.type !== 'function') {
    add('tool_invalid', 'Each tool must be an object with type "function".', { tool: `tools[${i}]` })
    return undefined
  }
  const named = typeof t.name === 'string' && t.name ? t.name : undefined
  const label = named ?? `tools[${i}]`
  if (!named || !NAME_RE.test(named)) add('name_invalid', `Use a name matching ${limits.toolNameRegex}.`, { tool: label })
  else if (named.toLowerCase().startsWith(RESERVED)) add('name_reserved', `Names starting with ${RESERVED}, in any case, are reserved for Tavia's built-in tools; rename it.`, { tool: label })
  else if (seen.has(named)) add('name_duplicate', 'Another tool already has this name.', { tool: label })
  if (named) seen.add(named)
  checkEffect(t, label, add)
  checkAction(t, label, add)
  const description = checkDescription(t, label, add)
  return { name: named, description, patterns: checkParameters(t.parameters, label, add) }
}

function checkPairs(tools: Checked[], add: Add): void {
  const th = TOOL_CHECKER.similarity
  tools.forEach((a, i) => tools.slice(i + 1).forEach((b) => {
    if (!a.name || !b.name || a.name === b.name) return
    const names = nameSimilarity(a.name, b.name) >= th.name
    const texts = !!a.description && !!b.description && textSimilarity(a.description, b.description) >= th.description
    if (names || texts) add('near_duplicate', `${a.name} and ${b.name} look alike; the agent may pick the wrong one.`, { tool: `${a.name}, ${b.name}` })
  }))
}

function checkCount(n: number, maxTools: number, add: Add): void {
  if (n > maxTools) add('tools_too_many', `${n} tools; a session takes at most ${maxTools}.`)
  else if (n > TOOL_CHECKER.accuracyTools) add('tools_many', `${n} tools; above ${TOOL_CHECKER.accuracyTools} the agent picks less reliably.`)
}

/**
 * Checks session tools before you connect. `errors` are what the server would refuse at session.update;
 * `warnings` cost accuracy or safety.
 *
 * @example
 * const { errors, warnings } = checkTools([functionTool({ name: 'check_slots', effect: 'read' })])
 */
export function checkTools(tools: readonly unknown[], { maxTools = limits.tools }: CheckToolsOptions = {}): ToolReport {
  const report: ToolReport = { errors: [], warnings: [] }
  const add: Add = (code, message, at = {}) => {
    const severity = TOOL_RULES[code].severity
    report[severity === 'error' ? 'errors' : 'warnings'].push({ code, severity, ...at, message })
  }
  checkCount(tools.length, maxTools, add)
  const seen = new Set<string>()
  const checked = tools.map((t, i) => checkOne(t, i, seen, add)).filter((c): c is Checked => c !== undefined)
  if (checked.reduce((n, c) => n + c.patterns, 0) > realtime.toolSchema.maxPatterns) {
    add('patterns_too_many', `More than ${realtime.toolSchema.maxPatterns} patterns across the session's tools.`)
  }
  checkPairs(checked, add)
  return report
}
