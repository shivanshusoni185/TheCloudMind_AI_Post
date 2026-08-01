import { marked } from 'marked'
import DOMPurify from 'dompurify'

// Article content is stored in two shapes across the codebase:
//   • RSS/auto-publish path → Markdown ("## What happened", blank-line paragraphs,
//     a "Source note:" / "Original source: <url>" trailer)
//   • CrewAI path → raw HTML ("<p>…</p><p>…</p>")
// marked() renders Markdown to HTML and passes through any block-level HTML it
// finds, so a single pass handles both. GFM autolinks bare URLs (the source line).
marked.setOptions({ gfm: true, breaks: true })

// Open source/citation links in a new tab so readers don't lose the article.
DOMPurify.addHook('afterSanitizeAttributes', (node) => {
  if (node.tagName === 'A' && node.getAttribute('href')) {
    node.setAttribute('target', '_blank')
    node.setAttribute('rel', 'noopener noreferrer')
  }
})

export function renderArticleContent(raw) {
  if (!raw) return ''
  const html = marked.parse(raw)
  return DOMPurify.sanitize(html, { ADD_ATTR: ['target', 'rel'] })
}
