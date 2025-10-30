import { describe, it, expect } from 'vitest'
import { renderMarkdown } from '@/utils/markdown'

describe('markdown utility', () => {
  it('renders basic markdown text', () => {
    const result = renderMarkdown('Hello **world**')
    expect(result).toContain('<strong>world</strong>')
  })

  it('renders markdown links with target="_blank"', () => {
    const result = renderMarkdown('[GitHub](https://github.com)')
    expect(result).toContain('href="https://github.com"')
    expect(result).toContain('target="_blank"')
    expect(result).toContain('rel="noopener noreferrer"')
    expect(result).toContain('>GitHub</a>')
  })

  it('renders markdown with line breaks (GFM)', () => {
    const result = renderMarkdown('Line 1\nLine 2')
    expect(result).toContain('<br>')
  })

  it('renders markdown headers', () => {
    expect(renderMarkdown('# Heading 1')).toContain('<h1')
    expect(renderMarkdown('## Heading 2')).toContain('<h2')
    expect(renderMarkdown('### Heading 3')).toContain('<h3')
  })

  it('renders markdown lists', () => {
    const unordered = renderMarkdown('- Item 1\n- Item 2')
    expect(unordered).toContain('<ul>')
    expect(unordered).toContain('<li>Item 1</li>')

    const ordered = renderMarkdown('1. First\n2. Second')
    expect(ordered).toContain('<ol>')
    expect(ordered).toContain('<li>First</li>')
  })

  it('renders markdown code blocks', () => {
    const inline = renderMarkdown('Use `console.log()` function')
    expect(inline).toContain('<code>console.log()</code>')

    const block = renderMarkdown('```js\nconst x = 1\n```')
    expect(block).toContain('<pre>')
    expect(block).toContain('<code')
  })

  it('renders markdown blockquotes', () => {
    const result = renderMarkdown('> This is a quote')
    expect(result).toContain('<blockquote>')
    expect(result).toContain('This is a quote')
  })

  it('sanitizes potentially dangerous HTML', () => {
    const result = renderMarkdown('<script>alert("xss")</script>')
    expect(result).not.toContain('<script>')
    expect(result).not.toContain('alert')
  })

  it('handles empty or null input', () => {
    expect(renderMarkdown('')).toBe('')
    expect(renderMarkdown(null)).toBe('')
    expect(renderMarkdown(undefined)).toBe('')
  })

  it('renders complex markdown with multiple elements', () => {
    const result = renderMarkdown(
      'This is **bold** and *italic* text with a [link](https://example.com)'
    )

    expect(result).toContain('<strong>bold</strong>')
    expect(result).toContain('<em>italic</em>')
    expect(result).toContain('href="https://example.com"')
    expect(result).toContain('target="_blank"')
  })

  it('handles markdown with special characters', () => {
    const result = renderMarkdown('Text with & < > " characters')
    expect(result).toContain('&amp;')
    expect(result).toContain('&lt;')
    expect(result).toContain('&gt;')
  })

  it('preserves links with query parameters', () => {
    const result = renderMarkdown('[Link](https://example.com?foo=bar&baz=qux)')
    expect(result).toContain('href="https://example.com?foo=bar&amp;baz=qux"')
    expect(result).toContain('target="_blank"')
  })
})
