// Canonical URL builders — dated, SEO-standard paths:
//   articles → /news/YYYY/MM/<slug>
//   jobs     → /jobs/YYYY/MM/<slug>
// The date segments come from the publish date; the slug is the real key,
// so lookups still work by slug regardless of the date in the path.

const ORIGIN = 'https://cloudmindai.in'

function ym(dateStr) {
  const d = dateStr ? new Date(dateStr) : new Date()
  const valid = !isNaN(d.getTime())
  const base = valid ? d : new Date()
  return {
    y: base.getFullYear(),
    m: String(base.getMonth() + 1).padStart(2, '0'),
  }
}

export function articlePath(article) {
  const { y, m } = ym(article?.created_at)
  return `/news/${y}/${m}/${article.slug}`
}

export function jobPath(job) {
  const { y, m } = ym(job?.posted_at || job?.created_at)
  return `/jobs/${y}/${m}/${job.slug}`
}

export const articleUrl = (article) => ORIGIN + articlePath(article)
export const jobUrl = (job) => ORIGIN + jobPath(job)

// Only allow http(s) external links; blocks javascript:/data: schemes in
// admin- or feed-supplied apply URLs from becoming an XSS/click vector.
export function safeExternalUrl(url) {
  if (typeof url !== 'string') return '#'
  return /^https?:\/\//i.test(url.trim()) ? url : '#'
}

// Serialize an object for embedding in a <script type="application/ld+json">.
// Escapes '<' so a value containing "</script>" cannot break out of the tag.
export function jsonLdSafe(obj) {
  return JSON.stringify(obj).replace(/</g, '\\u003c').replace(/>/g, '\\u003e')
}

