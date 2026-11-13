import { describe, it, expect } from 'vitest'
import { renderExamMarkdown, buildExamPrintDocument } from '@/utils/examMarkdown'
import { renderMarkdown } from '@/utils/markdown'

describe('renderExamMarkdown', () => {
  it('renders headings, lists, tables and LaTeX math', () => {
    const html = renderExamMarkdown(
      [
        '# 期中考',
        '1. 計算 $\\int_0^1 x^2\\,dx$。（10 分）',
        '',
        '$$',
        'T(n) = 2T(n/2) + O(n)',
        '$$',
        '',
        '| n | T(n) |',
        '|---|------|',
        '| 1 | 1 |',
      ].join('\n')
    )

    expect(html).toContain('<h1')
    expect(html).toContain('<ol')
    expect(html).toContain('<table')
    expect(html).toContain('class="katex"')
    expect(html).toContain('katex-display')
    expect(html).not.toContain('$$')
  })

  it('removes scripts and event handlers from the model output', () => {
    const html = renderExamMarkdown(
      'Q1 <img src=x onerror="alert(1)"><script>alert(2)</script> [x](javascript:alert(3))'
    )

    expect(html).not.toContain('onerror')
    expect(html).not.toContain('<script')
    expect(html).not.toContain('javascript:')
  })

  it('keeps invalid LaTeX as text instead of failing', () => {
    expect(() => renderExamMarkdown('broken $\\frac{1}{$ math')).not.toThrow()
  })

  it('does not change how notifications treat dollar signs', () => {
    expect(renderMarkdown('費用 $100 和 $200')).not.toContain('katex')
  })

  it('returns an empty string for empty content', () => {
    expect(renderExamMarkdown('')).toBe('')
    expect(renderExamMarkdown(null)).toBe('')
  })
})

describe('buildExamPrintDocument', () => {
  it('uses the escaped title, which browsers use as the PDF file name', () => {
    const doc = buildExamPrintDocument({
      title: '演算法_<王>_模擬試題',
      html: '<p>Q1</p>',
    })

    expect(doc).toContain('<title>演算法_&lt;王&gt;_模擬試題</title>')
    expect(doc).toContain('<body><p>Q1</p></body>')
    expect(doc).toContain('@page')
  })
})
