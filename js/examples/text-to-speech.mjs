// Render a sentence to a WAV file.  Usage: TAVIA_API_KEY=... node text-to-speech.mjs "Your table is ready."
import { writeFile } from 'node:fs/promises'

import { Tavia } from '@tavia/sdk'

const tavia = new Tavia({ apiKey: process.env.TAVIA_API_KEY })
const text = process.argv[2] ?? 'Your appointment is at ten tomorrow.'
const speech = await tavia.tts.render({ voice: 'elaine', text, lang: 'en' })
await writeFile('speech.wav', speech.wav)
console.log(`wrote speech.wav (${speech.audio_s.toFixed(1)} s)`)
