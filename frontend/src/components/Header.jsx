import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { LogOut, Settings, Menu, X } from 'lucide-react'
import logo from '../assets/logo.png'

const NAV_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/latest-news', label: 'Latest' },
  { to: '/about', label: 'About' },
  { to: '/contact', label: 'Contact' },
]

function Header() {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const token = localStorage.getItem('token')
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = () => {
    localStorage.removeItem('token')
    setMobileOpen(false)
    navigate('/')
  }

  const closeMobile = () => setMobileOpen(false)

  return (
    <header style={{
      position: 'sticky', top: 0, zIndex: 40,
      background: 'rgba(255,255,255,.80)',
      borderBottom: '1px solid rgba(255,255,255,.6)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
    }}>
      <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 24px' }}>

        {/* Logo */}
        <Link to="/" onClick={closeMobile} style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}>
          <img
            src={logo}
            alt="TheCloudMind.ai"
            style={{ height: 44, width: 44, borderRadius: '50%', objectFit: 'cover' }}
          />
          <span style={{
            fontSize: 17, fontWeight: 700, color: 'var(--fg1)',
            fontFamily: 'var(--font-sans)',
          }}
            className="hidden sm:block"
          >
            TheCloudMind.ai
          </span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex" style={{ gap: 26, alignItems: 'center', display: 'flex' }}>
          {NAV_LINKS.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              style={{
                fontSize: 14, fontWeight: 500,
                color: pathname === link.to ? 'var(--fg1)' : 'var(--fg3)',
                textDecoration: 'none',
                borderBottom: pathname === link.to ? '2px solid var(--cm-accent)' : '2px solid transparent',
                paddingBottom: 2,
                transition: 'color .15s',
              }}
            >
              {link.label}
            </Link>
          ))}
          <a
            href="https://www.youtube.com/@CloudMindAI"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: 'var(--fg5)', fontSize: 14, fontWeight: 500, textDecoration: 'none' }}
          >
            YouTube
          </a>
          <a
            href="https://www.instagram.com/thecloudmind.ai/"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: 'var(--fg5)', fontSize: 14, fontWeight: 500, textDecoration: 'none' }}
          >
            Instagram
          </a>
          {token && (
            <>
              <Link
                to="/admin"
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 6,
                  padding: '8px 16px', background: 'var(--bg5)', color: '#fff',
                  borderRadius: 'var(--radius-pill)', fontSize: 13, fontWeight: 600,
                  textDecoration: 'none',
                }}
              >
                <Settings size={14} /> Dashboard
              </Link>
              <button
                onClick={handleLogout}
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 6,
                  padding: '8px 16px', background: 'var(--danger-bg)',
                  color: 'var(--danger)', border: '1px solid var(--danger-border)',
                  borderRadius: 'var(--radius-pill)', fontSize: 13, fontWeight: 600,
                  cursor: 'pointer', fontFamily: 'inherit',
                }}
              >
                <LogOut size={14} /> Logout
              </button>
            </>
          )}
        </nav>

        {/* Mobile Hamburger */}
        <button
          type="button"
          onClick={() => setMobileOpen((prev) => !prev)}
          className="md:hidden"
          style={{
            padding: 8, borderRadius: 10,
            border: '1px solid var(--cm-border)',
            color: 'var(--fg3)', background: 'transparent', cursor: 'pointer',
          }}
          aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile Dropdown */}
      {mobileOpen && (
        <div
          className="md:hidden"
          style={{
            borderTop: '1px solid var(--cm-border)',
            background: 'rgba(255,253,245,.96)',
            backdropFilter: 'blur(20px)',
          }}
        >
          <div style={{ maxWidth: 1200, margin: '0 auto', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 4 }}>
            {NAV_LINKS.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                onClick={closeMobile}
                style={{
                  padding: '10px 12px', borderRadius: 10, fontSize: 14, fontWeight: 500,
                  color: pathname === link.to ? 'var(--cm-accent)' : 'var(--fg2)',
                  background: pathname === link.to ? 'rgba(15,118,110,.08)' : 'transparent',
                  textDecoration: 'none',
                }}
              >
                {link.label}
              </Link>
            ))}
            <div style={{ display: 'flex', gap: 16, padding: '8px 12px' }}>
              <a
                href="https://www.youtube.com/@CloudMindAI"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: 'var(--fg5)', fontSize: 14, textDecoration: 'none' }}
              >
                YouTube
              </a>
              <a
                href="https://www.instagram.com/thecloudmind.ai/"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: 'var(--fg5)', fontSize: 14, textDecoration: 'none' }}
              >
                Instagram
              </a>
            </div>
            {token && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, paddingTop: 8, borderTop: '1px solid var(--cm-border)', marginTop: 4 }}>
                <Link
                  to="/admin"
                  onClick={closeMobile}
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: 6,
                    padding: '10px 14px', background: 'var(--bg5)', color: '#fff',
                    borderRadius: 10, fontSize: 14, fontWeight: 600, textDecoration: 'none',
                  }}
                >
                  <Settings size={16} /> Admin Dashboard
                </Link>
                <button
                  onClick={handleLogout}
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: 6,
                    padding: '10px 14px', background: 'var(--danger-bg)',
                    color: 'var(--danger)', border: '1px solid var(--danger-border)',
                    borderRadius: 10, fontSize: 14, fontWeight: 600,
                    cursor: 'pointer', fontFamily: 'inherit',
                  }}
                >
                  <LogOut size={16} /> Logout
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  )
}

export default Header
