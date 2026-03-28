import { useEffect, useMemo, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { ArrowLeft, Calendar, ExternalLink, Loader, Tag } from 'lucide-react'
import { newsApi, getImageUrl } from '../lib/api'

function parseArticleContent(content) {
  const blocks = (content || '')
    .split('\n\n')
    .map(block => block.trim())
    .filter(Boolean)

  const sections = []
  let sourceNote = ''
  let originalSource = ''

  blocks.forEach(block => {
    if (block.startsWith('## ')) {
      const lines = block.split('\n')
      const heading = lines[0].replace(/^##\s+/, '').trim()
      const body = lines.slice(1).join(' ').trim()
      sections.push({ heading, body })
      return
    }

    if (block.startsWith('Source note:')) {
      sourceNote = block
      return
    }

    if (block.startsWith('Original source:')) {
      originalSource = block.replace('Original source:', '').trim()
    }
  })

  return { sections, sourceNote, originalSource }
}

function Article() {
  const { slug } = useParams()
  const [article, setArticle] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchArticle()
  }, [slug])

  const fetchArticle = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await newsApi.getBySlug(slug)
      setArticle(response.data)
    } catch (err) {
      setError('Article not found')
    } finally {
      setLoading(false)
    }
  }

  const parsedContent = useMemo(
    () => parseArticleContent(article?.content || ''),
    [article?.content],
  )

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <Loader className="w-8 h-8 animate-spin text-teal-600" />
      </div>
    )
  }

  if (error || !article) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
        <Link to="/" className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 transition hover:text-slate-950">
          <ArrowLeft className="h-4 w-4" />
          Back to Home
        </Link>
        <div className="mt-10 rounded-[28px] border border-slate-200 bg-white/90 p-12 text-center shadow-sm">
          <p className="text-xl text-slate-500">{error || 'Article not found'}</p>
        </div>
      </div>
    )
  }

  const imageUrl = getImageUrl(article.image_url)
  const tags = Array.isArray(article.tags)
    ? article.tags
    : (article.tags ? article.tags.split(',').map(t => t.trim()) : [])
  const date = new Date(article.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  const articleUrl = `https://cloudmindai.in/article/${article.slug}`
  const description = article.summary || `${article.title} | TheCloudMind.ai`
  const keywords = tags.join(', ')

  return (
    <>
      <Helmet>
        <title>{article.title} - TheCloudMind.ai</title>
        <meta name="description" content={description} />
        <meta name="keywords" content={`${keywords}, AI news, sports news, analysis`} />
        <meta property="og:title" content={article.title} />
        <meta property="og:description" content={description} />
        <meta property="og:type" content="article" />
        <meta property="og:url" content={articleUrl} />
        {imageUrl && <meta property="og:image" content={imageUrl} />}
        <meta property="article:published_time" content={article.created_at} />
        <meta name="twitter:card" content="summary_large_image" />
        <link rel="canonical" href={articleUrl} />
      </Helmet>

      <article className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-12">
        <Link to="/" className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 transition hover:text-slate-950">
          <ArrowLeft className="h-4 w-4" />
          Back to Home
        </Link>

        <div className="mt-6 grid gap-8 lg:grid-cols-[1fr_320px]">
          <div className="space-y-6">
            {imageUrl && (
              <div className="overflow-hidden rounded-[32px] border border-slate-200 bg-white shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
                <img
                  src={imageUrl}
                  alt={article.title}
                  className="aspect-[16/9] w-full object-cover"
                />
              </div>
            )}

            <header className="rounded-[32px] border border-slate-200 bg-white/92 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.06)] sm:p-8">
              <div className="flex flex-wrap items-center gap-3 text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
                <span className="inline-flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  {date}
                </span>
                {tags.map((tag, index) => (
                  <span key={`${tag}-${index}`} className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-[11px] text-slate-700">
                    <Tag className="h-3.5 w-3.5" />
                    {tag}
                  </span>
                ))}
              </div>

              <h1 className="mt-5 text-3xl font-bold leading-tight tracking-tight text-slate-950 sm:text-5xl">
                {article.title}
              </h1>

              <p className="font-editorial mt-5 text-xl leading-9 text-slate-600">
                {article.summary}
              </p>
            </header>

            <div className="space-y-5">
              {parsedContent.sections.map((section) => (
                <section
                  key={section.heading}
                  className="rounded-[28px] border border-slate-200 bg-white/90 p-6 shadow-[0_20px_60px_rgba(15,23,42,0.05)] sm:p-7"
                >
                  <h2 className="text-2xl font-bold tracking-tight text-slate-950">
                    {section.heading}
                  </h2>
                  <p className="font-editorial mt-3 text-[19px] leading-8 text-slate-700">
                    {section.body}
                  </p>
                </section>
              ))}
            </div>
          </div>

          <aside className="space-y-5">
            <div className="rounded-[28px] border border-slate-200 bg-white/92 p-6 shadow-[0_20px_60px_rgba(15,23,42,0.05)]">
              <div className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
                Story context
              </div>
              {parsedContent.sourceNote && (
                <p className="mt-4 text-sm leading-7 text-slate-600">
                  {parsedContent.sourceNote.replace('Source note:', '').trim()}
                </p>
              )}
              {parsedContent.originalSource && (
                <a
                  href={parsedContent.originalSource}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-teal-700 transition hover:text-teal-800"
                >
                  Open original reporting
                  <ExternalLink className="h-4 w-4" />
                </a>
              )}
            </div>
          </aside>
        </div>
      </article>
    </>
  )
}

export default Article
