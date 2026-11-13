import { Marked } from 'marked'
import markedKatex from 'marked-katex-extension'
import DOMPurify from 'dompurify'
import katexCssUrl from 'katex/dist/katex.min.css?url'
import 'katex/dist/katex.min.css'

// A separate instance: notifications use the shared `marked`, where "$" is not math
const examMarked = new Marked({ gfm: true, breaks: true }).use(
  markedKatex({ throwOnError: false, nonStandard: true })
)

// Render AI-generated exam Markdown (with $…$ / $$…$$ math) to safe HTML
export const renderExamMarkdown = (markdown) => {
  if (!markdown) return ''
  try {
    return DOMPurify.sanitize(examMarked.parse(markdown))
  } catch (error) {
    console.error('Exam markdown render error:', error)
    return DOMPurify.sanitize(markdown)
  }
}

const escapeHtml = (value) =>
  String(value ?? '').replace(
    /[&<>"']/g,
    (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]
  )

// A standalone page for printing. Its <title> becomes the default PDF file name.
export const buildExamPrintDocument = ({ title, html }) => `<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>${escapeHtml(title)}</title>
<link rel="stylesheet" href="${new URL(katexCssUrl, window.location.href).href}">
<style>
  @page { size: A4; margin: 18mm 16mm; }
  body {
    font-family: "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", "Heiti TC", sans-serif;
    font-size: 11pt; line-height: 1.7; color: #111; margin: 0;
  }
  h1, h2, h3 { line-height: 1.3; break-after: avoid; }
  h1 { font-size: 18pt; } h2 { font-size: 15pt; margin-top: 1.6em; } h3 { font-size: 12.5pt; }
  p, li { orphans: 3; widows: 3; }
  li { margin: 0.25em 0; }
  blockquote { margin: 0 0 1em; padding: 0.5em 0.9em; border-left: 3px solid #999; color: #444; }
  pre { background: #f5f5f5; padding: 0.7em; border-radius: 4px; white-space: pre-wrap;
        word-break: break-word; break-inside: avoid; font-size: 9.5pt; }
  code { font-family: "SF Mono", Menlo, Consolas, monospace; }
  table { border-collapse: collapse; margin: 0.8em 0; break-inside: avoid; }
  th, td { border: 1px solid #999; padding: 0.3em 0.6em; }
  hr { border: none; border-top: 1px solid #bbb; margin: 1.5em 0; }
  .katex-display { overflow-x: auto; overflow-y: hidden; }
</style>
</head>
<body>${html}</body>
</html>`

// Open the browser's print dialog for the exam, where "Save as PDF" is available
export const printExam = ({ title, html }) =>
  new Promise((resolve, reject) => {
    const frame = document.createElement('iframe')
    frame.setAttribute('aria-hidden', 'true')
    frame.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;border:0;'
    document.body.appendChild(frame)

    const cleanup = () => setTimeout(() => frame.remove(), 1000)
    frame.onload = () => {
      try {
        const win = frame.contentWindow
        // Wait for KaTeX fonts so formulas are not printed with fallback glyphs
        const fontsReady = win.document.fonts?.ready ?? Promise.resolve()
        fontsReady.then(() => {
          win.focus()
          win.print()
          cleanup()
          resolve()
        })
      } catch (error) {
        cleanup()
        reject(error)
      }
    }
    frame.srcdoc = buildExamPrintDocument({ title, html })
  })
