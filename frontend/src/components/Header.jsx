import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LogOut, Settings, Menu, X } from 'lucide-react'
import logo from '../assets/logo.jpg'

const NAV_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/latest-news', label: 'Latest News' },
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
    <header className="bg-white shadow-md border-b border-gray-200 sticky top-0 z-40">
      <div className="container mx-auto px-3 sm:px-4 py-2 flex justify-between items-center">
        {/* Logo */}
        <Link to="/" className="flex items-center space-x-2 group" onClick={closeMobile}>
          <img
            src={logo}
            alt="TheCloudMind.ai"
            className="h-12 w-12 sm:h-14 sm:w-14 rounded-full object-cover transition-transform group-hover:scale-105"
          />
          <span className="text-base sm:text-xl font-bold bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-600 bg-clip-text text-transparent hidden sm:block">
            TheCloudMind.ai
          </span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex space-x-6 items-center">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className="text-gray-700 hover:text-blue-600 transition font-medium"
            >
              {link.label}
            </Link>
          ))}
          <a
            href="https://www.youtube.com/@CloudMindAI"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-600 hover:text-red-600 transition"
            aria-label="YouTube"
          >
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
            </svg>
          </a>
          <a
            href="https://www.instagram.com/thecloudmind.ai/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-600 hover:text-pink-600 transition"
            aria-label="Instagram"
          >
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 0 0 0-12.324zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.406-11.845a1.44 1.44 0 1 0 0 2.881 1.44 1.44 0 0 0 0-2.881z"/>
            </svg>
          </a>
        </nav>

        {/* Desktop Admin Controls */}
        <div className="hidden md:flex items-center gap-2">
          {token && (
            <>
              <Link
                to="/admin"
                className="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-700 transition"
              >
                <Settings className="h-4 w-4" />
                Dashboard
              </Link>
              <button
                onClick={handleLogout}
                className="inline-flex items-center gap-2 px-4 py-2 border border-red-200 bg-red-50 text-red-600 rounded-lg text-sm font-medium hover:bg-red-100 transition"
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
          className="md:hidden p-2 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 transition"
          aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile Dropdown */}
      {mobileOpen && (
        <div className="md:hidden border-t border-gray-100 bg-white shadow-lg">
          <div className="container mx-auto px-4 py-3 flex flex-col gap-1">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                onClick={closeMobile}
                className="px-3 py-2.5 rounded-lg text-sm font-medium text-gray-800 hover:bg-gray-50 hover:text-blue-600 transition"
              >
                {link.label}
              </Link>
            ))}
            <div className="flex gap-4 px-3 py-2">
              <a href="https://www.youtube.com/@CloudMindAI" target="_blank" rel="noopener noreferrer" className="text-gray-500 hover:text-red-600 transition text-sm font-medium">YouTube</a>
              <a href="https://www.instagram.com/thecloudmind.ai/" target="_blank" rel="noopener noreferrer" className="text-gray-500 hover:text-pink-600 transition text-sm font-medium">Instagram</a>
            </div>
            {token && (
              <div className="flex flex-col gap-2 pt-2 border-t border-gray-100 mt-1">
                <Link to="/admin" onClick={closeMobile} className="inline-flex items-center gap-2 px-3 py-2.5 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-700 transition">
                  <Settings className="h-4 w-4" /> Admin Dashboard
                </Link>
                <button onClick={handleLogout} className="inline-flex items-center gap-2 px-3 py-2.5 border border-red-200 bg-red-50 text-red-600 rounded-lg text-sm font-medium hover:bg-red-100 transition">
                  <LogOut className="h-4 w-4" /> Logout
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
