import { useState } from 'react'
import { Share2, Link as LinkIcon, Check } from 'lucide-react'

// Reusable share row — used on article and job detail pages.
function ShareBar({ url, title, label = 'Share this' }) {
  const [copied, setCopied] = useState(false)
  const encodedUrl = encodeURIComponent(url)
  const encodedTitle = encodeURIComponent(title)

  const nativeShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({ title, url })
      } catch {
        /* user cancelled — ignore */
      }
    } else {
      copyLink()
    }
  }

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* clipboard blocked — ignore */
    }
  }

  const links = [
    { label: 'WhatsApp', href: `https://wa.me/?text=${encodedTitle}%20${encodedUrl}`, color: '#25D366' },
    { label: 'X', href: `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${encodedTitle}`, color: '#1A1A17' },
    { label: 'LinkedIn', href: `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`, color: '#0A66C2' },
    { label: 'Facebook', href: `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`, color: '#1877F2' },
  ]

  const chipStyle = {
    display: 'inline-flex', alignItems: 'center', gap: 6,
    padding: '8px 14px', borderRadius: 9999, fontSize: 13, fontWeight: 600,
    textDecoration: 'none', cursor: 'pointer', fontFamily: 'inherit',
    border: '1px solid var(--cm-border)', background: 'var(--cm-card)', color: 'var(--fg3)',
  }

  return (
    <div style={{ marginTop: 20, background: 'var(--cm-card)', border: '1px solid #e2e8f0', borderRadius: 20, padding: 'clamp(14px, 3vw, 18px) clamp(16px, 3.5vw, 22px)', boxShadow: 'var(--shadow-subtle)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <span style={{ display: 'inline-flex', gap: 8, alignItems: 'center', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '.18em', color: 'var(--fg5)', marginRight: 4 }}>
          <Share2 size={15} /> {label}
        </span>
        <button onClick={nativeShare} style={{ ...chipStyle, background: 'var(--bg5)', color: '#fff', border: '1px solid var(--bg5)' }}>
          <Share2 size={14} /> Share
        </button>
        {links.map(l => (
          <a key={l.label} href={l.href} target="_blank" rel="noopener noreferrer" style={{ ...chipStyle, color: l.color }}>
            {l.label}
          </a>
        ))}
        <button onClick={copyLink} style={chipStyle}>
          {copied ? <><Check size={14} /> Copied</> : <><LinkIcon size={14} /> Copy link</>}
        </button>
      </div>
    </div>
  )
}

export default ShareBar
