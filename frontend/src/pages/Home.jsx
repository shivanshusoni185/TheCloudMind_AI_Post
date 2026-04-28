import { useState, useEffect } from 'react'
import { Helmet } from 'react-helmet-async'
import { Search, Loader } from 'lucide-react'
import NewsCard from '../components/NewsCard'
import { newsApi } from '../lib/api'
import logo from '../assets/logo.jpg'

function Home() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')

  useEffect(() => {
    fetchNews()
  }, [search])

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

  const handleSearch = (e) => {
    e.preventDefault()
    setSearch(searchInput)
  }

  return (
    <>
      <Helmet>
        <title>TheCloudMind.ai - Latest AI News & Insights</title>
        <meta name="description" content="Stay updated with the latest AI news, artificial intelligence developments, machine learning breakthroughs, and GenAI innovations. Your trusted source for AI insights and technology trends." />
        <meta name="keywords" content="AI news, artificial intelligence, machine learning, GenAI, AI insights, AI developments, technology news, AI innovations" />
        <meta property="og:title" content="TheCloudMind.ai - Latest AI News & Insights" />
        <meta property="og:description" content="Your trusted source for AI news, developments, and innovations from around the world." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://cloudmindai.in/" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="TheCloudMind.ai - Latest AI News & Insights" />
        <meta name="twitter:description" content="Your trusted source for AI news, developments, and innovations from around the world." />
        <link rel="canonical" href="https://cloudmindai.in/" />
      </Helmet>
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Hero */}
        <div className="text-center mb-12">
          <div className="flex justify-center mb-6">
            <img
              src={logo}
              alt="TheCloudMind.ai"
              className="h-32 w-32 md:h-40 md:w-40 rounded-full object-cover shadow-2xl ring-4 ring-blue-100 hover:ring-blue-200 transition-all"
            />
          </div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold mb-3 sm:mb-4 px-4">
            <span className="bg-gradient-to-r from-cyan-500 via-blue-600 to-purple-600 bg-clip-text text-transparent">
              TheCloudMind.ai
            </span>
          </h1>
          <p className="text-lg sm:text-xl md:text-2xl font-semibold text-gray-800 mb-2 px-4">
            Latest AI News & Insights
          </p>
          <p className="text-sm sm:text-base md:text-lg text-gray-600 mb-6 sm:mb-8 px-4">
            Your trusted source for AI developments and innovations
          </p>
          <form onSubmit={handleSearch} className="max-w-xl mx-auto px-4">
            <div className="relative">
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Search news..."
                className="w-full px-4 sm:px-5 py-2.5 sm:py-3 pl-10 sm:pl-12 pr-20 sm:pr-24 rounded-full border border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition text-sm sm:text-base"
              />
              <Search className="absolute left-3 sm:left-4 top-1/2 -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-gray-400" />
              <button
                type="submit"
                className="absolute right-1.5 sm:right-2 top-1/2 -translate-y-1/2 px-3 sm:px-6 py-1.5 sm:py-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition text-sm sm:text-base"
              >
                Search
              </button>
            </div>
          </form>
        </div>

        {loading ? (
          <div className="flex justify-center items-center py-20">
            <Loader className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : articles.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-gray-500 text-xl">No articles found</p>
            {search && (
              <button
                onClick={() => { setSearch(''); setSearchInput('') }}
                className="mt-4 text-blue-600 hover:underline"
              >
                Clear search
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {articles.map((article) => (
              <NewsCard key={article.id} article={article} />
            ))}
          </div>
        )}
      </div>
    </>
  )
}

export default Home
