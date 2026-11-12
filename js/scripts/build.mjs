#!/usr/bin/env node
// Builds the publishable package into dist/: JS and types, the audio worklet, README, LICENSE and a package.json
// of its own. The workspace package.json keeps pointing at src for local development; publish from dist.
import { execFileSync } from 'node:child_process'
import { copyFileSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const PKG = join(dirname(fileURLToPath(import.meta.url)), '..')
const DIST = join(PKG, 'dist')
const META = JSON.parse(readFileSync(join(PKG, 'src/generated/package-meta.json'), 'utf8'))

export function distManifest(p) {
  return {
    name: p.npm,
    version: p.version,
    description: 'Tavia realtime voice agents, speech-to-text and text-to-speech for browsers and Node',
    license: p.license,
    homepage: p.homepage,
    repository: { type: 'git', url: `git+${p.repository}.git` },
    bugs: { url: `${p.repository}/issues` },
    keywords: p.keywords,
    type: 'module',
    exports: { '.': { types: './index.d.ts', import: './index.js' } },
    sideEffects: false,
    engines: { node: '>=22' },
    peerDependencies: { ws: '>=8' },
    peerDependenciesMeta: { ws: { optional: true } },
    publishConfig: { access: 'public' },
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  rmSync(DIST, { recursive: true, force: true })
  execFileSync('npx', ['tsc', '-p', join(PKG, 'tsconfig.build.json')], { stdio: 'inherit' })
  copyFileSync(join(PKG, 'src/audio/capture-worklet.js'), join(DIST, 'audio/capture-worklet.js'))
  for (const file of ['README.md', 'LICENSE']) copyFileSync(join(PKG, file), join(DIST, file))
  writeFileSync(join(DIST, 'package.json'), `${JSON.stringify(distManifest(META), null, 2)}\n`)
}
