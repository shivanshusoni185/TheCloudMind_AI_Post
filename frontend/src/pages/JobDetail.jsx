import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { ArrowLeft, MapPin, Briefcase, Wifi, ExternalLink, Loader } from 'lucide-react'
import { jobsApi } from '../lib/api'
import { renderArticleContent } from '../lib/content'

function JobDetail() {
  const { slug } = useParams()
  const [job, setJob] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    jobsApi.getBySlug(slug)
      .then(res => setJob(res.data))
      .catch(() => setError('Job not found'))
      .finally(() => setLoading(false))
  }, [slug])

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
        <Loader size={32} className="animate-spin" style={{ color: 'var(--cm-accent)' }} />
      </div>
    )
  }

  if (error || !job) {
    return (
      <div style={{ maxWidth: 820, margin: '0 auto', padding: '32px 24px' }}>
        <Link to="/jobs" style={{ display: 'inline-flex', gap: 8, alignItems: 'center', fontSize: 14, fontWeight: 500, color: 'var(--fg3)', textDecoration: 'none' }}>
          <ArrowLeft size={16} /> Back to Jobs
        </Link>
        <div style={{ textAlign: 'center', padding: '80px 0' }}>
          <p style={{ color: 'var(--fg4)', fontSize: 18 }}>{error || 'Job not found'}</p>
        </div>
      </div>
    )
  }

  const tags = Array.isArray(job.tags) ? job.tags : []
  const posted = job.posted_at || job.created_at
  const dateStr = posted ? new Date(posted).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : ''
  const jobUrl = `https://cloudmindai.in/jobs/${job.slug}`

  // Google Jobs (JobPosting) structured data for SEO.
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'JobPosting',
    title: job.title,
    description: job.description || `${job.title} at ${job.company}`,
    datePosted: posted,
    employmentType: job.job_type || undefined,
    hiringOrganization: {
      '@type': 'Organization',
      name: job.company,
      logo: job.company_logo || undefined,
    },
    jobLocationType: job.remote ? 'TELECOMMUTE' : undefined,
    applicantLocationRequirements: job.remote && job.location
      ? { '@type': 'Country', name: job.location } : undefined,
    jobLocation: !job.remote && job.location
      ? { '@type': 'Place', address: { '@type': 'PostalAddress', addressLocality: job.location } } : undefined,
    directApply: false,
    url: jobUrl,
  }

  const ApplyButton = ({ block }) => (
    <a href={job.apply_url} target="_blank" rel="noopener noreferrer"
      style={{
        display: 'inline-flex', gap: 8, alignItems: 'center', justifyContent: 'center',
        padding: '13px 26px', background: 'var(--bg5)', color: '#fff',
        borderRadius: 14, fontSize: 15, fontWeight: 600, textDecoration: 'none',
        width: block ? '100%' : 'auto',
      }}>
      Apply on company site <ExternalLink size={16} />
    </a>
  )

  return (
    <>
      <Helmet>
        <title>{job.title} at {job.company} — TheCloudMind.ai Jobs</title>
        <meta name="description" content={`${job.title} at ${job.company}${job.location ? ' · ' + job.location : ''}. Apply now via TheCloudMind.ai jobs board.`} />
        <link rel="canonical" href={jobUrl} />
        <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>
      </Helmet>

      <div style={{ maxWidth: 820, margin: '0 auto', padding: '32px 24px' }}>
        <Link to="/jobs" style={{ display: 'inline-flex', gap: 8, alignItems: 'center', fontSize: 14, fontWeight: 500, color: 'var(--fg3)', textDecoration: 'none', marginBottom: 22 }}>
          <ArrowLeft size={16} /> Back to Jobs
        </Link>

        <header style={{ background: 'var(--cm-card)', border: '1px solid #e2e8f0', borderRadius: 28, padding: 'clamp(20px, 4.5vw, 32px)', boxShadow: 'var(--shadow-card)' }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start', flexWrap: 'wrap' }}>
            {job.company_logo && (
              <img src={job.company_logo} alt={job.company}
                style={{ width: 60, height: 60, borderRadius: 16, objectFit: 'contain', background: '#fff', border: '1px solid #e2e8f0' }}
                onError={e => { e.currentTarget.style.display = 'none' }} />
            )}
            <div style={{ flex: 1, minWidth: 200 }}>
              <h1 style={{ margin: 0, fontSize: 'clamp(22px, 3.5vw, 32px)', fontWeight: 700, lineHeight: 1.15, letterSpacing: '-.01em', color: 'var(--fg1)' }}>
                {job.title}
              </h1>
              <div style={{ marginTop: 6, fontSize: 16, fontWeight: 600, color: 'var(--fg3)' }}>{job.company}</div>
            </div>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 16 }}>
            {job.remote && <span style={pill('teal')}><Wifi size={13} /> Remote</span>}
            {job.location && <span style={pill()}><MapPin size={13} /> {job.location}</span>}
            {job.job_type && <span style={pill()}><Briefcase size={13} /> {job.job_type}</span>}
            {job.category && <span style={pill()}>{job.category.replace(/[-_]/g, ' ')}</span>}
            {job.salary && <span style={pill()}>{job.salary}</span>}
          </div>

          {dateStr && <div style={{ marginTop: 14, fontSize: 13, color: 'var(--fg5)' }}>Posted {dateStr}</div>}

          <div style={{ marginTop: 20 }}><ApplyButton /></div>
        </header>

        {job.description && (
          <div className="article-body"
            style={{ marginTop: 20, background: 'var(--cm-card)', border: '1px solid #e2e8f0', borderRadius: 28, padding: 'clamp(18px, 4vw, 28px) clamp(18px, 4.5vw, 32px)', boxShadow: 'var(--shadow-rest)' }}
            dangerouslySetInnerHTML={{ __html: renderArticleContent(job.description) }} />
        )}

        <div style={{ marginTop: 20, background: 'var(--cm-card)', border: '1px solid #e2e8f0', borderRadius: 20, padding: 'clamp(18px, 4vw, 24px)', boxShadow: 'var(--shadow-subtle)', textAlign: 'center' }}>
          <p style={{ margin: '0 0 14px', color: 'var(--fg4)', fontSize: 14 }}>Interested in this role at {job.company}?</p>
          <ApplyButton block />
        </div>
        {tags.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 18 }}>
            {tags.map(t => (
              <span key={t} style={{ fontSize: 12, color: 'var(--fg4)', background: 'var(--cm-section)', padding: '4px 12px', borderRadius: 9999 }}>{t}</span>
            ))}
          </div>
        )}
      </div>
    </>
  )
}

function pill(tone) {
  const tones = { teal: { bg: 'var(--teal-50)', color: 'var(--teal-ink)' } }
  const t = tones[tone] || { bg: '#f1f5f9', color: '#475569' }
  return {
    display: 'inline-flex', alignItems: 'center', gap: 6,
    background: t.bg, color: t.color, padding: '5px 13px', borderRadius: 9999,
    fontSize: 12, fontWeight: 600,
  }
}

export default JobDetail
