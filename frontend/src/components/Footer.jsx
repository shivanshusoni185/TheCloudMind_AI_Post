import { Link } from 'react-router-dom'
import { Mail, Youtube, Instagram, Heart } from 'lucide-react'
import logo from '../assets/logo.jpg'

function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white mt-12 sm:mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8 mb-6 sm:mb-8">
          {/* Brand */}
          <div className="space-y-3 sm:space-y-4">
            <div className="flex items-center gap-3">
              <img
                src={logo}
                alt="TheCloudMind.ai"
                className="h-12 w-12 sm:h-16 sm:w-16 rounded-full object-cover shadow-xl ring-2 ring-white/20"
              />
              <div>
                <h3 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
                  TheCloudMind.ai
                </h3>
                <p className="text-xs sm:text-sm text-gray-300">AI News & Insights</p>
              </div>
            </div>
            <p className="text-gray-300 text-xs sm:text-sm leading-relaxed">
              Your trusted source for the latest AI developments, innovations, and insights.
              Stay informed about the future of artificial intelligence.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="font-bold text-base sm:text-lg mb-3 sm:mb-4 text-cyan-400">Quick Links</h4>
            <ul className="space-y-2 sm:space-y-3">
              {[
                { to: '/', label: 'Home' },
                { to: '/latest-news', label: 'Latest News' },
                { to: '/about', label: 'About Us' },
                { to: '/contact', label: 'Contact' },
              ].map((link) => (
                <li key={link.to}>
                  <Link
                    to={link.to}
                    className="text-gray-300 hover:text-white transition-colors flex items-center gap-2 group text-sm sm:text-base"
                  >
                    <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full group-hover:bg-white transition-colors"></span>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Connect */}
          <div>
            <h4 className="font-bold text-base sm:text-lg mb-3 sm:mb-4 text-cyan-400">Connect With Us</h4>
            <div className="space-y-3 sm:space-y-4">
              <Link
                to="/contact"
                className="inline-flex items-center gap-2 px-3 sm:px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors text-white text-sm sm:text-base"
              >
                <Mail className="w-4 h-4 sm:w-5 sm:h-5" />
                <span>Send us a Message</span>
              </Link>
              <div>
                <p className="text-xs sm:text-sm text-gray-400 mb-2">Follow us on social media</p>
                <div className="flex gap-2 sm:gap-3">
                  <a
                    href="https://www.youtube.com/@CloudMindAI"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 sm:p-3 bg-white/10 rounded-lg hover:bg-red-600 transition-all transform hover:scale-110"
                    aria-label="YouTube"
                  >
                    <Youtube className="w-4 h-4 sm:w-5 sm:h-5" />
                  </a>
                  <a
                    href="https://www.instagram.com/thecloudmind.ai/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 sm:p-3 bg-white/10 rounded-lg hover:bg-pink-600 transition-all transform hover:scale-110"
                    aria-label="Instagram"
                  >
                    <Instagram className="w-4 h-4 sm:w-5 sm:h-5" />
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-white/10 pt-6 sm:pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-3 sm:gap-4">
            <p className="text-xs sm:text-sm text-gray-400 text-center md:text-left">
              &copy; {currentYear} TheCloudMind.ai. All rights reserved.
            </p>
            <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-4 text-xs sm:text-sm text-gray-400">
              <Link to="/" className="hover:text-white transition-colors">Privacy Policy</Link>
              <span className="hidden sm:block">•</span>
              <Link to="/" className="hover:text-white transition-colors">Terms of Service</Link>
              <span className="hidden sm:block">•</span>
              <p className="flex items-center gap-1">
                Made with <Heart className="w-3 h-3 sm:w-4 sm:h-4 text-red-500 fill-red-500" /> for AI Enthusiasts
              </p>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer
