const BASE64_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

const toUtf8Bytes = (text: string): number[] => {
  const bytes: number[] = []
  for (const char of text) {
    const codePoint = char.codePointAt(0) ?? 0
    if (codePoint <= 0x7f) {
      bytes.push(codePoint)
    } else if (codePoint <= 0x7ff) {
      bytes.push(0xc0 | (codePoint >> 6))
      bytes.push(0x80 | (codePoint & 0x3f))
    } else if (codePoint <= 0xffff) {
      bytes.push(0xe0 | (codePoint >> 12))
      bytes.push(0x80 | ((codePoint >> 6) & 0x3f))
      bytes.push(0x80 | (codePoint & 0x3f))
    } else {
      bytes.push(0xf0 | (codePoint >> 18))
      bytes.push(0x80 | ((codePoint >> 12) & 0x3f))
      bytes.push(0x80 | ((codePoint >> 6) & 0x3f))
      bytes.push(0x80 | (codePoint & 0x3f))
    }
  }
  return bytes
}

const toBase64 = (text: string): string => {
  const bytes = toUtf8Bytes(text)
  let output = ''

  for (let i = 0; i < bytes.length; i += 3) {
    const byte1 = bytes[i]
    const byte2 = i + 1 < bytes.length ? bytes[i + 1] : 0
    const byte3 = i + 2 < bytes.length ? bytes[i + 2] : 0

    const combined = (byte1 << 16) | (byte2 << 8) | byte3

    output += BASE64_ALPHABET[(combined >> 18) & 63]
    output += BASE64_ALPHABET[(combined >> 12) & 63]
    output += i + 1 < bytes.length ? BASE64_ALPHABET[(combined >> 6) & 63] : '='
    output += i + 2 < bytes.length ? BASE64_ALPHABET[combined & 63] : '='
  }

  return output
}

const normalizeBase64 = (value: string) => {
  let normalized = value.replace(/-/g, '+').replace(/_/g, '/')
  while (normalized.length % 4 !== 0) {
    normalized += '='
  }
  return normalized
}

const fromBase64ToBytes = (value: string): Uint8Array => {
  const normalized = normalizeBase64(value)
  const bytes: number[] = []

  for (let i = 0; i < normalized.length; i += 4) {
    const c1 = normalized[i]
    const c2 = normalized[i + 1]
    const c3 = normalized[i + 2]
    const c4 = normalized[i + 3]

    const n1 = BASE64_ALPHABET.indexOf(c1)
    const n2 = BASE64_ALPHABET.indexOf(c2)
    const n3 = c3 === '=' ? -1 : BASE64_ALPHABET.indexOf(c3)
    const n4 = c4 === '=' ? -1 : BASE64_ALPHABET.indexOf(c4)

    const combined = (n1 << 18) | (n2 << 12) | ((n3 < 0 ? 0 : n3) << 6) | (n4 < 0 ? 0 : n4)

    bytes.push((combined >> 16) & 255)
    if (n3 >= 0) {
      bytes.push((combined >> 8) & 255)
    }
    if (n4 >= 0) {
      bytes.push(combined & 255)
    }
  }

  return new Uint8Array(bytes)
}

export const fromBase64ToBinaryString = (value: string): string => {
  const bytes = fromBase64ToBytes(value)
  let result = ''
  for (const byte of bytes) {
    result += String.fromCharCode(byte)
  }
  return result
}

const encodeTokenSegment = (input: Record<string, unknown>) =>
  toBase64(JSON.stringify(input)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')

export const buildJwt = (payload: Record<string, unknown>) => {
  const header = encodeTokenSegment({ alg: 'HS256', typ: 'JWT' })
  const body = encodeTokenSegment(payload)
  return `${header}.${body}.signature`
}
