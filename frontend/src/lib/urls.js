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
