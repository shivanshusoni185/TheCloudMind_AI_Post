import { Link } from 'react-router-dom'
import { ArrowUpRight, Calendar, Tag } from 'lucide-react'
import { getImageUrl } from '../lib/api'

function NewsCard({ article }) {
  const imageUrl = getImageUrl(article.image_url)
  const tags = Array.isArray(article.tags)
    ? article.tags
    : (article.tags ? article.tags.split(',').map(t => t.trim()) : [])

  const date = new Date(article.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })

  return (
    <Link
      to={`/article/${article.slug}`}
      className="group block overflow-hidden rounded-[28px] border border-slate-200/70 bg-white/90 shadow-[0_22px_65px_rgba(15,23,42,0.07)] transition duration-300 hover:-translate-y-1 hover:shadow-[0_28px_80px_rgba(15,23,42,0.12)]"
    >
      <div className="relative aspect-[16/10] overflow-hidden bg-slate-100">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={article.title}
            className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-teal-100 via-white to-blue-100 text-sm font-medium uppercase tracking-[0.3em] text-slate-500">
            TheCloudMind
          </div>
        )}
        <div className="absolute inset-x-0 top-0 flex items-start justify-between p-4">
          {tags[0] && (
            <span className="rounded-full bg-slate-950/85 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-white backdrop-blur">
              {tags[0]}
            </span>
          )}
          <span className="rounded-full bg-white/88 p-2 text-slate-700 shadow-sm backdrop-blur">
            <ArrowUpRight className="h-4 w-4" />
          </span>
        </div>
      </div>

      <div className="space-y-4 p-5 sm:p-6">
        <div className="flex items-center gap-3 text-xs font-medium uppercase tracking-[0.24em] text-slate-400">
          <span className="inline-flex items-center gap-2">
            <Calendar className="h-3.5 w-3.5" />
            {date}
          </span>
          {tags[1] && (
            <span className="inline-flex items-center gap-2">
              <Tag className="h-3.5 w-3.5" />
              {tags[1]}
            </span>
          )}
        </div>

        <div>
          <h3 className="line-clamp-2 text-xl font-bold leading-tight tracking-tight text-slate-950 transition group-hover:text-teal-700">
            {article.title}
          </h3>
          <p className="mt-3 line-clamp-3 font-editorial text-[17px] leading-7 text-slate-600">
            {article.summary}
          </p>
        </div>
      </div>
    </Link>
  )
}

export default NewsCard
