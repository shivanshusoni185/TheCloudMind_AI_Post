import { Link, useNavigate } from 'react-router-dom'
import { LogOut, Settings } from 'lucide-react'
import logo from '../assets/logo.jpg'

function Header() {
  const navigate = useNavigate()
  const token = localStorage.getItem('token')

  const handleLogout = () => {
    localStorage.removeItem('token')
    navigate('/')
  }

  return (
    <header className="sticky top-0 z-40 border-b border-white/60 bg-white/75 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        <Link to="/" className="flex items-center gap-3">
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

        <nav className="hidden items-center gap-8 md:flex">
          <Link to="/" className="text-sm font-medium text-slate-700 transition hover:text-slate-950">
            Home
          </Link>
          <Link to="/latest-news" className="text-sm font-medium text-slate-700 transition hover:text-slate-950">
            Latest
          </Link>
          <Link to="/about" className="text-sm font-medium text-slate-700 transition hover:text-slate-950">
            About
          </Link>
          <Link to="/contact" className="text-sm font-medium text-slate-700 transition hover:text-slate-950">
            Contact
          </Link>
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

        {token && (
          <div className="flex items-center gap-2">
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
          </div>
        )}
      </div>
    </header>
  )
}

export default Header
