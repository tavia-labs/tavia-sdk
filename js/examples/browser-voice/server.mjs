// Serves the page and mints a short-lived token for it. The API key never leaves this server.
// Usage: TAVIA_API_KEY=... APP_ORIGIN=https://your-app.example node server.mjs
// APP_ORIGIN is the https origin the page is served from; add it to your organisation's allowed origins first.
import { readFile } from 'node:fs/promises'
import { createServer } from 'node:http'

import { Tavia } from '@tavia/sdk'

const tavia = new Tavia({ apiKey: process.env.TAVIA_API_KEY })
const page = await readFile(new URL('./index.html', import.meta.url))

async function mintToken(res) {
  const { token, url, expires_at } = await tavia.tokens.create('voice', process.env.APP_ORIGIN)
  res.writeHead(200, { 'content-type': 'application/json' }).end(JSON.stringify({ token, url, expires_at }))
}

createServer((req, res) => {
  if (req.method === 'POST' && req.url === '/token') {
    mintToken(res).catch((err) => res.writeHead(502).end(err.message))
    return
  }
  res.writeHead(200, { 'content-type': 'text/html' }).end(page)
}).listen(3000, () => console.log('listening on :3000'))
