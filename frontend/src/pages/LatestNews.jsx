import { useState, useEffect } from 'react'
import { Helmet } from 'react-helmet-async'
import { Loader } from 'lucide-react'
import NewsCard from '../components/NewsCard'
import { newsApi } from '../lib/api'

function LatestNews() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { fetchLatestNews() }, [])

  const fetchLatestNews = async () => {
    setLoading(true)
    try {
      const response = await newsApi.getAll()
      const sevenDaysAgo = new Date()
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)
      setArticles(response.data.filter(a => new Date(a.created_at) >= sevenDaysAgo))
    } catch (error) {
      console.error('Error fetching latest news:', error)
    } finally {
      setLoading(false)
    }
  }

  const getDaysAgo = (dateString) => {
    const days = Math.floor(Math.abs(new Date() - new Date(dateString)) / 86400000)
    if (days === 0) return 'Today'
    if (days === 1) return 'Yesterday'
    return days + 'd ago'
  }

  return (
    <>
      <Helmet>
        <title>Latest AI News - TheCloudMind.ai | Breaking AI Updates</title>
        <meta name="description" content="Discover the latest AI news from the past 7 days. Stay updated with breaking developments in artificial intelligence, machine learning, and GenAI innovations." />
        <meta name="keywords" content="latest AI news, breaking AI updates, recent AI developments" />
        <meta property="og:title" content="Latest AI News - TheCloudMind.ai" />
        <meta property="og:description" content="Breaking AI news and updates from the past 7 days." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://cloudmindai.in/latest-news" />
        <meta name="twitter:card" content="summary_large_image" />
        <link rel="canonical" href="https://cloudmindai.in/latest-news" />
      </Helmet>
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '36px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 28, flexWrap: 'wrap', gap: 16 }}>
          <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
            <div style={{ background: 'var(--teal-600)', color: '#fff', padding: 10, borderRadius: 16, boxShadow: '0 4px 12px rgba(13,148,136,.3)' }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </svg>
            </div>
            <div>
              <div className="eyebrow">LAST 7 DAYS</div>
              <h1 style={{ margin: '2px 0 0', fontSize: 30, fontWeight: 700, letterSpacing: '-.01em', color: 'var(--fg1)' }}>Latest News</h1>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <span style={{ background: 'var(--teal-50)', color: 'var(--teal-ink)', border: '1px solid #99f6e4', padding: '8px 16px', borderRadius: 9999, fontSize: 13, fontWeight: 600 }}>
              {articles.length} articles
            </span>
            <button onClick={fetchLatestNews} style={{ display: 'inline-flex', gap: 8, alignItems: 'center', padding: '10px 20px', background: 'var(--cm-card)', color: 'var(--fg3)', border: '1px solid #e2e8f0', borderRadius: 9999, fontSize: 14, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit' }}>
              Refresh
            </button>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 10, alignItems: 'center', background: 'var(--cm-card)', border: '1px solid rgba(226,232,240,.8)', padding: '14px 20px', borderRadius: 20, marginBottom: 28 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: '#94a3b8', flexShrink: 0 }}>
            <rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18"/>
          </svg>
          <span style={{ fontSize: 14, color: 'var(--fg4)' }}>Showing articles published in the last 7 days, newest first.</span>
        </div>

        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '80px 0' }}>
            <Loader size={32} className="animate-spin" style={{ color: 'var(--cm-accent)' }} />
          </div>
        ) : articles.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '80px 0', background: 'var(--cm-card)', borderRadius: 28, border: '1px solid rgba(226,232,240,.7)' }}>
            <p style={{ color: 'var(--fg4)', fontSize: 18, fontWeight: 600 }}>No Recent Articles</p>
            <p style={{ color: 'var(--fg5)', fontSize: 14, marginTop: 6 }}>No articles have been published in the last 7 days.</p>
          </div>
        ) : (
          <div className="coverage-grid">
            {articles.map(a => (
              <div key={a.id} style={{ position: 'relative' }}>
                <NewsCard article={a} />
                <span style={{ position: 'absolute', top: 16, right: 16, zIndex: 2, background: 'var(--teal-600)', color: '#fff', padding: '4px 12px', borderRadius: 9999, fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.06em', boxShadow: '0 4px 10px rgba(13,148,136,.35)' }}>
                  {getDaysAgo(a.created_at)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  )
}

export default LatestNews
