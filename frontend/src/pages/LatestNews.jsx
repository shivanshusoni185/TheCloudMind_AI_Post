import { useState, useEffect } from 'react'
import { Helmet } from 'react-helmet-async'
import { Calendar, Loader, TrendingUp, RefreshCw } from 'lucide-react'
import NewsCard from '../components/NewsCard'
import { newsApi } from '../lib/api'

function LatestNews() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchLatestNews()
  }, [])

  const fetchLatestNews = async () => {
    setLoading(true)
    try {
      const response = await newsApi.getAll()
      const sevenDaysAgo = new Date()
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)
      const recent = response.data.filter(
        (a) => new Date(a.created_at) >= sevenDaysAgo,
      )
      setArticles(recent)
    } catch (error) {
      console.error('Error fetching latest news:', error)
    } finally {
      setLoading(false)
    }
  }

  const getDaysAgo = (dateString) => {
    const diffDays = Math.floor(
      Math.abs(new Date() - new Date(dateString)) / (1000 * 60 * 60 * 24),
    )
    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    return `${diffDays}d ago`
  }

  return (
    <>
      <Helmet>
        <title>Latest News — TheCloudMind.ai</title>
        <meta
          name="description"
          content="The freshest AI and sports stories from the last 7 days on TheCloudMind.ai."
        />
        <meta
          name="keywords"
          content="latest AI news, breaking AI updates, recent AI developments, sports news today"
        />
        <meta property="og:title" content="Latest News — TheCloudMind.ai" />
        <meta
          property="og:description"
          content="Breaking AI and sports news from the past 7 days."
        />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://cloudmindai.in/latest-news" />
        <meta name="twitter:card" content="summary_large_image" />
        <link rel="canonical" href="https://cloudmindai.in/latest-news" />
      </Helmet>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-10">
        {/* Page header */}
        <div className="mb-8 sm:mb-10">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <div className="flex items-center gap-3">
                <div className="rounded-2xl bg-teal-600 p-2.5 shadow-md">
                  <TrendingUp className="h-6 w-6 text-white" />
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
                    Last 7 days
                  </p>
                  <h1 className="text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
                    Latest News
                  </h1>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {!loading && (
                <span className="rounded-full border border-teal-200 bg-teal-50 px-4 py-2 text-sm font-semibold text-teal-700">
                  {articles.length} {articles.length === 1 ? 'article' : 'articles'}
                </span>
              )}
              <button
                onClick={fetchLatestNews}
                disabled={loading}
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 hover:text-slate-950 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>

          <div className="mt-5 flex items-center gap-3 rounded-[20px] border border-slate-200/80 bg-white/80 px-5 py-3.5 shadow-sm">
            <Calendar className="h-4 w-4 shrink-0 text-slate-400" />
            <p className="text-sm text-slate-600">
              Showing articles published in the last 7 days, newest first.
            </p>
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex justify-center py-24">
            <Loader className="h-8 w-8 animate-spin text-teal-600" />
          </div>
        ) : articles.length === 0 ? (
          <div className="rounded-[28px] border border-slate-200 bg-white/90 p-12 text-center shadow-sm">
            <Calendar className="mx-auto mb-4 h-14 w-14 text-slate-300" />
            <h3 className="text-xl font-semibold text-slate-700">No recent articles</h3>
            <p className="mt-2 text-sm text-slate-500">
              Nothing published in the last 7 days yet.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {articles.map((article) => (
              <div key={article.id} className="relative">
                <NewsCard article={article} />
                <span className="absolute right-4 top-4 z-10 rounded-full bg-teal-600 px-3 py-1 text-[11px] font-bold uppercase tracking-wide text-white shadow-md">
                  {getDaysAgo(article.created_at)}
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
