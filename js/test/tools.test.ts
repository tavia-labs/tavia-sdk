import { describe, expect, it } from 'vitest'

import { TOOL_MARKS, checkTools, functionTool, templateTool } from '../src/index.ts'

describe('tool helpers', () => {
  it('templates_are_the_published_tools_as_fresh_copies', () => {
    const tool = templateTool('check_availability')
    expect(tool[TOOL_MARKS.effect]).toBe('read')
    expect(tool.parameters?.properties?.date?.[TOOL_MARKS.date]).toBe('booking')
    tool.name = 'changed'
    expect(templateTool('check_availability').name).toBe('check_availability')
  })
})

describe('functionTool', () => {
  it('states_its_effect_and_passes_the_checker', () => {
    const tool = functionTool({ name: 'get_hours', effect: 'read', description: 'Opening hours for a day.',
      parameters: { type: 'object', properties: { day: { type: 'string' } } } })
    expect(tool[TOOL_MARKS.effect]).toBe('read')
    expect(checkTools([tool]).errors).toEqual([])
    expect(functionTool({ name: 'book', effect: 'write', action: 'create' })[TOOL_MARKS.action]).toBe('create')
    expect(() => functionTool({ name: 'x', effect: 'maybe' as never })).toThrow(/effect/)
  })
})
