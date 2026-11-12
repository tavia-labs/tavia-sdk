// PCM16 little-endian <-> base64, the wire form of realtime audio events. No Buffer, so it runs in browsers too.

const BYTES_PER_SAMPLE = 2

/** Encodes PCM16 samples as little-endian base64. */
export function pcm16ToBase64(pcm: Int16Array): string {
  const view = new DataView(new ArrayBuffer(pcm.length * BYTES_PER_SAMPLE))
  pcm.forEach((v, i) => view.setInt16(i * BYTES_PER_SAMPLE, v, true))
  const bytes = new Uint8Array(view.buffer)
  let bin = ''
  for (const b of bytes) bin += String.fromCharCode(b)
  return btoa(bin)
}

/** Decodes little-endian base64 into PCM16 samples. */
export function base64ToPcm16(b64: string): Int16Array {
  const bin = atob(b64)
  const out = new Int16Array(Math.floor(bin.length / BYTES_PER_SAMPLE))
  for (let i = 0; i < out.length; i++) {
    const lo = bin.charCodeAt(i * BYTES_PER_SAMPLE)
    const hi = bin.charCodeAt(i * BYTES_PER_SAMPLE + 1)
    out[i] = (hi << 24 >> 16) | lo
  }
  return out
}
