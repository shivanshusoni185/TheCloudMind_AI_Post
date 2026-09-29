import { Link } from 'react-router-dom'
import { ArrowUpRight } from 'lucide-react'
import logo from '../assets/logo-square.webp'

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="site-width">
        <div className="footer-top">
          <div><Link to="/" className="brand"><img className="brand-logo" src={logo} alt="" width={44} height={44} loading="lazy" /><span>TheCloudMind<span className="brand-ai">.ai</span></span></Link><p>For curious minds.<br />For a world that never stands still.</p></div>
          <div><span className="eyebrow">EXPLORE</span><Link to="/latest-news">Latest stories</Link><Link to="/jobs">Find your next role</Link><Link to="/about">Our story</Link><Link to="/contact">Get in touch</Link></div>
          <div><span className="eyebrow">STAY IN THE LOOP</span><a href="https://www.youtube.com/@CloudMindAI" target="_blank" rel="noopener noreferrer">YouTube <ArrowUpRight size={14} /></a><a href="https://www.instagram.com/thecloudmind.ai/" target="_blank" rel="noopener noreferrer">Instagram <ArrowUpRight size={14} /></a><a href="mailto:contact@cloudmindai.in">contact@cloudmindai.in <ArrowUpRight size={14} /></a></div>
        </div>
        <div className="footer-bottom"><span>© {new Date().getFullYear()} TheCloudMind.ai</span><span>Intelligence, with a human perspective.<span className="status-dot" /></span><a href="#main-content">Back to top ↑</a></div>
      </div>
    </footer>
  )
}
