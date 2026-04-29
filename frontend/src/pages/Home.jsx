import { useState, useEffect } from 'react'
import { Helmet } from 'react-helmet-async'
import { Loader } from 'lucide-react'
import NewsCard from '../components/NewsCard'
import { newsApi } from '../lib/api'

function FilterBar({ active, onChange, search, setSearch, onSubmit }) {
  const tabs = [
    { label: 'All News', value: '' },
    { label: 'AI', value: 'AI' },
  ]
  return (
    <section style={{ marginBottom: 40 }}>
      <div className="glass-panel" style={{ padding: '18px 22px', borderRadius: 20 }}>
        <div className="filter-bar-inner">
          <div>
            <div className="eyebrow" style={{ marginBottom: 8 }}>BROWSE BY TOPIC</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {tabs.map(t => (
                <button key={t.value} onClick={() => onChange(t.value)} style={{
                  background: active === t.value ? 'var(--bg5)' : '#fff',
                  color: active === t.value ? '#fff' : 'var(--fg4)',
                  border: '1px solid ' + (active === t.value ? 'var(--bg5)' : '#e2e8f0'),
                  padding: '8px 18px', borderRadius: 9999,
                  fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit',
                  transition: 'background .15s, color .15s',
                }}>{t.label}</button>
              ))}
            </div>
          </div>
          <form onSubmit={e => { e.preventDefault(); onSubmit() }} style={{ display: 'flex', gap: 8 }}>
            <div style={{ position: 'relative' }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#94a3b8', pointerEvents: 'none' }}>
                <circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>
              </svg>
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search stories..."
                style={{
                  border: '1px solid #e2e8f0', background: '#fff', borderRadius: 14,
                  padding: '10px 14px 10px 38px', fontFamily: 'inherit', fontSize: 13,
                  outline: 'none', width: 200,
                }}
              />
            </div>
            <button type="submit" style={{
              padding: '10px 20px', background: 'var(--bg5)', color: '#fff',
              border: 'none', borderRadius: 14, fontSize: 14, fontWeight: 600,
              cursor: 'pointer', fontFamily: 'inherit',
            }}>Search</button>
          </form>
        </div>
      </div>
    </section>
  )
}

function HeroRow({ articles }) {
  const [featured, ...rest] = articles
  if (!featured) return null
  return (
    <section className="hero-row">
      <NewsCard article={featured} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {rest.slice(0, 3).map(a => <NewsCard key={a.id} article={a} compact />)}
      </div>
    </section>
  )
}

function Home() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [active, setActive] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')

  useEffect(() => { fetchNews() }, [search])

  const fetchNews = async () => {
    setLoading(true)
    try {
      const response = await newsApi.getAll(search)
      setArticles(response.data)
    } catch (error) {
      console.error('Error fetching news:', error)
    } finally {
      setLoading(false)
    }
  }

  const filtered = articles.filter(a => {
    if (!active) return true
    const tags = Array.isArray(a.tags) ? a.tags : (a.tags ? a.tags.split(',').map(t => t.trim()) : [])
    return tags.some(t => t.toLowerCase() === active.toLowerCase())
  })

  const heading = active === 'AI'
    ? 'AI coverage — analysis and developments'
    : 'Original reporting built for fast reading'

  return (
    <>
      <Helmet>
        <title>TheCloudMind.ai - Latest AI News & Insights</title>
        <meta name="description" content="Stay updated with the latest AI news, artificial intelligence developments, machine learning breakthroughs, and GenAI innovations." />
        <meta name="keywords" content="AI news, artificial intelligence, machine learning, GenAI, AI insights" />
        <meta property="og:title" content="TheCloudMind.ai - Latest AI News & Insights" />
        <meta property="og:description" content="Your trusted source for AI news, developments, and innovations from around the world." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://cloudmindai.in/" />
        <meta name="twitter:card" content="summary_large_image" />
        <link rel="canonical" href="https://cloudmindai.in/" />
      </Helmet>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 24px 16px' }}>
        <FilterBar
          active={active}
          onChange={setActive}
          search={searchInput}
          setSearch={setSearchInput}
          onSubmit={() => setSearch(searchInput)}
        />
        <section style={{ marginBottom: 32 }}>
          <div className="eyebrow">{active ? active.toUpperCase() : 'ALL NEWS'}</div>
          <h1 style={{ marginTop: 6, fontSize: 'clamp(22px, 3vw, 30px)', fontWeight: 700, letterSpacing: '-.01em', color: 'var(--fg1)' }}>
            {heading}
          </h1>
        </section>

        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '80px 0' }}>
            <Loader size={32} className="animate-spin" style={{ color: 'var(--cm-accent)' }} />
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '80px 0' }}>
            <p style={{ color: 'var(--fg4)', fontSize: 18 }}>No articles found</p>
            {(search || active) && (
              <button
                onClick={() => { setSearch(''); setSearchInput(''); setActive('') }}
                style={{ marginTop: 16, color: 'var(--cm-accent)', background: 'none', border: 'none', cursor: 'pointer', fontSize: 14, fontFamily: 'inherit', textDecoration: 'underline' }}
              >
                Clear filters
              </button>
            )}
          </div>
        ) : (
          <HeroRow articles={filtered} />
        )}
      </div>

      {!loading && filtered.length > 4 && (
        <div style={{ background: 'var(--cm-section)', borderTop: '1px solid var(--cm-border)', borderBottom: '1px solid var(--cm-border)', padding: '56px 0' }}>
          <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 24px' }}>
            <div className="eyebrow" style={{ marginBottom: 6 }}>MORE COVERAGE</div>
            <h2 style={{ margin: '0 0 24px', fontSize: 24, fontWeight: 700, letterSpacing: '-.01em', color: 'var(--fg1)' }}>
              Fresh analysis across AI and technology
            </h2>
            <div className="coverage-grid">
              {filtered.slice(4).map(a => <NewsCard key={a.id} article={a} />)}
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default Home
