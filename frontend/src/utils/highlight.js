import hljs from 'highlight.js/lib/core'
import bash from 'highlight.js/lib/languages/bash'
import c from 'highlight.js/lib/languages/c'
import cpp from 'highlight.js/lib/languages/cpp'
import css from 'highlight.js/lib/languages/css'
import javascript from 'highlight.js/lib/languages/javascript'
import kotlin from 'highlight.js/lib/languages/kotlin'
import php from 'highlight.js/lib/languages/php'
import plaintext from 'highlight.js/lib/languages/plaintext'
import python from 'highlight.js/lib/languages/python'
import ruby from 'highlight.js/lib/languages/ruby'
import rust from 'highlight.js/lib/languages/rust'
import sql from 'highlight.js/lib/languages/sql'
import xml from 'highlight.js/lib/languages/xml'

// Only register the languages used by memes to keep the bundle small
const languages = {
  bash,
  c,
  cpp,
  css,
  javascript,
  kotlin,
  php,
  plaintext,
  python,
  ruby,
  rust,
  sql,
  xml,
}

for (const [name, language] of Object.entries(languages)) {
  hljs.registerLanguage(name, language)
}

export const highlightCode = (code, language) => {
  const lang = language && hljs.getLanguage(language) ? language : 'plaintext'
  return hljs.highlight(code, { language: lang }).value
}
