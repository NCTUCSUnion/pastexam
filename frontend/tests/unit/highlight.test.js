import { describe, expect, it } from 'vitest'
import { highlightCode } from '@/utils/highlight'

describe('highlightCode', () => {
  it('highlights registered languages', () => {
    expect(highlightCode('const a = 1', 'javascript')).toContain('hljs-keyword')
  })

  it('supports the html alias', () => {
    expect(highlightCode('<div></div>', 'html')).toContain('hljs-tag')
  })

  it('falls back to plaintext for unknown or missing languages', () => {
    expect(highlightCode('<b>', 'brainfuck')).toBe('&lt;b&gt;')
    expect(highlightCode('<b>', '')).toBe('&lt;b&gt;')
  })
})
