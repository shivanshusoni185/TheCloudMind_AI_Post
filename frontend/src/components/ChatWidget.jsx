import { Link, useLocation } from 'react-router-dom'
import { MessageCircle } from 'lucide-react'

// Floating action button (bottom-right) matching the redesign's chat bubble.
// Routes to the Contact page so it's a working support entry point.
function ChatWidget() {
  const { pathname } = useLocation()
  if (pathname.startsWith('/admin')) return null

  return (
    <Link
      to="/contact"
      aria-label="Contact us"
      title="Questions? Get in touch"
      style={{
        position: 'fixed', bottom: 24, right: 24, zIndex: 50,
        width: 56, height: 56, borderRadius: '50%',
        background: 'var(--bg5)', color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: 'var(--shadow-cta)', textDecoration: 'none',
        transition: 'transform .2s, box-shadow .2s',
      }}
      onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.06)' }}
      onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)' }}
    >
      <MessageCircle size={24} />
    </Link>
  )
}

export default ChatWidget
