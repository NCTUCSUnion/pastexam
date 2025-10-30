import { marked } from 'marked'
import DOMPurify from 'dompurify'

// Configure marked options
marked.use({
  breaks: true,
  gfm: true,
  renderer: {
    link({ href, title, text }) {
      const safeHref = href ?? ''
      const titleAttr = title ? ` title="${title}"` : ''
      return `<a href="${safeHref}"${titleAttr} target="_blank" rel="noopener noreferrer">${text}</a>`
    },
  },
})

export const renderMarkdown = (markdown) => {
  if (!markdown) return ''
  try {
    const rawHtml = marked.parse(markdown)
    // Configure DOMPurify to allow target attribute when sanitizing
    return DOMPurify.sanitize(rawHtml, {
      ADD_ATTR: ['target'],
    })
  } catch (error) {
    console.error('Markdown render error:', error)
    return DOMPurify.sanitize(markdown, {
      ADD_ATTR: ['target'],
    })
  }
}
