import { Link } from 'react-router-dom'
import logo from '../assets/logo.jpg'

function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="mt-16 border-t border-slate-200/80 bg-slate-950 text-slate-200">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:grid-cols-3 sm:px-6">
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <img
              src={logo}
              alt="TheCloudMind.ai"
              className="h-14 w-14 rounded-2xl object-cover ring-2 ring-white/10"
            />
            <div>
              <div className="text-xl font-bold text-white">TheCloudMind.ai</div>
              <div className="text-xs uppercase tracking-[0.28em] text-slate-400">
                Original analysis, not copied feeds
              </div>
            </div>
          </div>
          <p className="max-w-sm text-sm leading-7 text-slate-400">
            Built to turn raw reporting into fast, readable coverage with better sourcing,
            cleaner visuals, and a product surface that feels editorial.
          </p>
        </div>

        <div>
          <div className="mb-4 text-sm font-semibold uppercase tracking-[0.22em] text-slate-500">
            Navigate
          </div>
          <div className="space-y-3 text-sm text-slate-300">
            <Link to="/" className="block transition hover:text-white">Home</Link>
            <Link to="/latest-news" className="block transition hover:text-white">Latest News</Link>
            <Link to="/about" className="block transition hover:text-white">About</Link>
            <Link to="/contact" className="block transition hover:text-white">Contact</Link>
          </div>
        </div>

        <div>
          <div className="mb-4 text-sm font-semibold uppercase tracking-[0.22em] text-slate-500">
            Channels
          </div>
          <div className="space-y-3 text-sm text-slate-300">
            <a href="https://www.youtube.com/@CloudMindAI" target="_blank" rel="noopener noreferrer" className="block transition hover:text-white">
              YouTube
            </a>
            <a href="https://www.instagram.com/thecloudmind.ai/" target="_blank" rel="noopener noreferrer" className="block transition hover:text-white">
              Instagram
            </a>
            <a href="mailto:contact@cloudmindai.in" className="block transition hover:text-white">
              contact@cloudmindai.in
            </a>
          </div>
        </div>
      </div>

      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-5 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <p>Copyright {currentYear} TheCloudMind.ai</p>
          <p>AI-first newsroom workflow with direct-source publishing.</p>
        </div>
      </div>
    </footer>
  )
}

export default Footer
