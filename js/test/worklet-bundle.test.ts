import { mkdtempSync, readdirSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

import { build } from 'vite'
import { describe, expect, it } from 'vitest'

const MIC = fileURLToPath(new URL('../src/audio/mic.ts', import.meta.url))

// A consumer's default Vite build must ship the worklet as a file: a strict CSP blocks a data: worklet.
describe('worklet in a consumer bundle', () => {
  it('a_default_vite_build_emits_the_worklet_as_a_file', async () => {
    const root = mkdtempSync(join(tmpdir(), 'tavia-sdk-consumer-'))
    const entry = join(root, 'main.js')
    writeFileSync(entry, `import { openMic } from ${JSON.stringify(MIC)}\nglobalThis.openMic = openMic\n`)
    const outDir = join(root, 'dist')
    await build({ root, configFile: false, logLevel: 'silent', build: { outDir, rollupOptions: { input: entry } } })
    const files = readdirSync(join(outDir, 'assets'))
    const text = files.map((f) => readFileSync(join(outDir, 'assets', f), 'utf8')).join('\n')
    expect(text).not.toContain('data:text/javascript')
    const worklet = files.find((f) => /^capture-worklet-[\w-]+\.js$/.test(f)) ?? ''
    expect(worklet).not.toBe('')
    expect(text).toContain(worklet)
    expect(text).not.toContain('no-inline')
  }, 120_000)
})
