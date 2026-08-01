import { useState } from 'react'
import { Link } from 'react-router-dom'
import { MapPin, Briefcase, Wifi } from 'lucide-react'
import { jobPath } from '../lib/urls'

// Warm-palette initial avatar for companies without a usable logo.
function CompanyMark({ company }) {
  const letter = (company || '?').trim().charAt(0).toUpperCase()
  let h = 5381
  for (let i = 0; i < company.length; i++) h = ((h << 5) + h) + company.charCodeAt(i)
  const palettes = ['#B8A07A', '#C49B7E', '#9DAE93', '#A89684', '#C9B582', '#A88478', '#9F9678', '#B89A7C']
  const bg = palettes[Math.abs(h) % palettes.length]
  return (
    <div style={{
      width: 52, height: 52, flexShrink: 0, borderRadius: 14, background: bg,
      color: '#FFFDF5', display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: 22, fontWeight: 700, fontFamily: 'var(--font-sans)',
    }}>{letter}</div>
  )
}

function Badge({ children, tone = 'default' }) {
  const tones = {
    default: { bg: '#f1f5f9', color: '#475569' },
    teal: { bg: 'var(--teal-50)', color: 'var(--teal-ink)' },
  }
  const t = tones[tone] || tones.default
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      background: t.bg, color: t.color, padding: '3px 10px', borderRadius: 9999,
      fontSize: 11, fontWeight: 600,
    }}>{children}</span>
  )
}

function JobCard({ job }) {
  const [logoOk, setLogoOk] = useState(true)
  const tags = Array.isArray(job.tags) ? job.tags : []
  const posted = job.posted_at || job.created_at
  const date = posted
    ? new Date(posted).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
    : ''

  return (
    <Link
      to={jobPath(job)}
      style={{
        display: 'block', background: 'var(--cm-card)',
        border: '1px solid rgba(226,232,240,.7)', borderRadius: 22,
        boxShadow: '0 10px 34px rgba(74,60,25,.06)', padding: 20,
        textDecoration: 'none', transition: 'transform .25s, box-shadow .25s',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.transform = 'translateY(-3px)'
        e.currentTarget.style.boxShadow = '0 20px 55px rgba(74,60,25,.12)'
      }}
      onMouseLeave={e => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = '0 10px 34px rgba(74,60,25,.06)'
      }}
    >
      <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
        {job.company_logo && logoOk
          ? <img src={job.company_logo} alt={job.company} loading="lazy"
              style={{ width: 52, height: 52, flexShrink: 0, borderRadius: 14, objectFit: 'contain', background: '#fff', border: '1px solid rgba(226,232,240,.7)' }}
              onError={() => setLogoOk(false)} />
          : <CompanyMark company={job.company} />
        }
        <div style={{ flex: 1, minWidth: 0 }}>
          {job.pinned && (
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '.14em', textTransform: 'uppercase', color: 'var(--cm-accent)', marginBottom: 4 }}>
              Featured
            </div>
          )}
          <h3 style={{
            margin: 0, fontSize: 16, fontWeight: 700, lineHeight: 1.3, color: 'var(--fg1)',
            display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden',
          }}>{job.title}</h3>
          <div style={{ marginTop: 3, fontSize: 14, fontWeight: 600, color: 'var(--fg3)' }}>
            {job.company}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 14 }}>
        {job.remote && <Badge tone="teal"><Wifi size={12} /> Remote</Badge>}
        {job.location && <Badge><MapPin size={12} /> {job.location}</Badge>}
        {job.job_type && <Badge><Briefcase size={12} /> {job.job_type}</Badge>}
        {job.category && <Badge>{job.category.replace(/[-_]/g, ' ')}</Badge>}
      </div>

      {tags.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 12 }}>
          {tags.slice(0, 4).map(t => (
            <span key={t} style={{ fontSize: 11, color: 'var(--fg4)', background: 'var(--cm-section)', padding: '2px 9px', borderRadius: 9999 }}>{t}</span>
          ))}
        </div>
      )}

      <div style={{ marginTop: 14, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 12, color: 'var(--fg5)' }}>{date}</span>
        {job.salary && <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--fg3)' }}>{job.salary}</span>}
      </div>
    </Link>
  )
}

export default JobCard
