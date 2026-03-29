import { Link } from 'react-router-dom'
import { ArrowUpRight, Calendar } from 'lucide-react'
import { getImageUrl } from '../lib/api'

function NewsCard({ article, compact = false }) {
  const imageUrl = getImageUrl(article.image_url)
  const tags = Array.isArray(article.tags)
    ? article.tags
    : article.tags
    ? article.tags.split(',').map((t) => t.trim())
    : []

  const date = new Date(article.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })

  /* ── Compact / sidebar variant ─────────────────────────────── */
  if (compact) {
    return (
      <Link
        to={`/article/${article.slug}`}
        className="group flex gap-4 overflow-hidden rounded-[22px] border border-slate-200/70 bg-white/90 p-4 shadow-[0_8px_30px_rgba(15,23,42,0.06)] transition duration-300 hover:-translate-y-0.5 hover:shadow-[0_14px_45px_rgba(15,23,42,0.10)]"
      >
        {/* Thumbnail */}
        <div className="relative aspect-square w-20 shrink-0 overflow-hidden rounded-[14px] bg-slate-100">
          {imageUrl ? (
            <img
              src={imageUrl}
              alt={article.title}
              className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-teal-100 via-white to-blue-100 text-[9px] font-semibold uppercase tracking-widest text-slate-400">
              TCM
            </div>
          )}
          {tags[0] && (
            <span className="absolute bottom-1.5 left-1.5 rounded-full bg-slate-950/80 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-white backdrop-blur">
              {tags[0]}
            </span>
          )}
        </div>

        {/* Text */}
        <div className="min-w-0 flex-1 space-y-1.5">
          <p className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.2em] text-slate-400">
            <Calendar className="h-3 w-3" />
            {date}
          </p>
          <h3 className="line-clamp-2 text-[15px] font-bold leading-snug tracking-tight text-slate-950 transition group-hover:text-teal-700">
            {article.title}
          </h3>
          <p className="line-clamp-2 font-editorial text-[13px] leading-5 text-slate-500">
            {article.summary}
          </p>
        </div>

        {/* Arrow */}
        <ArrowUpRight className="h-4 w-4 shrink-0 text-slate-400 transition group-hover:text-teal-600" />
      </Link>
    )
  }

  /* ── Standard card ──────────────────────────────────────────── */
  return (
    <Link
      to={`/article/${article.slug}`}
      className="group block overflow-hidden rounded-[28px] border border-slate-200/70 bg-white/90 shadow-[0_22px_65px_rgba(15,23,42,0.07)] transition duration-300 hover:-translate-y-1 hover:shadow-[0_28px_80px_rgba(15,23,42,0.12)]"
    >
      {/* Image */}
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
        {/* Overlay badges */}
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

      {/* Body */}
      <div className="space-y-3 p-5 sm:p-6">
        <p className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.24em] text-slate-400">
          <Calendar className="h-3.5 w-3.5" />
          {date}
          {tags[1] && (
            <span className="ml-1 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
              {tags[1]}
            </span>
          )}
        </p>
        <div>
          <h3 className="line-clamp-2 text-xl font-bold leading-tight tracking-tight text-slate-950 transition group-hover:text-teal-700">
            {article.title}
          </h3>
          <p className="mt-2.5 line-clamp-3 font-editorial text-[16px] leading-7 text-slate-600">
            {article.summary}
          </p>
        </div>
      </div>
    </Link>
  )
}

export default NewsCard
