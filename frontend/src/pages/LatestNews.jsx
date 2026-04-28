import { useState, useEffect } from 'react'
import { Helmet } from 'react-helmet-async'
import { Calendar, Loader, TrendingUp } from 'lucide-react'
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
      const recentArticles = response.data.filter(
        (article) => new Date(article.created_at) >= sevenDaysAgo
      )
      setArticles(recentArticles)
    } catch (error) {
      console.error('Error fetching latest news:', error)
    } finally {
      setLoading(false)
    }
  }

  const getDaysAgo = (dateString) => {
    const diffDays = Math.floor(
      Math.abs(new Date() - new Date(dateString)) / (1000 * 60 * 60 * 24)
    )
    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    return `${diffDays} days ago`
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  return (
    <>
      <Helmet>
        <title>Latest AI News - TheCloudMind.ai | Breaking AI Updates</title>
        <meta name="description" content="Discover the latest AI news from the past 7 days. Stay updated with breaking developments in artificial intelligence, machine learning, and GenAI innovations." />
        <meta name="keywords" content="latest AI news, breaking AI updates, recent AI developments, AI news today, artificial intelligence updates" />
        <meta property="og:title" content="Latest AI News - TheCloudMind.ai" />
        <meta property="og:description" content="Breaking AI news and updates from the past 7 days." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://cloudmindai.in/latest-news" />
        <meta name="twitter:card" content="summary_large_image" />
        <link rel="canonical" href="https://cloudmindai.in/latest-news" />
      </Helmet>
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6 sm:mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 sm:p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
              <TrendingUp className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900">Latest News</h1>
              <p className="text-gray-600 flex items-center gap-2 mt-1 text-sm sm:text-base">
                <Calendar className="w-3 h-3 sm:w-4 sm:h-4" />
                Articles from the last 7 days
              </p>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="bg-blue-500 text-white font-bold text-lg sm:text-xl rounded-full w-9 h-9 sm:w-10 sm:h-10 flex items-center justify-center flex-shrink-0">
                {articles.length}
              </div>
              <span className="text-gray-700 font-medium text-sm sm:text-base">
                {articles.length === 1 ? 'article' : 'articles'} published in the last week
              </span>
            </div>
            <button
              onClick={fetchLatestNews}
              className="text-blue-600 hover:text-blue-800 font-medium flex items-center gap-2 text-sm sm:text-base"
            >
              <Loader className="w-4 h-4" />
              Refresh
            </button>
          </div>
        </div>

        {articles.length === 0 ? (
          <div className="text-center py-20 bg-gray-50 rounded-xl">
            <Calendar className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-600 mb-2">No Recent Articles</h3>
            <p className="text-gray-500">No articles have been published in the last 7 days.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {articles.map((article) => (
              <div key={article.id} className="relative">
                <NewsCard article={article} />
                <div className="absolute top-4 right-4 bg-blue-600 text-white text-xs font-semibold px-3 py-1 rounded-full shadow-lg">
                  {getDaysAgo(article.created_at)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  )
}

export default LatestNews
