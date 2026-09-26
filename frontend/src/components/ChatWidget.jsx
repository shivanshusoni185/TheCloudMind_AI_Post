import { useState, lazy, Suspense } from 'react'
import { useLocation } from 'react-router-dom'
import { Sparkles, X } from 'lucide-react'

// The panel (and the markdown renderer it uses) is only downloaded when a
// visitor first opens JEV AI, so it costs nothing on initial page load.
const JevPanel = lazy(() => import('./JevPanel'))

// Floating JEV AI button (bottom-right) that opens the assistant panel.
function ChatWidget() {
  const { pathname } = useLocation()
  const [open, setOpen] = useState(false)
  if (pathname.startsWith('/admin')) return null

  return (
    <>
      {open && (
        <Suspense fallback={null}>
          <JevPanel onClose={() => setOpen(false)} />
        </Suspense>
      )}
      <button
        onClick={() => setOpen(o => !o)}
        aria-label={open ? 'Close JEV AI' : 'Ask JEV AI'}
        aria-expanded={open}
        title="Ask JEV AI"
        style={{
          position: 'fixed', bottom: 24, right: 24, zIndex: 60,
          height: 56, minWidth: 56, padding: open ? 0 : '0 20px 0 16px', borderRadius: 9999,
          background: 'var(--bg5)', color: '#fff', border: 'none', cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          boxShadow: 'var(--shadow-cta)', fontFamily: 'inherit', fontSize: 14, fontWeight: 700,
          transition: 'transform .2s, box-shadow .2s',
        }}
        onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.04)' }}
        onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)' }}
      >
        {open ? <X size={24} /> : <><Sparkles size={20} /> JEV AI</>}
      </button>
    </>
  )
}

export default ChatWidget
