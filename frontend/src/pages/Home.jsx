import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { Search } from 'lucide-react'
import NewsCard from '../components/NewsCard'
import { newsApi, getLocalCache, setLocalCache } from '../lib/api'

const CATEGORY_TABS = [
  { label: 'All News', value: '' },
  { label: 'AI', value: 'AI' },
  { label: 'Sports', value: 'Sports' },
]

const getArticleTags = (article) => {
  if (Array.isArray(article.tags)) return article.tags
  if (typeof article.tags === 'string')
    return article.tags.split(',').map((t) => t.trim()).filter(Boolean)
  return []
}

const hasTag = (article, tag) =>
  getArticleTags(article).some((v) => v.toLowerCase() === tag.toLowerCase())

// ── Skeleton card ─────────────────────────────────────────────────
function SkeletonCard({ compact = false }) {
  if (compact) {
    return (
      <div className="flex gap-4 overflow-hidden rounded-[22px] border border-slate-200/70 bg-white/90 p-4">
        <div className="h-20 w-20 shrink-0 animate-pulse rounded-[14px] bg-slate-200" />
        <div className="flex-1 space-y-2 py-1">
          <div className="h-3 w-1/3 animate-pulse rounded-full bg-slate-200" />
          <div className="h-4 animate-pulse rounded-full bg-slate-200" />
          <div className="h-4 w-3/4 animate-pulse rounded-full bg-slate-200" />
        </div>
      </div>
    )
  }
  return (
    <div className="overflow-hidden rounded-[28px] border border-slate-200/70 bg-white/90">
      <div className="aspect-[16/10] animate-pulse bg-slate-200" />
      <div className="space-y-3 p-5">
        <div className="h-3 w-1/4 animate-pulse rounded-full bg-slate-200" />
        <div className="h-5 animate-pulse rounded-full bg-slate-200" />
        <div className="h-5 w-5/6 animate-pulse rounded-full bg-slate-200" />
        <div className="h-4 w-4/6 animate-pulse rounded-full bg-slate-200" />
      </div>
    </div>
  )
}

function SkeletonGrid() {
  return (
    <div className="space-y-14">
      <section>
        <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
          <SkeletonCard />
          <div className="flex flex-col gap-4">
            <SkeletonCard compact />
            <SkeletonCard compact />
            <SkeletonCard compact />
          </div>
        </div>
      </section>
      <section className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </section>
    </div>
  )
}

