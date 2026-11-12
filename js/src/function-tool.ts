import { TOOL_MARKS } from './generated/spec.ts'
import type { ToolDefinition } from './generated/types.ts'

/** Whether a tool only reads (`read`) or changes something (`write`). */
export type ToolEffect = (typeof TOOL_MARKS.effects)[number]
/** The kind of change a write tool makes, such as `create` or `cancel`. */
export type ToolAction = (typeof TOOL_MARKS.actions)[number]

/** The fields of a function tool built with {@link functionTool}. */
export interface FunctionToolOptions {
  /** The tool's name, as the agent calls it. */
  name: string
  /** read runs at once; write only after a read-back and the caller's yes. A tool without one is treated as a write. */
  effect: ToolEffect
  /** What the tool does and when the agent should call it. */
  description?: string
  /** A JSON Schema for the arguments; defaults to an object with no properties. */
  parameters?: Record<string, unknown>
  /** The kind of change a write tool makes. */
  action?: ToolAction
}

/**
 * Builds a function tool definition with its effect stated, ready for `session.tools`.
 * Throws a TypeError when `effect` is not a known effect.
 *
 * @example
 * const findOrder = functionTool({
 *   name: 'find_order',
 *   effect: 'read',
 *   description: 'Look up an order by its number.',
 *   parameters: { type: 'object', properties: { order_id: { type: 'string' } }, required: ['order_id'] },
 * })
 */
export function functionTool(opts: FunctionToolOptions): ToolDefinition {
  if (!(TOOL_MARKS.effects as readonly string[]).includes(opts.effect)) {
    throw new TypeError(`effect must be one of ${TOOL_MARKS.effects.join(', ')}`)
  }
  const tool: Record<string, unknown> = {
    type: 'function', name: opts.name, [TOOL_MARKS.effect]: opts.effect,
    parameters: structuredClone(opts.parameters ?? { type: 'object', properties: {} }),
  }
  if (opts.description) tool.description = opts.description
  if (opts.action !== undefined) tool[TOOL_MARKS.action] = opts.action
  return tool as unknown as ToolDefinition
}
