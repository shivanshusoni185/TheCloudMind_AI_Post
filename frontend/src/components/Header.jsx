import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LogOut, Settings, Menu, X } from 'lucide-react'
import logo from '../assets/logo.jpg'

const NAV_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/latest-news', label: 'Latest' },
  { to: '/about', label: 'About' },
  { to: '/contact', label: 'Contact' },
]

function Header() {
  const navigate = useNavigate()
  const token = localStorage.getItem('token')
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = () => {
    localStorage.removeItem('token')
    setMobileOpen(false)
    navigate('/')
  }

  const closeMobile = () => setMobileOpen(false)

  return (
    <header className="sticky top-0 z-40 border-b border-white/60 bg-white/75 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3" onClick={closeMobile}>
          <img
            src={logo}
            alt="TheCloudMind.ai"
            className="h-12 w-12 rounded-2xl object-cover shadow-lg ring-2 ring-white"
          />
          <div>
            <div className="text-lg font-bold tracking-tight text-slate-950 sm:text-xl">
              TheCloudMind.ai
            </div>
            <div className="text-xs uppercase tracking-[0.28em] text-slate-500">
              AI and sports intelligence
            </div>
          </div>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className="text-sm font-medium text-slate-700 transition hover:text-slate-950"
            >
              {link.label}
            </Link>
          ))}
          <a
            href="https://www.youtube.com/@CloudMindAI"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-medium text-slate-500 transition hover:text-red-600"
          >
            YouTube
          </a>
          <a
            href="https://www.instagram.com/thecloudmind.ai/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-medium text-slate-500 transition hover:text-pink-600"
          >
            Instagram
          </a>
        </nav>

        {/* Desktop Admin Controls */}
        <div className="hidden items-center gap-2 md:flex">
          {token && (
            <>
              <Link
                to="/admin"
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-950 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
              >
                <Settings className="h-4 w-4" />
                Dashboard
              </Link>
              <button
                onClick={handleLogout}
                className="inline-flex items-center gap-2 rounded-full border border-red-200 bg-red-50 px-4 py-2 text-sm font-medium text-red-600 transition hover:bg-red-100"
              >
                <LogOut className="h-4 w-4" />
                Logout
              </button>
            </>
          )}
        </div>

        {/* Mobile Hamburger */}
        <button
          type="button"
          onClick={() => setMobileOpen((prev) => !prev)}
          className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white p-2.5 text-slate-700 shadow-sm transition hover:bg-slate-50 md:hidden"
          aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile Dropdown */}
      {mobileOpen && (
        <div className="border-t border-slate-100 bg-white/98 shadow-xl backdrop-blur-xl md:hidden">
          <div className="mx-auto max-w-7xl divide-y divide-slate-100 px-4 py-3 sm:px-6">
            <div className="flex flex-col pb-3">
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={closeMobile}
                  className="rounded-xl px-4 py-3 text-sm font-medium text-slate-800 transition hover:bg-slate-50 hover:text-slate-950"
                >
                  {link.label}
                </Link>
              ))}
              <a
                href="https://www.youtube.com/@CloudMindAI"
                target="_blank"
                rel="noopener noreferrer"
                onClick={closeMobile}
                className="rounded-xl px-4 py-3 text-sm font-medium text-slate-500 transition hover:bg-slate-50 hover:text-red-600"
              >
                YouTube
              </a>
              <a
                href="https://www.instagram.com/thecloudmind.ai/"
                target="_blank"
                rel="noopener noreferrer"
                onClick={closeMobile}
                className="rounded-xl px-4 py-3 text-sm font-medium text-slate-500 transition hover:bg-slate-50 hover:text-pink-600"
              >
                Instagram
              </a>
            </div>

            {token && (
              <div className="flex flex-col gap-2 pt-3">
                <Link
                  to="/admin"
                  onClick={closeMobile}
                  className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800"
                >
                  <Settings className="h-4 w-4" />
                  Admin Dashboard
                </Link>
                <button
                  onClick={handleLogout}
                  className="inline-flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-600 transition hover:bg-red-100"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
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
