import { useState, useEffect, useCallback } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Loader, Trash2, Plus, X, Download, Star, ArrowLeft, ExternalLink } from 'lucide-react'
import { adminApi } from '../lib/api'
import { safeExternalUrl } from '../lib/urls'

const EMPTY = {
  title: '', company: '', location: '', remote: true,
  job_type: 'Full-time', category: '', tags: '', salary: '',
  apply_url: '', company_logo: '', description: '', published: true, pinned: false,
}

function AdminJobs() {
  const navigate = useNavigate()
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [fetching, setFetching] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState(EMPTY)

  const load = useCallback(async () => {
    try {
      const res = await adminApi.getAllJobs()
      setJobs(res.data)
    } catch (err) {
      if (err.response?.status === 401) {
        localStorage.removeItem('token')
        navigate('/admin/login')
      }
    } finally {
      setLoading(false)
    }
  }, [navigate])

  useEffect(() => {
    if (!localStorage.getItem('token')) { navigate('/admin/login'); return }
    load()
  }, [load, navigate])

  const handleFetch = async () => {
    setFetching(true)
    try {
      const res = await adminApi.fetchJobs()
      const s = res.data?.updated || {}
      alert(`Jobs fetched. Created: ${s.created || 0}, Updated: ${s.updated || 0}, Fetched: ${s.fetched || 0}`)
      load()
    } catch (err) {
      alert('Error fetching jobs: ' + (err.response?.data?.detail || err.message))
    } finally {
      setFetching(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this job?')) return
    try { await adminApi.deleteJob(id); load() } catch { alert('Error deleting job') }
  }

  const togglePin = async (job) => {
    try { await adminApi.updateJob(job.id, { pinned: !job.pinned }); load() } catch { alert('Error updating job') }
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setForm(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }))
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setCreating(true)
    try {
      const payload = {
        ...form,
        tags: form.tags ? form.tags.split(',').map(t => t.trim()).filter(Boolean) : [],
      }
      await adminApi.createJob(payload)
      setShowModal(false)
      setForm(EMPTY)
      load()
    } catch (err) {
      alert('Error creating job: ' + (err.response?.data?.detail || err.message))
    } finally {
      setCreating(false)
    }
  }

  if (loading) {
    return <div className="flex justify-center items-center py-20"><Loader className="w-8 h-8 animate-spin text-blue-600" /></div>
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="bg-white rounded-xl shadow-md p-6 mb-8">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <Link to="/admin" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800 mb-1">
              <ArrowLeft className="w-4 h-4" /> Back to Dashboard
            </Link>
            <h1 className="text-2xl font-bold text-gray-900">Manage Jobs</h1>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <button onClick={() => setShowModal(true)} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
              <Plus className="w-5 h-5" /> Add Job
            </button>
            <button onClick={handleFetch} disabled={fetching} className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition disabled:opacity-50">
              {fetching ? <Loader className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5" />} Fetch from API
            </button>
          </div>
        </div>
      </div>

      <div className="mb-4 text-sm text-gray-600">Total: <span className="font-semibold">{jobs.length}</span> job{jobs.length !== 1 ? 's' : ''}</div>

      {jobs.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-xl shadow">
          <p className="text-gray-500 text-xl">No jobs yet</p>
          <p className="text-gray-400 text-sm mt-2">Add one manually or click “Fetch from API”.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow overflow-x-auto">
          <table className="w-full min-w-[720px]">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-5 py-3 text-left text-sm font-medium text-gray-500">Title</th>
                <th className="px-5 py-3 text-left text-sm font-medium text-gray-500">Company</th>
                <th className="px-5 py-3 text-left text-sm font-medium text-gray-500">Category</th>
                <th className="px-5 py-3 text-left text-sm font-medium text-gray-500">Source</th>
                <th className="px-5 py-3 text-right text-sm font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {jobs.map(job => (
                <tr key={job.id} className="hover:bg-gray-50">
                  <td className="px-5 py-4">
                    <span className="font-medium text-gray-900">{job.title}</span>
                    {job.pinned && <span className="ml-2 text-xs text-amber-600 font-semibold">★ Featured</span>}
                  </td>
                  <td className="px-5 py-4 text-gray-700">{job.company}</td>
                  <td className="px-5 py-4 text-gray-500 text-sm">{job.category || '—'}</td>
                  <td className="px-5 py-4 text-gray-500 text-sm">{job.source || 'manual'}</td>
                  <td className="px-5 py-4 text-right whitespace-nowrap">
                    <a href={safeExternalUrl(job.apply_url)} target="_blank" rel="noopener noreferrer" className="inline-block p-2 text-gray-500 hover:bg-gray-100 rounded-lg" title="Open apply link">
                      <ExternalLink className="w-5 h-5" />
                    </a>
                    <button onClick={() => togglePin(job)} className={`p-2 rounded-lg ${job.pinned ? 'text-amber-500 hover:bg-amber-50' : 'text-gray-400 hover:bg-gray-100'}`} title="Toggle featured">
                      <Star className="w-5 h-5" fill={job.pinned ? 'currentColor' : 'none'} />
                    </button>
                    <button onClick={() => handleDelete(job.id)} className="p-2 text-red-600 hover:bg-red-50 rounded-lg" title="Delete">
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">Add Job</h2>
              <button onClick={() => setShowModal(false)} className="p-2 hover:bg-gray-100 rounded-lg"><X className="w-6 h-6" /></button>
            </div>
            <form onSubmit={handleCreate} className="p-6 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="Title *"><input name="title" required value={form.title} onChange={handleChange} className={inputCls} placeholder="Senior Software Engineer" /></Field>
                <Field label="Company *"><input name="company" required value={form.company} onChange={handleChange} className={inputCls} placeholder="Acme Corp" /></Field>
                <Field label="Location"><input name="location" value={form.location} onChange={handleChange} className={inputCls} placeholder="Bangalore, India / Remote" /></Field>
                <Field label="Job type"><input name="job_type" value={form.job_type} onChange={handleChange} className={inputCls} placeholder="Full-time" /></Field>
                <Field label="Category"><input name="category" value={form.category} onChange={handleChange} className={inputCls} placeholder="software-dev" /></Field>
                <Field label="Salary"><input name="salary" value={form.salary} onChange={handleChange} className={inputCls} placeholder="₹20–35 LPA (optional)" /></Field>
              </div>
              <Field label="Apply URL *"><input name="apply_url" required type="url" value={form.apply_url} onChange={handleChange} className={inputCls} placeholder="https://careers.company.com/job/123" /></Field>
              <Field label="Company logo URL"><input name="company_logo" value={form.company_logo} onChange={handleChange} className={inputCls} placeholder="https://logo.clearbit.com/company.com (optional)" /></Field>
              <Field label="Tags (comma-separated)"><input name="tags" value={form.tags} onChange={handleChange} className={inputCls} placeholder="Python, React, AWS" /></Field>
              <Field label="Description"><textarea name="description" rows="5" value={form.description} onChange={handleChange} className={inputCls} placeholder="Role summary, responsibilities, requirements…" /></Field>
              <div className="flex items-center gap-6">
                <label className="inline-flex items-center gap-2 text-sm text-gray-700"><input type="checkbox" name="remote" checked={form.remote} onChange={handleChange} /> Remote</label>
                <label className="inline-flex items-center gap-2 text-sm text-gray-700"><input type="checkbox" name="pinned" checked={form.pinned} onChange={handleChange} /> Featured</label>
                <label className="inline-flex items-center gap-2 text-sm text-gray-700"><input type="checkbox" name="published" checked={form.published} onChange={handleChange} /> Published</label>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="submit" disabled={creating} className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 flex items-center justify-center gap-2">
                  {creating ? <><Loader className="w-5 h-5 animate-spin" /> Saving…</> : <><Plus className="w-5 h-5" /> Add Job</>}
                </button>
                <button type="button" onClick={() => setShowModal(false)} className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition">Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

const inputCls = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
function Field({ label, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      {children}
    </div>
  )
}

export default AdminJobs
