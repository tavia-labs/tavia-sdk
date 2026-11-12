// GENERATED from the API specification. Do not edit.
import { CONSTANTS } from './checker-spec.ts'
import { TOOL_CHECKER } from './checker-spec.ts'

const { limits, realtime } = CONSTANTS
const S = realtime.toolSchema
const EFFECT = realtime.toolEffect
const ACTION = realtime.toolAction
const ACTIONS = `${ACTION.values.slice(0, -1).join(', ')} or ${ACTION.values.at(-1)}`
const SEVERITY = TOOL_CHECKER.rules
const COORDINATE_WORDS = Object.values(TOOL_CHECKER.coordinateHints).flatMap((h) => h.words)

export type ToolSeverity = 'error' | 'warning'

// Every check the tool checker runs, its severity from the spec. Errors are what the server refuses; warnings cost accuracy or safety.
export const TOOL_RULES = {
  tool_invalid: { severity: SEVERITY.tool_invalid, rule: 'Each tool is an object with type "function".' },
  name_invalid: { severity: SEVERITY.name_invalid, rule: `The name matches ${limits.toolNameRegex}.` },
  name_reserved: {
    severity: SEVERITY.name_reserved,
    rule: `Names starting with ${realtime.builtinTools.prefix}, in any case, are reserved for Tavia's built-in tools.`,
  },
  name_duplicate: { severity: SEVERITY.name_duplicate, rule: 'Each tool name is used once in the session.' },
  effect_invalid: { severity: SEVERITY.effect_invalid, rule: `${EFFECT.key} is ${EFFECT.values.join(' or ')} when given.` },
  action_invalid: { severity: SEVERITY.action_invalid, rule: `${ACTION.key} is ${ACTIONS} when given.` },
  parameters_invalid: { severity: SEVERITY.parameters_invalid, rule: 'parameters is a JSON Schema with type "object".' },
  schema_too_large: {
    severity: SEVERITY.schema_too_large,
    rule: `parameters stays within ${S.maxDepth} levels, ${S.maxNodes} nodes and keys of ${S.maxKeyChars} characters.`,
  },
  pattern_invalid: {
    severity: SEVERITY.pattern_invalid,
    rule: `A pattern is at most ${S.maxPatternChars} characters (${S.patternSubset.maxExpandedChars} with its repeats written out, each repeat at most ${S.patternSubset.maxRepeat}) and runs in linear time: no lookaround or backreferences.`,
  },
  patterns_too_many: { severity: SEVERITY.patterns_too_many, rule: `At most ${S.maxPatternsPerTool} patterns per tool and ${S.maxPatterns} per session.` },
  tools_too_many: { severity: SEVERITY.tools_too_many, rule: `At most ${limits.tools} tools per session (${realtime.tokenCaps.tools} with a browser token).` },
  effect_missing: {
    severity: SEVERITY.effect_missing,
    rule: `No ${EFFECT.key}: the tool runs as ${EFFECT.default}, read back and confirmed before every call. Set read for lookups.`,
  },
  effect_read_looks_like_write: {
    severity: SEVERITY.effect_read_looks_like_write,
    rule: `A tool marked read whose name sounds like a change (${TOOL_CHECKER.writeHints.slice(0, 6).join(', ')}…). English hint only.`,
  },
  action_on_read: {
    severity: SEVERITY.action_on_read,
    rule: `A tool marked read with ${ACTION.key}: the action is ignored, since a read only backs 'found'.`,
  },
  description_missing: { severity: SEVERITY.description_missing, rule: 'Every tool has a description saying what it does and when to call it.' },
  description_vague: {
    severity: SEVERITY.description_vague,
    rule: `A description under ${TOOL_CHECKER.minDescriptionBytes} bytes, or one that only repeats the name.`,
  },
  param_description_missing: { severity: SEVERITY.param_description_missing, rule: 'Every parameter has a description.' },
  format_missing: {
    severity: SEVERITY.format_missing,
    rule: 'A date, time or phone field (by its name) without a format, pattern or enum.',
  },
  format_unknown: { severity: SEVERITY.format_unknown, rule: `A format other than ${TOOL_CHECKER.formats.join(', ')} is not enforced.` },
  coordinates_unbounded: {
    severity: SEVERITY.coordinates_unbounded,
    rule: `A number field named like a coordinate (${COORDINATE_WORDS.join(', ')}) without minimum and maximum. English hint only.`,
  },
  required_unknown: { severity: SEVERITY.required_unknown, rule: 'required names a field that properties does not define.' },
  near_duplicate: {
    severity: SEVERITY.near_duplicate,
    rule: `Two tools with near-identical names (${TOOL_CHECKER.similarity.name}) or descriptions (${TOOL_CHECKER.similarity.description}): the agent may pick the wrong one.`,
  },
  tools_many: {
    severity: SEVERITY.tools_many,
    rule: `More than ${TOOL_CHECKER.accuracyTools} tools: the agent picks less reliably. Split by task or merge similar tools.`,
  },
} as const satisfies Record<string, { severity: ToolSeverity, rule: string }>

export type ToolIssueCode = keyof typeof TOOL_RULES
