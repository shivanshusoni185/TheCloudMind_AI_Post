import { useCallback, useEffect, useMemo, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { ArrowLeft, Calendar, Check, Copy, Linkedin, Loader, Tag, Twitter } from 'lucide-react'
import { newsApi, getImageUrl } from '../lib/api'

function parseArticleContent(content) {
  const blocks = (content || '')
    .split('\n\n')
    .map(block => block.trim())
    .filter(Boolean)

  const sections = []

  blocks.forEach(block => {
    if (block.startsWith('## ')) {
      const lines = block.split('\n')
      const heading = lines[0].replace(/^##\s+/, '').trim()
      const body = lines.slice(1).join(' ').trim()
      sections.push({ heading, body })
    }
  })

  return { sections }
}

// Deterministic fallback image from picsum — same article always gets same photo
function getFallbackImage(id) {
  return `https://picsum.photos/seed/tcm${id}/1200/675`
}

function ShareBar({ url, title }) {
  const [copied, setCopied] = useState(false)

  const encoded = encodeURIComponent(url)
  const encodedTitle = encodeURIComponent(title)

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // fallback for older browsers
      const el = document.createElement('textarea')
      el.value = url
      document.body.appendChild(el)
      el.select()
      document.execCommand('copy')
      document.body.removeChild(el)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="rounded-[28px] border border-slate-200 bg-white/90 p-5 shadow-[0_20px_60px_rgba(15,23,42,0.05)] sm:p-6">
      <p className="mb-4 text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">
        Share this story
      </p>
      <div className="flex flex-wrap gap-3">
        {/* WhatsApp */}
        <a
          href={`https://wa.me/?text=${encodedTitle}%0A${encoded}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-full bg-[#25D366] px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-90"
        >
          <svg className="h-4 w-4 shrink-0" fill="currentColor" viewBox="0 0 24 24">
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
          </svg>
          WhatsApp
        </a>

        {/* LinkedIn */}
        <a
          href={`https://www.linkedin.com/sharing/share-offsite/?url=${encoded}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-full bg-[#0A66C2] px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-90"
        >
          <Linkedin className="h-4 w-4 shrink-0" />
          LinkedIn
        </a>

        {/* Twitter / X */}
        <a
          href={`https://twitter.com/intent/tweet?text=${encodedTitle}&url=${encoded}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-full bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700"
        >
          <Twitter className="h-4 w-4 shrink-0" />
          Twitter / X
        </a>

        {/* Copy link */}
        <button
          type="button"
          onClick={copyLink}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:text-slate-950"
        >
          {copied ? <Check className="h-4 w-4 shrink-0 text-teal-600" /> : <Copy className="h-4 w-4 shrink-0" />}
          {copied ? 'Copied!' : 'Copy link'}
        </button>
      </div>
    </div>
  )
}

function Article() {
  const { slug } = useParams()
  const [article, setArticle] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchArticle = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await newsApi.getBySlug(slug)
      setArticle(response.data)
    } catch {
      setError('Article not found')
    } finally {
      setLoading(false)
    }
  }, [slug])

  useEffect(() => {
    fetchArticle()
  }, [fetchArticle])

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

  const imageUrl = getImageUrl(article.image_url) || getFallbackImage(article.id)
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
        <meta property="og:image" content={imageUrl} />
        <meta property="article:published_time" content={article.created_at} />
        <meta name="twitter:card" content="summary_large_image" />
        <link rel="canonical" href={articleUrl} />
      </Helmet>

      <article className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-12">
        <Link to="/" className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 transition hover:text-slate-950">
          <ArrowLeft className="h-4 w-4" />
          Back to Home
        </Link>

        <div className="mt-6 space-y-6">
          {/* Hero image — always shown (fallback to picsum if no stored image) */}
          <div className="overflow-hidden rounded-[32px] border border-slate-200 bg-white shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
            <img
              src={imageUrl}
              alt={article.title}
              className="aspect-[16/9] w-full object-cover"
            />
          </div>

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

          {/* Social share */}
          <ShareBar url={articleUrl} title={article.title} />
        </div>
      </article>
    </>
  )
}

export default Article
