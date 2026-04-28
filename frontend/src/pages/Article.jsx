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

  useEffect(() => {
    fetchArticle()
  }, [slug])

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
      <div className="flex justify-center items-center py-20">
        <Loader className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  if (error || !article) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <Link to="/" className="flex items-center text-blue-600 hover:underline mb-8">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Home
        </Link>
        <div className="text-center py-20">
          <p className="text-gray-500 text-xl">{error || 'Article not found'}</p>
        </div>
      </div>
    )
  }

  const imageUrl = getImageUrl(article.image_url)
  const tags = Array.isArray(article.tags)
    ? article.tags
    : article.tags
    ? article.tags.split(',').map((t) => t.trim())
    : []
  const date = new Date(article.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  const articleUrl = `https://cloudmindai.in/article/${article.slug}`
  const description = article.summary || article.content.substring(0, 160) + '...'
  const keywords = tags.join(', ')

  return (
    <>
      <Helmet>
        <title>{article.title} - TheCloudMind.ai</title>
        <meta name="description" content={description} />
        <meta name="keywords" content={`${keywords}, AI news, artificial intelligence, machine learning`} />
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
      <article className="max-w-4xl mx-auto px-4 py-8">
        <Link to="/" className="flex items-center text-blue-600 hover:underline mb-8">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Home
        </Link>

        {imageUrl && (
          <div className="aspect-video bg-gray-100 rounded-xl overflow-hidden mb-8">
            <img
              src={imageUrl}
              alt={article.title}
              className="w-full h-full object-cover"
            />
          </div>
        )}

        <header className="mb-8">
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 mb-4 leading-tight">
            {article.title}
          </h1>
          <div className="flex flex-wrap items-center gap-3 sm:gap-4 text-sm sm:text-base text-gray-500">
            <div className="flex items-center space-x-2">
              <Calendar className="w-4 h-4 sm:w-5 sm:h-5" />
              <span>{date}</span>
            </div>
            {tags.length > 0 && (
              <div className="flex items-start space-x-2 w-full sm:w-auto">
                <Tag className="w-4 h-4 sm:w-5 sm:h-5 mt-1 flex-shrink-0" />
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag, i) => (
                    <span key={i} className="px-2 py-1 bg-blue-100 text-blue-600 rounded text-xs sm:text-sm whitespace-nowrap">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </header>

        <div className="bg-blue-50 border-l-4 border-blue-500 p-3 sm:p-4 mb-6 sm:mb-8 rounded-r-lg">
          <p className="text-gray-700 text-base sm:text-lg italic leading-relaxed">
            {article.summary}
          </p>
        </div>

        <div
          className="prose prose-sm sm:prose-base lg:prose-lg max-w-none text-gray-700 leading-relaxed"
          dangerouslySetInnerHTML={{ __html: article.content }}
        />
      </article>
    </>
  )
}

export default Article
