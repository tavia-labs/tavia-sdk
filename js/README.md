# @tavia/sdk

The TypeScript SDK for [Tavia](https://tavialabs.com): realtime voice agents, speech-to-text and text-to-speech, in
browsers and Node. Typed end to end: every session option, event, error code and limit the API has.

```sh
npm install @tavia/sdk
npm install ws          # Node only, for realtime and streaming with an API key
```

Node 22 or later, or any current browser. Every endpoint is under `https://api.tavialabs.com/v1`, except the live
speech-to-text socket, which has its own host.

## Quick start: a voice agent from your server (Node)

Save as `agent.mjs` (an ES module, for top-level `await`) and run `TAVIA_API_KEY=... node agent.mjs`.

```js
import { Tavia, functionTool } from '@tavia/sdk'

const tavia = new Tavia({ apiKey: process.env.TAVIA_API_KEY })
const call = await tavia.realtime.connect({
  session: {
    voice: 'elaine',
    instructions: 'You answer calls for a clinic. Be warm and brief.',
    tools: [functionTool({ name: 'check_slots', effect: 'read', description: 'Free slots on a day' })],
  },
})
call.tool('check_slots', async ({ day }) => ({ day, slots: ['10:00', '14:30'] }))
call.on('transcript', (t) => { if (t.final) console.log(`${t.role}: ${t.text}`) })
call.sendText('Any slots on Friday?')
```

## Quick start: talking in the browser

A page never holds your API key. Your server mints a short-lived token for the page's origin, and the page connects
with it.

```ts
// On your server (the origin must be on your organisation's allowed list)
const { token, url } = await tavia.tokens.create('voice', 'https://app.example.com')
```

```ts
// In the page
import { LIMITS, Tavia, createPlayer, openMic } from '@tavia/sdk'

const { token, url } = await (await fetch('/token', { method: 'POST' })).json()
const tavia = new Tavia({ token, urls: { realtime: url } })
const player = createPlayer(LIMITS['realtime.outputRates'][0])
const call = await tavia.realtime.connect({ player, session: { voice: 'elaine' } })
const mic = await openMic({ sampleRate: LIMITS['realtime.inputRates'][0] })
mic.onFrame((pcm) => call.sendAudio(pcm))
```

`new Tavia({ apiKey })` throws in a browser, so a key cannot ship in page code by mistake.

## Speech-to-text and text-to-speech

```ts
import { readFile, writeFile } from 'node:fs/promises'

const { text } = await tavia.stt.transcribe(await readFile('call.wav'), { terms: ['Tavia'] })
const speech = await tavia.tts.render({ voice: 'elaine', text: 'Your table is ready.', lang: 'en' })
await writeFile('speech.wav', speech.wav)
```

Live streams: `tavia.stt.stream()` (partials and formatted finals) and `tavia.tts.stream(voice)` (audio as it is
made, many utterances on one socket). `tavia.tts.voices()` lists the voices.

## Using a standard API client instead

Tavia also speaks the standard realtime and audio API, so an official client library built for that API works
when you change two settings. Use it when you already have code on that API; use this SDK for Tavia's own features
(friendly events, tool handlers, the tool checker, live speech-to-text).

| | A standard API client | `@tavia/sdk` |
|---|---|---|
| Base URL | `https://api.tavialabs.com/v1` | the default |
| Key | your Tavia API key | your Tavia API key |
| Realtime | `/v1/realtime`, standard events | `tavia.realtime.connect()`: the same standard events, plus Tavia's |
| File transcription | `POST /v1/audio/transcriptions` | `tavia.stt.transcribe(file)` |
| Speech | `POST /v1/audio/speech` | `tavia.tts.render({ voice, text, lang })` |
| Tavia session options | under `session.tavia` | top-level session options, typed |

## Core concepts

- **Session.** One realtime conversation over a WebSocket. `connect()` sends your session options; `call.update()`
  changes them live. Options are typed (`SessionConfig`); the SDK sends them in the standard shape, with Tavia's own
  options under `tavia`.
- **Events.** `call.on(name)` gives friendly events: `transcript`, `turn`, `interruption`, `tool_call`, `timing`,
  `warning`, `error`, `audio`, `ended`. `call.onEvent(type)` gives every wire event, typed, under its standard name
  (`response.output_audio.delta`, `conversation.item.added`, ...). `call.onRaw()` gives every message as received.
- **Tools.** Describe each tool with `functionTool({ name, effect })`: `read` runs at once; `write` runs only after
  the agent reads it back and the caller says yes. `call.tool(name, handler)` runs your handler and sends its
  result. `checkTools(tools)` reports what a session would refuse, before you connect.
- **Audio.** PCM16 mono, base64 on the wire, at the rates in `LIMITS['realtime.inputRates']` and
  `LIMITS['realtime.outputRates']`. `openMic()` captures 20 ms frames in the browser; `createPlayer()` plays the
  agent and lets `call.interrupt()` stop it at the point the caller heard.

## Errors

Every failure is a `TaviaError` with `code`, `message` and `http`, and a subclass per kind:

| Class | When |
|---|---|
| `AuthenticationError` | a missing, wrong or expired key or token (401) |
| `PermissionDeniedError`, `InsufficientCreditError` | not allowed (403), out of credit (402) |
| `InvalidRequestError`, `UnprocessableError`, `TooLargeError` | the request was refused (400, 422, 413) |
| `RateLimitError` | too many requests (429) |
| `ServerError` | the server failed (5xx) |
| `ConnectError` | the server could not be reached, or a socket closed before it opened |
| `SessionClosedError` | a send on a session that has closed |

```ts
import { RateLimitError } from '@tavia/sdk'

try {
  await tavia.tts.render({ voice: 'elaine', text, lang: 'en' })
} catch (err) {
  if (err instanceof RateLimitError) console.log('slow down:', err.message)
  else throw err
}
```

Rate limits and unavailable answers are retried twice with backoff (`maxRetries` changes it); the server's
`Retry-After` is honoured.

## Configuration

```ts
new Tavia({
  apiKey,                                   // or { token } in a browser
  baseURL: 'https://api.tavialabs.com/v1',  // the default
  urls: { realtime: 'ws://localhost:8080/v1/realtime' },  // point one endpoint elsewhere, e.g. a test server
  maxRetries: 2,
})
```

## Examples

[`examples/`](examples): a browser voice page with its token server, transcribing a file, and text-to-speech.

## Links

- Documentation: https://app.tavialabs.com/docs
- Python SDK: `pip install tavia`
- License: Apache-2.0
