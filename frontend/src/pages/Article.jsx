import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { ArrowLeft, Calendar, Tag, Loader } from 'lucide-react'
import { newsApi, getImageUrl } from '../lib/api'

function Article() {
  const { slug } = useParams()
  const [article, setArticle] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => { fetchArticle() }, [slug])

  const fetchArticle = async () => {
    setLoading(true)
    try {
      const response = await newsApi.getBySlug(slug)
      setArticle(response.data)
    } catch (err) {
      setError('Article not found')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '80px 0' }}>
        <Loader size={32} className="animate-spin" style={{ color: 'var(--cm-accent)' }} />
      </div>
    )
  }

  if (error || !article) {
    return (
      <div style={{ maxWidth: 960, margin: '0 auto', padding: '32px 24px' }}>
        <Link to="/" style={{ display: 'inline-flex', gap: 8, alignItems: 'center', fontSize: 14, fontWeight: 500, color: 'var(--fg3)', textDecoration: 'none' }}>
          <ArrowLeft size={16} /> Back to Home
        </Link>
        <div style={{ textAlign: 'center', padding: '80px 0' }}>
          <p style={{ color: 'var(--fg4)', fontSize: 18 }}>{error || 'Article not found'}</p>
        </div>
      </div>
    )
  }

  const imageUrl = getImageUrl(article.image_url)
  const tags = Array.isArray(article.tags)
    ? article.tags
    : article.tags
    ? article.tags.split(',').map(t => t.trim())
    : []
  const date = new Date(article.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
  const articleUrl = `https://cloudmindai.in/article/${article.slug}`
  const description = article.summary || article.content.substring(0, 160) + '...'

  return (
    <>
      <Helmet>
        <title>{article.title} - TheCloudMind.ai</title>
        <meta name="description" content={description} />
        <meta name="keywords" content={`${tags.join(', ')}, AI news, artificial intelligence`} />
        <meta property="og:title" content={article.title} />
        <meta property="og:description" content={description} />
        <meta property="og:type" content="article" />
        <meta property="og:url" content={articleUrl} />
        {imageUrl && <meta property="og:image" content={imageUrl} />}
        <meta property="article:published_time" content={article.created_at} />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={article.title} />
        <meta name="twitter:description" content={description} />
        {imageUrl && <meta name="twitter:image" content={imageUrl} />}
        <link rel="canonical" href={articleUrl} />
      </Helmet>

      <article style={{ maxWidth: 960, margin: '0 auto', padding: '32px 24px' }}>
        <Link to="/" style={{ display: 'inline-flex', gap: 8, alignItems: 'center', fontSize: 14, fontWeight: 500, color: 'var(--fg3)', textDecoration: 'none', marginBottom: 22 }}>
          <ArrowLeft size={16} /> Back to Home
        </Link>

        {imageUrl && (
          <div style={{ marginTop: 22, borderRadius: 32, overflow: 'hidden', border: '1px solid #e2e8f0', boxShadow: 'var(--shadow-card)' }}>
            <img src={imageUrl} alt={article.title} style={{ width: '100%', display: 'block', aspectRatio: '16/9', objectFit: 'cover' }} />
          </div>
        )}

        <header style={{ marginTop: 20, background: 'var(--cm-card)', border: '1px solid #e2e8f0', borderRadius: 32, padding: 32, boxShadow: 'var(--shadow-card)' }}>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.24em', color: 'var(--fg5)', marginBottom: 14 }}>
            <span style={{ display: 'inline-flex', gap: 6, alignItems: 'center' }}>
              <Calendar size={13} /> {date}
            </span>
            {tags.map(t => (
              <span key={t} style={{ display: 'inline-flex', gap: 6, alignItems: 'center', background: '#f1f5f9', color: '#475569', padding: '3px 10px', borderRadius: 9999, fontSize: 11, letterSpacing: '.18em' }}>
                <Tag size={11} /> {t}
              </span>
            ))}
          </div>
          <h1 style={{ margin: 0, fontSize: 'clamp(26px, 4vw, 42px)', fontWeight: 700, lineHeight: 1.1, letterSpacing: '-.015em', color: 'var(--fg1)' }}>
            {article.title}
          </h1>
          {article.summary && (
            <p style={{ margin: '16px 0 0', fontFamily: 'var(--font-serif)', fontSize: 19, lineHeight: 1.7, color: 'var(--fg4)' }}>
              {article.summary}
            </p>
          )}
        </header>

        <div
          className="article-body"
          style={{ marginTop: 20, background: 'var(--cm-card)', border: '1px solid #e2e8f0', borderRadius: 28, padding: '28px 32px', boxShadow: 'var(--shadow-rest)' }}
          dangerouslySetInnerHTML={{ __html: article.content }}
        />
      </article>
    </>
  )
}

export default Article
