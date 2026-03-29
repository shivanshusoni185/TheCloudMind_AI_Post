import { useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { Send, CheckCircle, AlertCircle, Mail, MessageSquare, Lightbulb, Flag } from 'lucide-react'
import axios from 'axios'

const ICON_CLASS = 'h-4 w-4 text-teal-600'
const REASONS = [
  { node: <MessageSquare className={ICON_CLASS} />, text: 'Ask questions about AI news' },
  { node: <Lightbulb className={ICON_CLASS} />, text: 'Suggest topics for coverage' },
  { node: <Flag className={ICON_CLASS} />, text: 'Report issues or give feedback' },
]

function ContactUs() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
  })
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setSuccess(false)
    try {
      await axios.post('/api/contact/', formData)
      setSuccess(true)
      setFormData({ name: '', email: '', subject: '', message: '' })
      setTimeout(() => setSuccess(false), 5000)
    } catch (err) {
      setError('Failed to send message. Please try again later.')
      console.error('Contact form error:', err)
    } finally {
      setLoading(false)
    }
  }

  const inputClass =
    'w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-100'
  const labelClass = 'mb-2 block text-sm font-medium text-slate-700'

  return (
    <>
      <Helmet>
        <title>Contact — TheCloudMind.ai</title>
        <meta
          name="description"
          content="Get in touch with TheCloudMind.ai — ask questions, suggest topics, or report issues."
        />
        <meta name="keywords" content="contact TheCloudMind.ai, AI news feedback, get in touch" />
        <meta property="og:title" content="Contact — TheCloudMind.ai" />
        <meta
          property="og:description"
          content="Get in touch with the TheCloudMind.ai team."
        />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://cloudmindai.in/contact" />
        <meta name="twitter:card" content="summary_large_image" />
        <link rel="canonical" href="https://cloudmindai.in/contact" />
      </Helmet>

      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 sm:py-14">

        {/* Page header */}
        <div className="mb-10 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
            Get in touch
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
            Contact Us
          </h1>
          <p className="font-editorial mx-auto mt-3 max-w-xl text-lg leading-8 text-slate-600">
            Have questions? We would love to hear from you. Send us a message and we will respond
            as soon as possible.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_2fr]">

          {/* Info panel */}
          <div className="space-y-5">
            {/* Why contact */}
            <div className="rounded-[28px] border border-slate-200 bg-white/90 p-6 shadow-[0_18px_55px_rgba(15,23,42,0.05)]">
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
                Why contact us
              </p>
              <div className="mt-4 space-y-4">
                {REASONS.map(({ node, text }) => (
                  <div key={text} className="flex items-start gap-3">
                    <div className="rounded-xl bg-teal-50 p-2">{node}</div>
                    <p className="text-sm leading-6 text-slate-600">{text}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Email */}
            <div className="rounded-[28px] border border-slate-200 bg-white/90 p-6 shadow-[0_18px_55px_rgba(15,23,42,0.05)]">
              <div className="flex items-center gap-3">
                <div className="rounded-xl bg-slate-100 p-2">
                  <Mail className="h-4 w-4 text-slate-600" />
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                    Email
                  </p>
                  <a
                    href="mailto:contact@cloudmindai.in"
                    className="text-sm font-medium text-slate-900 transition hover:text-teal-700"
                  >
                    contact@cloudmindai.in
                  </a>
                </div>
              </div>
            </div>
          </div>

          {/* Form */}
          <div className="rounded-[32px] border border-slate-200 bg-white/90 p-6 shadow-[0_22px_65px_rgba(15,23,42,0.06)] sm:p-8">
            <h2 className="mb-6 text-xl font-bold tracking-tight text-slate-950">
              Send us a message
            </h2>

            {success && (
              <div className="mb-6 flex items-center gap-3 rounded-[18px] border border-teal-200 bg-teal-50 p-4 text-sm font-medium text-teal-800">
                <CheckCircle className="h-5 w-5 shrink-0 text-teal-600" />
                Thank you! We will get back to you soon.
              </div>
            )}

            {error && (
              <div className="mb-6 flex items-center gap-3 rounded-[18px] border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-800">
                <AlertCircle className="h-5 w-5 shrink-0 text-red-500" />
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                <div>
                  <label className={labelClass}>Your Name *</label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    placeholder="John Doe"
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className={labelClass}>Your Email *</label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    placeholder="john@example.com"
                    className={inputClass}
                  />
                </div>
              </div>

              <div>
                <label className={labelClass}>Subject *</label>
                <input
                  type="text"
                  name="subject"
                  value={formData.subject}
                  onChange={handleChange}
                  required
                  placeholder="How can we help you?"
                  className={inputClass}
                />
              </div>

              <div>
                <label className={labelClass}>Message *</label>
                <textarea
                  name="message"
                  value={formData.message}
                  onChange={handleChange}
                  required
                  rows={6}
                  placeholder="Tell us more about your inquiry…"
                  className={`${inputClass} resize-none`}
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-slate-950 py-3.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Sending…
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                    Send Message
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </>
  )
}

export default ContactUs