function Home() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [activeTag, setActiveTag] = useState('')
  const fetchingRef = useRef(false)

  const cacheKey = `news:${search}:${activeTag}`

  const fetchNews = useCallback(async () => {
    if (fetchingRef.current) return
    fetchingRef.current = true
    setError('')

    // Show stale cache immediately — zero perceived latency on return visits
    const cached = getLocalCache(cacheKey)
    if (cached) {
      setArticles(cached)
      setLoading(false)
    } else {
      setLoading(true)
    }

    try {
      const response = await newsApi.getAll(search, activeTag)
      setArticles(response.data)
      setLoading(false)
      if (!search) {
        setLocalCache(cacheKey, response.data)
      }
    } catch (err) {
      console.error('Error fetching news:', err)
      if (!cached) {
        setLoading(false)
        setError('Unable to load news right now. Please try again in a moment.')
      }
      // With stale data visible, silently skip showing an error
    } finally {
      fetchingRef.current = false
    }
  }, [activeTag, search, cacheKey])

  useEffect(() => {
    fetchNews()
  }, [fetchNews])

  const featuredArticle = articles[0]
  const secondaryArticles = articles.slice(1, 4)
  const restArticles = articles.slice(4)
  const aiArticles = useMemo(
    () => articles.filter((a) => hasTag(a, 'AI')),
    [articles],
  )
  const sportsArticles = useMemo(
    () => articles.filter((a) => hasTag(a, 'Sports')),
    [articles],
  )

  const activeLabel = useMemo(
    () => CATEGORY_TABS.find((t) => t.value === activeTag)?.label ?? 'All News',
    [activeTag],
  )

  const handleSearch = (e) => {
    e.preventDefault()
    setSearch(searchInput)
  }

  return (
    <>
      <Helmet>
        <title>TheCloudMind.ai — AI and Sports Newsroom</title>
        <meta
          name="description"
          content="Direct-source AI and sports coverage, rewritten into concise original analysis for fast reading."
        />
        <meta
          name="keywords"
          content="AI news, sports news, artificial intelligence, analysis, newsroom"
        />
        <meta property="og:title" content="TheCloudMind.ai — AI and Sports Newsroom" />
        <meta
          property="og:description"
          content="Original AI and sports coverage built from direct sources and rewritten for clarity."
        />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://cloudmindai.in/" />
        <meta name="twitter:card" content="summary_large_image" />
        <link rel="canonical" href="https://cloudmindai.in/" />
      </Helmet>

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8">

        {/* Filter + Search bar */}
        <section className="mb-8 md:mb-10">
          <div className="glass-panel rounded-[24px] px-4 py-4 sm:px-6 sm:py-5">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div className="min-w-0">
                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">
                  Browse by topic
                </p>
                <div className="mt-2 flex gap-2 overflow-x-auto pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
                  {CATEGORY_TABS.map((tab) => {
                    const isActive = tab.value === activeTag
                    return (
                      <button
                        key={tab.label}
                        type="button"
                        onClick={() => setActiveTag(tab.value)}
                        className={`shrink-0 rounded-full border px-5 py-2 text-sm font-semibold transition ${
                          isActive
                            ? 'border-slate-950 bg-slate-950 text-white shadow-sm'
                            : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:text-slate-950'
                        }`}
                      >
                        {tab.label}
                      </button>
                    )
                  })}
                </div>
              </div>

              <form onSubmit={handleSearch} className="w-full lg:max-w-xl">
                <div className="flex gap-2 sm:gap-3">
                  <div className="relative flex-1">
                    <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                    <input
                      type="text"
                      value={searchInput}
                      onChange={(e) => setSearchInput(e.target.value)}
                      placeholder="Search stories…"
                      className="w-full rounded-2xl border border-slate-200 bg-white py-3 pl-11 pr-4 text-sm text-slate-900 outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-100"
                    />
                  </div>
                  <button
                    type="submit"
                    className="rounded-2xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
                  >
                    Search
                  </button>
                </div>
              </form>
            </div>
          </div>
        </section>

        {/* Section heading */}
        <section className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
            {activeLabel}
          </p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
            {activeTag === 'AI'
              ? 'AI coverage — analysis and developments'
              : activeTag === 'Sports'
              ? 'Sports coverage — results and analysis'
              : 'Original reporting built for fast reading'}
          </h1>
        </section>

        {/* Content */}
        {loading ? (
          <SkeletonGrid />
        ) : error ? (
          <div className="rounded-[28px] border border-red-200 bg-white/90 p-10 text-center shadow-sm">
            <p className="text-lg font-medium text-red-600">{error}</p>
            <button
              onClick={fetchNews}
              className="mt-5 rounded-full bg-slate-950 px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              Retry
            </button>
          </div>
        ) : articles.length === 0 ? (
          <div className="rounded-[28px] border border-slate-200 bg-white/90 p-12 text-center shadow-sm">
            <p className="text-xl text-slate-500">No articles found.</p>
          </div>
        ) : (
          <div className="space-y-14">

            {/* Hero */}
            {featuredArticle && (
              <section>
                <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
                  <div className="overflow-hidden rounded-[32px] border border-slate-200/70 bg-white/90 shadow-[0_22px_65px_rgba(15,23,42,0.07)] transition duration-300 hover:-translate-y-1 hover:shadow-[0_28px_80px_rgba(15,23,42,0.12)]">
                    <NewsCard article={featuredArticle} />
                  </div>
                  <div className="flex flex-col gap-4">
                    {secondaryArticles.map((article) => (
                      <NewsCard key={article.id} article={article} compact />
                    ))}
                  </div>
                </div>
              </section>
            )}

            {/* AI + Sports desk strips */}
            {!activeTag && (
              <section className="grid gap-8 xl:grid-cols-2">
                {aiArticles.length > 0 && (
                  <div className="rounded-[30px] border border-slate-200/80 bg-white/80 p-5 shadow-[0_18px_55px_rgba(15,23,42,0.05)] sm:p-6">
                    <div className="mb-5 flex items-center justify-between gap-4">
                      <div>
                        <span className="inline-block rounded-full bg-teal-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-teal-700">
                          AI Desk
                        </span>
                        <h2 className="mt-2 text-xl font-bold tracking-tight text-slate-950">
                          Artificial Intelligence
                        </h2>
                      </div>
                      <button
                        type="button"
                        onClick={() => setActiveTag('AI')}
                        className="shrink-0 rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition hover:border-teal-300 hover:text-teal-700"
                      >
                        See all AI →
                      </button>
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                      {aiArticles.slice(0, 4).map((article) => (
                        <NewsCard key={article.id} article={article} />
                      ))}
                    </div>
                  </div>
                )}

                {sportsArticles.length > 0 && (
                  <div className="rounded-[30px] border border-slate-200/80 bg-white/80 p-5 shadow-[0_18px_55px_rgba(15,23,42,0.05)] sm:p-6">
                    <div className="mb-5 flex items-center justify-between gap-4">
                      <div>
                        <span className="inline-block rounded-full bg-blue-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-blue-700">
                          Sports Desk
                        </span>
                        <h2 className="mt-2 text-xl font-bold tracking-tight text-slate-950">
                          Sports Coverage
                        </h2>
                      </div>
                      <button
                        type="button"
                        onClick={() => setActiveTag('Sports')}
                        className="shrink-0 rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition hover:border-blue-300 hover:text-blue-700"
                      >
                        See all Sports →
                      </button>
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                      {sportsArticles.slice(0, 4).map((article) => (
                        <NewsCard key={article.id} article={article} />
                      ))}
                    </div>
                  </div>
                )}
              </section>
            )}

            {/* More coverage */}
            {restArticles.length > 0 && (
              <section>
                <div className="mb-6">
                  <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
                    More coverage
                  </p>
                  <h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-950">
                    Fresh analysis across AI and sport
                  </h2>
                </div>
                <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                  {restArticles.map((article) => (
                    <NewsCard key={article.id} article={article} />
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </>
  )
}

export default Home
