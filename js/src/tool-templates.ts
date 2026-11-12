import { TOOL_TEMPLATES, type ToolTemplateId } from './generated/spec.ts'
import type { ToolDefinition } from './generated/types.ts'

/**
 * A ready-made tool as a fresh, editable copy: change it freely, the template itself stays unchanged.
 * Throws when `id` is not a known template.
 */
export function templateTool(id: ToolTemplateId): ToolDefinition {
  const found = TOOL_TEMPLATES.find((t) => t.id === id)
  if (!found) throw new Error(`unknown tool template ${String(id)}`)
  return structuredClone(found.tool) as unknown as ToolDefinition
}
