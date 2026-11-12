import { describe, expect, it } from 'vitest'

import { base64ToPcm16, pcm16ToBase64 } from '../src/audio/pcm.ts'

describe('pcm', () => {
  it('round_trips_little_endian_pcm16_through_base64', () => {
    const pcm = Int16Array.from([0, 1, -1, 32767, -32768, 1234])
    expect([...base64ToPcm16(pcm16ToBase64(pcm))]).toEqual([...pcm])
  })

  it('encodes_low_byte_first', () => {
    expect(pcm16ToBase64(Int16Array.from([1]))).toBe('AQA=')
  })

  it('ignores_a_trailing_odd_byte', () => {
    expect(base64ToPcm16('AQAC').length).toBe(1)
  })
})
