import { useState, useEffect } from 'react'
import { Helmet } from 'react-helmet-async'
import { Loader, Briefcase } from 'lucide-react'
import JobCard from '../components/JobCard'
import { jobsApi } from '../lib/api'

function Jobs() {
  const [jobs, setJobs] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [category, setCategory] = useState('')
  const [remoteOnly, setRemoteOnly] = useState(false)
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')

  useEffect(() => {
    jobsApi.getCategories()
      .then(res => setCategories(res.data))
      .catch(() => setCategories([]))
  }, [])

  useEffect(() => { fetchJobs() }, [search, category, remoteOnly])

  const fetchJobs = async () => {
    setLoading(true)
    try {
      const res = await jobsApi.getAll({
        search,
        category,
        remote: remoteOnly ? true : null,
      })
      setJobs(res.data)
    } catch {
      setJobs([])
    } finally {
      setLoading(false)
    }
  }

  const prettyCat = (c) => c.replace(/[-_]/g, ' ').replace(/\b\w/g, m => m.toUpperCase())

  return (
    <>
      <Helmet>
        <title>Tech Jobs — TheCloudMind.ai | Roles Across Companies</title>
        <meta name="description" content="Browse the latest tech, AI, data, design and product jobs from companies around the world. Updated daily on TheCloudMind.ai." />
        <meta name="keywords" content="tech jobs, AI jobs, remote jobs, software jobs, data jobs, careers" />
        <meta property="og:title" content="Tech Jobs — TheCloudMind.ai" />
        <meta property="og:description" content="Latest tech and AI jobs from companies around the world, updated daily." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://cloudmindai.in/jobs" />
        <link rel="canonical" href="https://cloudmindai.in/jobs" />
      </Helmet>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '36px 24px' }}>
        <div style={{ display: 'flex', gap: 14, alignItems: 'center', marginBottom: 22 }}>
          <div style={{ background: 'var(--teal-600)', color: '#fff', padding: 10, borderRadius: 16, boxShadow: '0 4px 12px rgba(13,148,136,.3)' }}>
            <Briefcase size={22} />
          </div>
          <div>
            <div className="eyebrow">CAREERS</div>
            <h1 style={{ margin: '2px 0 0', fontSize: 30, fontWeight: 700, letterSpacing: '-.01em', color: 'var(--fg1)' }}>Jobs Board</h1>
          </div>
        </div>

        {/* Filters */}
        <div className="glass-panel" style={{ padding: '18px 22px', borderRadius: 20, marginBottom: 28 }}>
          <div className="filter-bar-inner">
            <div style={{ minWidth: 0 }}>
              <div className="eyebrow" style={{ marginBottom: 8 }}>BROWSE BY CATEGORY</div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {[{ label: 'All', value: '' }, ...categories.map(c => ({ label: prettyCat(c), value: c }))].map(c => (
                  <button key={c.value} onClick={() => setCategory(c.value)} style={{
                    background: category === c.value ? 'var(--bg5)' : '#fff',
                    color: category === c.value ? '#fff' : 'var(--fg4)',
                    border: '1px solid ' + (category === c.value ? 'var(--bg5)' : '#e2e8f0'),
                    padding: '7px 16px', borderRadius: 9999,
                    fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit',
                  }}>{c.label}</button>
                ))}
              </div>
            </div>
            <form onSubmit={e => { e.preventDefault(); setSearch(searchInput) }} className="search-form">
              <div className="search-input-wrap">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                  style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#94a3b8', pointerEvents: 'none' }}>
                  <circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" />
                </svg>
                <input value={searchInput} onChange={e => setSearchInput(e.target.value)} placeholder="Search jobs..." className="search-input"
                  style={{ border: '1px solid #e2e8f0', background: '#fff', borderRadius: 14, padding: '10px 14px 10px 38px', fontFamily: 'inherit', fontSize: 13, outline: 'none' }} />
              </div>
              <button type="submit" style={{ padding: '10px 20px', background: 'var(--bg5)', color: '#fff', border: 'none', borderRadius: 14, fontSize: 14, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit' }}>Search</button>
            </form>
          </div>
          <label style={{ display: 'inline-flex', gap: 8, alignItems: 'center', marginTop: 14, fontSize: 13, color: 'var(--fg3)', cursor: 'pointer' }}>
            <input type="checkbox" checked={remoteOnly} onChange={e => setRemoteOnly(e.target.checked)} />
            Remote only
          </label>
        </div>

        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
            <Loader size={32} className="animate-spin" style={{ color: 'var(--cm-accent)' }} />
          </div>
        ) : jobs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '80px 0', background: 'var(--cm-card)', borderRadius: 28, border: '1px solid rgba(226,232,240,.7)' }}>
            <p style={{ color: 'var(--fg4)', fontSize: 18, fontWeight: 600 }}>No jobs found</p>
            <p style={{ color: 'var(--fg5)', fontSize: 14, marginTop: 6 }}>Try clearing filters or check back soon — the board refreshes daily.</p>
          </div>
        ) : (
          <>
            <div style={{ marginBottom: 16, fontSize: 14, color: 'var(--fg4)' }}>{jobs.length} open role{jobs.length !== 1 ? 's' : ''}</div>
            <div className="coverage-grid">
              {jobs.map(j => <JobCard key={j.id} job={j} />)}
            </div>
          </>
        )}
      </div>
    </>
  )
}

export default Jobs
