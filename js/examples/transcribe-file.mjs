// Transcribe an audio file.  Usage: TAVIA_API_KEY=... node transcribe-file.mjs call.wav
import { readFile } from 'node:fs/promises'

import { Tavia } from '@tavia/sdk'

const tavia = new Tavia({ apiKey: process.env.TAVIA_API_KEY })
const audio = await readFile(process.argv[2] ?? 'call.wav')
const result = await tavia.stt.transcribe(audio, { terms: ['Tavia'] })
console.log(result.text)
