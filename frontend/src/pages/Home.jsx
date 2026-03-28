import { useEffect, useMemo, useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { Search, Loader, Sparkles, Newspaper, Radar } from 'lucide-react'
import NewsCard from '../components/NewsCard'
import { newsApi } from '../lib/api'
import logo from '../assets/logo.jpg'

function Home() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')

  useEffect(() => {
    fetchNews()
  }, [search])

  const fetchNews = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await newsApi.getAll(search)
      setArticles(response.data)
    } catch (err) {
      console.error('Error fetching news:', err)
      setArticles([])
      setError('Unable to load news right now. Please try again in a moment.')
    } finally {
      setLoading(false)
    }
  }

  const featuredArticle = articles[0]
  const secondaryArticles = articles.slice(1, 7)
  const restArticles = articles.slice(7)

  const stats = useMemo(() => {
    const tags = new Set()
    articles.forEach(article => {
      const values = Array.isArray(article.tags) ? article.tags : []
      values.forEach(tag => tags.add(tag))
    })
    return {
      count: articles.length,
      tags: tags.size,
    }
  }, [articles])

  const handleSearch = (e) => {
    e.preventDefault()
    setSearch(searchInput)
  }

  return (
    <>
      <Helmet>
        <title>TheCloudMind.ai - AI and Sports Newsroom</title>
        <meta
          name="description"
          content="Direct-source AI and sports coverage, rewritten into concise original analysis for fast reading."
        />
        <meta
          name="keywords"
          content="AI news, sports news, artificial intelligence, analysis, newsroom, direct sources"
        />
        <meta property="og:title" content="TheCloudMind.ai - AI and Sports Newsroom" />
        <meta
          property="og:description"
          content="Original AI and sports coverage built from direct sources and rewritten for clarity."
        />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://cloudmindai.in/" />
        <meta name="twitter:card" content="summary_large_image" />
        <link rel="canonical" href="https://cloudmindai.in/" />
      </Helmet>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-10">
        <section className="hero-grid glass-panel overflow-hidden rounded-[36px] px-6 py-8 sm:px-10 sm:py-12">
          <div className="grid gap-8 lg:grid-cols-[1.3fr_0.7fr] lg:items-end">
            <div>
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/80 px-4 py-2 text-xs font-semibold uppercase tracking-[0.28em] text-slate-600">
                <Sparkles className="h-4 w-4 text-teal-600" />
                Direct-source newsroom workflow
              </div>

              <div className="flex items-center gap-4">
                <img
                  src={logo}
                  alt="TheCloudMind.ai"
                  className="h-20 w-20 rounded-[28px] object-cover shadow-xl ring-4 ring-white/80 sm:h-24 sm:w-24"
                />
                <div>
                  <h1 className="text-4xl font-bold tracking-tight text-slate-950 sm:text-6xl">
                    TheCloudMind.ai
                  </h1>
                  <p className="mt-2 max-w-2xl font-editorial text-xl leading-8 text-slate-600">
                    AI and sports coverage rewritten into crisp original analysis instead of copied feed text.
                  </p>
                </div>
              </div>

              <form onSubmit={handleSearch} className="mt-8 max-w-2xl">
                <div className="flex flex-col gap-3 rounded-[24px] border border-white/70 bg-white/85 p-3 shadow-lg sm:flex-row">
                  <div className="relative flex-1">
                    <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                    <input
                      type="text"
                      value={searchInput}
                      onChange={(e) => setSearchInput(e.target.value)}
                      placeholder="Search AI, sport, policy, markets..."
                      className="w-full rounded-2xl border border-slate-200 bg-slate-50 py-3 pl-12 pr-4 text-sm text-slate-900 outline-none transition focus:border-teal-500 focus:bg-white"
                    />
                  </div>
                  <button
                    type="submit"
                    className="rounded-2xl bg-slate-950 px-6 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
                  >
                    Search
                  </button>
                </div>
              </form>
            </div>

            <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1">
              <div className="rounded-[28px] border border-white/70 bg-white/85 p-5">
                <div className="flex items-center gap-3 text-sm font-semibold uppercase tracking-[0.22em] text-slate-500">
                  <Newspaper className="h-4 w-4 text-teal-600" />
                  Live stories
                </div>
                <div className="mt-3 text-4xl font-bold text-slate-950">{stats.count}</div>
              </div>
              <div className="rounded-[28px] border border-white/70 bg-white/85 p-5">
                <div className="flex items-center gap-3 text-sm font-semibold uppercase tracking-[0.22em] text-slate-500">
                  <Radar className="h-4 w-4 text-blue-600" />
                  Active beats
                </div>
                <div className="mt-3 text-4xl font-bold text-slate-950">{stats.tags}</div>
              </div>
            </div>
          </div>
        </section>

        {loading ? (
          <div className="flex justify-center py-20">
            <Loader className="h-8 w-8 animate-spin text-teal-600" />
          </div>
        ) : error ? (
          <div className="rounded-[28px] border border-red-200 bg-white/90 p-10 text-center shadow-sm">
            <p className="text-lg font-medium text-red-600">{error}</p>
            <button
              onClick={fetchNews}
              className="mt-5 rounded-full bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              Retry
            </button>
          </div>
        ) : articles.length === 0 ? (
          <div className="rounded-[28px] border border-slate-200 bg-white/90 p-12 text-center shadow-sm">
            <p className="text-xl text-slate-500">No articles found.</p>
          </div>
        ) : (
          <div className="mt-10 space-y-12">
            {featuredArticle && (
              <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-stretch">
                <div className="glass-panel overflow-hidden rounded-[34px] p-4">
                  <NewsCard article={featuredArticle} />
                </div>
                <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-1">
                  {secondaryArticles.slice(0, 3).map(article => (
                    <NewsCard key={article.id} article={article} />
                  ))}
                </div>
              </section>
            )}

            {restArticles.length > 0 && (
              <section>
                <div className="mb-5 flex items-center justify-between">
                  <div>
                    <div className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
                      More coverage
                    </div>
                    <h2 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">
                      Fresh analysis across AI and sport
                    </h2>
                  </div>
                </div>
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {restArticles.map(article => (
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
