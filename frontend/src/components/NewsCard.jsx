import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUpRight } from 'lucide-react'
import { getImageUrl } from '../lib/api'
import { articlePath } from '../lib/urls'

export default function NewsCard({ article, compact = false, priority = false, featured = false }) {
  const [failedImage, setFailedImage] = useState(null)
  const imageUrl = getImageUrl(article.image_url)
  const tags = Array.isArray(article.tags) ? article.tags : (article.tags || '').split(',').map(t => t.trim())
  const date = new Date(article.created_at)
  const formattedDate = Number.isNaN(date.getTime()) ? 'Latest story' : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  return (
    <Link to={articlePath(article)} className={`story-card${compact ? ' story-compact' : ''}${featured ? ' story-featured' : ''}`}>
      <div className={`story-image story-art-${Number(article.id) % 3}`}>
        {imageUrl && failedImage !== imageUrl ? <img src={imageUrl} alt="" loading={priority ? 'eager' : 'lazy'} fetchPriority={priority ? 'high' : 'auto'} decoding="async" width="800" height="500" onError={() => setFailedImage(imageUrl)} /> : <div className="story-placeholder" aria-hidden="true"><span /><span /><span /><b>cm.</b></div>}
        <span className="story-category">{tags[0] || 'Insights'}</span>
        <span className="story-arrow"><ArrowUpRight size={19} /></span>
      </div>
      <div className="story-copy">
        <div className="story-meta"><span>{featured ? 'THE BIG PICTURE' : 'THE CLOUDMIND EDIT'}</span><time dateTime={Number.isNaN(date.getTime()) ? undefined : date.toISOString()}>{formattedDate}</time></div>
        <h3>{article.title}</h3>
        {!compact && <p>{article.summary}</p>}
        <span className="story-read">Read the story <ArrowUpRight size={15} /></span>
      </div>
    </Link>
  )
}
