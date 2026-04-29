import { Link } from 'react-router-dom'
import { getImageUrl } from '../lib/api'

// Warm-palette placeholder for cards without a real photo
function SeedImage({ seed = 'tcm', aspect = '16/10', tag, showArrow = true }) {
  let h = 5381
  for (let i = 0; i < seed.length; i++) h = ((h << 5) + h) + seed.charCodeAt(i)

  const palettes = [
    ['#D9C9A8', '#B8A07A', '#7C6B4F'],
    ['#E2C8B0', '#C49B7E', '#8C5E3F'],
    ['#C9D2C2', '#9DAE93', '#5F7361'],
    ['#D4C7BD', '#A89684', '#6B5B4E'],
    ['#E5D7B3', '#C9B582', '#8A7644'],
    ['#D7BFB8', '#A88478', '#6B4A40'],
    ['#C8C0A8', '#9F9678', '#5C5640'],
    ['#D8C9B6', '#B89A7C', '#7A5A40'],
  ]
  const p = palettes[Math.abs(h) % palettes.length]
  const ring1 = 10 + (Math.abs(h >> 3) % 40)
  const ring2 = 30 + (Math.abs(h >> 6) % 40)
  const bg = `linear-gradient(135deg, ${p[0]} 0%, ${p[1]} 55%, ${p[2]} 100%)`

  return (
    <div style={{ position: 'relative', aspectRatio: aspect, overflow: 'hidden', background: bg }}>
      <div style={{ position: 'absolute', inset: 0, background: `radial-gradient(circle at ${ring1}% ${ring2}%, rgba(255,255,255,.28), transparent 50%)` }} />
      <div style={{ position: 'absolute', inset: 0, background: `radial-gradient(circle at ${100 - ring1}% ${100 - ring2}%, rgba(0,0,0,.14), transparent 55%)` }} />
      {tag && (
        <span style={{
          position: 'absolute', top: 14, left: 14,
          background: 'rgba(26,26,23,.78)', color: '#FFFDF5',
          padding: '4px 12px', borderRadius: 9999,
          fontSize: 11, fontWeight: 600, letterSpacing: '.22em', textTransform: 'uppercase',
          backdropFilter: 'blur(6px)',
        }}>{tag}</span>
      )}
      {showArrow && (
        <span style={{
          position: 'absolute', top: 14, right: 14,
          background: 'rgba(255,253,245,.92)', width: 34, height: 34, borderRadius: 9999,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 2px 6px rgba(74,60,25,.10)',
          color: '#4A4636',
        }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="m7 17 10-10M9 7h8v8"/>
          </svg>
        </span>
      )}
    </div>
  )
}

function NewsCard({ article, compact }) {
  const imageUrl = getImageUrl(article.image_url)
  const tags = Array.isArray(article.tags)
    ? article.tags
    : article.tags
    ? article.tags.split(',').map((t) => t.trim())
    : []
  const date = new Date(article.created_at).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  })

  if (compact) {
    return (
      <Link
        to={`/article/${article.slug}`}
        style={{
          display: 'flex', gap: 14, padding: 14,
          background: 'var(--cm-card)', border: '1px solid rgba(226,232,240,.7)',
          borderRadius: 22, boxShadow: '0 8px 30px rgba(74,60,25,.06)',
          textDecoration: 'none', transition: 'transform .3s, box-shadow .3s',
        }}
        onMouseEnter={e => {
          e.currentTarget.style.transform = 'translateY(-2px)'
          e.currentTarget.style.boxShadow = '0 14px 45px rgba(74,60,25,.12)'
        }}
        onMouseLeave={e => {
          e.currentTarget.style.transform = 'translateY(0)'
          e.currentTarget.style.boxShadow = '0 8px 30px rgba(74,60,25,.06)'
        }}
      >
        <div style={{ width: 76, height: 76, flexShrink: 0, borderRadius: 14, overflow: 'hidden' }}>
          {imageUrl
            ? <img src={imageUrl} alt={article.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            : <SeedImage seed={'tcm' + article.id} aspect="1/1" tag={null} showArrow={false} />
          }
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.2em', color: 'var(--fg5)', marginBottom: 5 }}>
            {date}
          </div>
          <h3 style={{
            margin: 0, fontSize: 14, fontWeight: 700, lineHeight: 1.3,
            color: 'var(--fg1)', letterSpacing: '-.005em',
            display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden',
          }}>{article.title}</h3>
          <p style={{
            margin: '4px 0 0', fontFamily: 'var(--font-serif)', fontSize: 13,
            lineHeight: 1.5, color: 'var(--fg4)',
            display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden',
          }}>{article.summary}</p>
        </div>
      </Link>
    )
  }

  return (
    <Link
      to={`/article/${article.slug}`}
      style={{
        display: 'block', overflow: 'hidden',
        background: 'var(--cm-card)', border: '1px solid rgba(226,232,240,.7)',
        borderRadius: 28, boxShadow: '0 22px 65px rgba(74,60,25,.07)',
        textDecoration: 'none', transition: 'transform .3s, box-shadow .3s',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.transform = 'translateY(-4px)'
        e.currentTarget.style.boxShadow = '0 28px 80px rgba(74,60,25,.14)'
      }}
      onMouseLeave={e => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = '0 22px 65px rgba(74,60,25,.07)'
      }}
    >
      {imageUrl
        ? <img src={imageUrl} alt={article.title} style={{ width: '100%', aspectRatio: '16/10', objectFit: 'cover' }} />
        : <SeedImage seed={'tcm' + article.id} aspect="16/10" tag={tags[0]} />
      }
      <div style={{ padding: 22 }}>
        <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.24em', color: 'var(--fg5)', marginBottom: 10 }}>
          {date}
          {tags[0] && (
            <span style={{ marginLeft: 10, fontSize: 10, background: '#f1f5f9', color: '#475569', padding: '2px 9px', borderRadius: 9999, fontWeight: 600, letterSpacing: 0, textTransform: 'none' }}>
              {tags[0]}
            </span>
          )}
        </div>
        <h3 style={{ margin: 0, fontSize: 19, fontWeight: 700, lineHeight: 1.2, letterSpacing: '-.01em', color: 'var(--fg1)' }}>
          {article.title}
        </h3>
        <p style={{
          margin: '10px 0 0', fontFamily: 'var(--font-serif)', fontSize: 15,
          lineHeight: 1.6, color: 'var(--fg4)',
          display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden',
        }}>
          {article.summary}
        </p>
      </div>
    </Link>
  )
}

export default NewsCard
