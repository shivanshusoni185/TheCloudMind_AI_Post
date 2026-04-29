import { Link } from 'react-router-dom'
import logo from '../assets/logo.png'

function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer style={{ marginTop: 64, background: '#1A1A17', color: '#e2e8f0' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '48px 28px 20px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr 1fr', gap: 40 }}>
          {/* Brand */}
          <div>
            <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
              <div style={{ background: '#FFFDF5', padding: 10, borderRadius: 16, flexShrink: 0 }}>
                <img src={logo} alt="TheCloudMind.ai" style={{ height: 44, width: 44, display: 'block' }} />
              </div>
              <div>
                <div style={{ color: '#fff', fontWeight: 700, fontSize: 20, fontFamily: 'var(--font-sans)' }}>
                  TheCloudMind.ai
                </div>
                <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.28em', color: '#64748b', marginTop: 2 }}>
                  ORIGINAL ANALYSIS
                </div>
              </div>
            </div>
            <p style={{ marginTop: 16, color: '#94a3b8', fontSize: 14, lineHeight: 1.7, maxWidth: 320 }}>
              Built to turn raw reporting into fast, readable AI coverage — better sourcing,
              cleaner visuals, and an editorial feel.
            </p>
          </div>

          {/* Navigate */}
          <div>
            <h4 style={{ margin: '0 0 14px', color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.22em' }}>
              NAVIGATE
            </h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, lineHeight: 2.2 }}>
              {[
                { to: '/', label: 'Home' },
                { to: '/latest-news', label: 'Latest News' },
                { to: '/about', label: 'About' },
                { to: '/contact', label: 'Contact' },
              ].map((link) => (
                <li key={link.to}>
                  <Link to={link.to} style={{ color: '#cbd5e1', fontSize: 14, textDecoration: 'none' }}>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Channels */}
          <div>
            <h4 style={{ margin: '0 0 14px', color: '#64748b', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.22em' }}>
              CHANNELS
            </h4>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, lineHeight: 2.2 }}>
              <li>
                <a href="https://www.youtube.com/@CloudMindAI" target="_blank" rel="noopener noreferrer"
                  style={{ color: '#cbd5e1', fontSize: 14, textDecoration: 'none' }}>
                  YouTube
                </a>
              </li>
              <li>
                <a href="https://www.instagram.com/thecloudmind.ai/" target="_blank" rel="noopener noreferrer"
                  style={{ color: '#cbd5e1', fontSize: 14, textDecoration: 'none' }}>
                  Instagram
                </a>
              </li>
              <li>
                <a href="mailto:contact@cloudmindai.in"
                  style={{ color: '#cbd5e1', fontSize: 14, textDecoration: 'none' }}>
                  contact@cloudmindai.in
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div style={{ borderTop: '1px solid rgba(255,255,255,.1)' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '16px 28px', display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: 13, flexWrap: 'wrap', gap: 8 }}>
          <span>&copy; {currentYear} TheCloudMind.ai. All rights reserved.</span>
          <span>AI-first newsroom with direct-source publishing.</span>
        </div>
      </div>
    </footer>
  )
}

export default Footer
