import { useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { Send, CheckCircle, AlertCircle } from 'lucide-react'
import axios from 'axios'

function ContactUs() {
  const [formData, setFormData] = useState({ name: '', email: '', subject: '', message: '' })
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')

  const handleChange = e => setFormData({ ...formData, [e.target.name]: e.target.value })

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
    } finally {
      setLoading(false)
    }
  }

  const inputStyle = {
    width: '100%', padding: '12px 16px',
    border: '1px solid #e2e8f0', borderRadius: 14,
    fontFamily: 'var(--font-sans)', fontSize: 14,
    color: 'var(--fg2)', background: '#fff', outline: 'none',
    boxSizing: 'border-box',
  }

  const labelStyle = {
    display: 'block', fontSize: 13, fontWeight: 600,
    color: 'var(--fg3)', marginBottom: 6,
  }

  return (
    <>
      <Helmet>
        <title>Contact Us - TheCloudMind.ai | Get in Touch</title>
        <meta name="description" content="Have questions about AI news or want to collaborate? Contact TheCloudMind.ai team." />
        <meta name="keywords" content="contact TheCloudMind.ai, AI news contact, get in touch, feedback" />
        <meta property="og:title" content="Contact Us - TheCloudMind.ai" />
        <meta property="og:description" content="Get in touch with TheCloudMind.ai team." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://cloudmindai.in/contact" />
        <meta name="twitter:card" content="summary_large_image" />
        <link rel="canonical" href="https://cloudmindai.in/contact" />
      </Helmet>

      <div style={{ maxWidth: 900, margin: '0 auto', padding: '48px 24px' }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div className="eyebrow" style={{ marginBottom: 8 }}>GET IN TOUCH</div>
          <h1 style={{ margin: 0, fontSize: 'clamp(28px, 4vw, 40px)', fontWeight: 700, letterSpacing: '-.015em', color: 'var(--fg1)' }}>
            Contact Us
          </h1>
          <p style={{ margin: '14px auto 0', maxWidth: 480, fontFamily: 'var(--font-serif)', fontSize: 17, lineHeight: 1.7, color: 'var(--fg4)' }}>
            Have questions? We would love to hear from you. Send us a message and we will respond as soon as possible.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 24 }} className="contact-grid">
          {/* Info */}
          <div style={{ background: 'var(--bg5)', borderRadius: 28, padding: 28, color: '#fff' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 18, fontWeight: 700, color: '#fff' }}>Why Contact Us?</h3>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {['Get expert insights on AI news', 'Suggest topics for coverage', 'Report issues or feedback', 'Collaboration inquiries'].map(item => (
                <li key={item} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', marginBottom: 14, fontSize: 14, color: '#94a3b8' }}>
                  <CheckCircle size={16} style={{ color: 'var(--teal-600)', flexShrink: 0, marginTop: 1 }} />
                  {item}
                </li>
              ))}
            </ul>
            <div style={{ marginTop: 28, paddingTop: 20, borderTop: '1px solid rgba(255,255,255,.1)' }}>
              <div className="eyebrow" style={{ marginBottom: 8 }}>EMAIL</div>
              <a href="mailto:contact@cloudmindai.in" style={{ color: '#cbd5e1', fontSize: 14, textDecoration: 'none' }}>
                contact@cloudmindai.in
              </a>
            </div>
          </div>

          {/* Form */}
          <div style={{ background: 'var(--cm-card)', border: '1px solid #e2e8f0', borderRadius: 28, padding: 32, boxShadow: 'var(--shadow-card)' }}>
            <h2 style={{ margin: '0 0 24px', fontSize: 22, fontWeight: 700, color: 'var(--fg1)' }}>Send us a Message</h2>

            {success && (
              <div style={{ marginBottom: 20, padding: '12px 16px', background: 'var(--teal-50)', border: '1px solid #99f6e4', borderRadius: 14, display: 'flex', alignItems: 'center', gap: 10, color: 'var(--teal-ink)', fontSize: 14 }}>
                <CheckCircle size={18} /> Thank you! We will get back to you soon.
              </div>
            )}
            {error && (
              <div style={{ marginBottom: 20, padding: '12px 16px', background: 'var(--danger-bg)', border: '1px solid var(--danger-border)', borderRadius: 14, display: 'flex', alignItems: 'center', gap: 10, color: 'var(--danger)', fontSize: 14 }}>
                <AlertCircle size={18} /> {error}
              </div>
            )}

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <label style={labelStyle}>Your Name *</label>
                  <input type="text" name="name" value={formData.name} onChange={handleChange} required style={inputStyle} placeholder="John Doe" />
                </div>
                <div>
                  <label style={labelStyle}>Your Email *</label>
                  <input type="email" name="email" value={formData.email} onChange={handleChange} required style={inputStyle} placeholder="john@example.com" />
                </div>
              </div>
              <div>
                <label style={labelStyle}>Subject *</label>
                <input type="text" name="subject" value={formData.subject} onChange={handleChange} required style={inputStyle} placeholder="How can we help you?" />
              </div>
              <div>
                <label style={labelStyle}>Message *</label>
                <textarea name="message" value={formData.message} onChange={handleChange} required rows="5"
                  style={{ ...inputStyle, resize: 'none' }}
                  placeholder="Tell us more about your inquiry..." />
              </div>
              <button type="submit" disabled={loading} style={{
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                padding: '14px 24px', background: 'var(--bg5)', color: '#fff',
                border: 'none', borderRadius: 14, fontSize: 15, fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer', fontFamily: 'inherit',
                opacity: loading ? 0.6 : 1,
              }}>
                {loading
                  ? <><div style={{ width: 18, height: 18, border: '2px solid rgba(255,255,255,.4)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />Sending...</>
                  : <><Send size={16} />Send Message</>
                }
              </button>
            </form>
          </div>
        </div>
      </div>
    </>
  )
}

export default ContactUs
