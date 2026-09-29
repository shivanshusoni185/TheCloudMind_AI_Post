import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { ArrowUpRight, Menu, X, LogOut } from 'lucide-react'
import logo from '../assets/logo-square.webp'

const links = [['/', 'Home'], ['/latest-news', 'The Latest'], ['/jobs', 'Careers'], ['/about', 'About us']]

export default function Header() {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()
  const token = localStorage.getItem('token')
  const close = () => setOpen(false)
  return (
    <header className="site-header">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <div className="site-width header-inner">
        <Link to="/" className="brand" onClick={close} aria-label="TheCloudMind.ai home">
          <img className="brand-logo" src={logo} alt="" width={44} height={44} />
          <span>TheCloudMind<span className="brand-ai">.ai</span><small>A WORLD OF WHAT'S NEXT</small></span>
        </Link>
        <nav className="desktop-nav" aria-label="Main navigation">
          {links.map(([to, label]) => <NavLink key={to} to={to} end={to === '/'}>{label}</NavLink>)}
        </nav>
        <div className="header-actions">
          {token && <><Link className="admin-link" to="/admin">Dashboard</Link><button className="icon-button" aria-label="Log out" onClick={() => { localStorage.removeItem('token'); navigate('/'); close() }}><LogOut size={18} /></button></>}
          <Link to="/contact" className="button button-dark header-cta">Let's connect <ArrowUpRight size={16} /></Link>
          <button className="icon-button menu-toggle" onClick={() => setOpen(!open)} aria-expanded={open} aria-controls="mobile-navigation" aria-label={open ? 'Close menu' : 'Open menu'}>{open ? <X /> : <Menu />}</button>
        </div>
      </div>
      {open && <nav id="mobile-navigation" className="mobile-nav" aria-label="Mobile navigation" onKeyDown={e => { if (e.key === 'Escape') close() }}>
        {links.concat([['/contact', 'Let’s connect']]).map(([to, label]) => <NavLink key={to} to={to} end={to === '/'} onClick={close}>{label}<ArrowUpRight size={16} /></NavLink>)}
      </nav>}
    </header>
  )
}
