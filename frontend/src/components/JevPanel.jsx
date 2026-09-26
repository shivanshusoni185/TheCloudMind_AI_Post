import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { X, Send, Loader, Newspaper, Briefcase, Sparkles } from 'lucide-react'
import { jevApi } from '../lib/api'
import { renderArticleContent } from '../lib/content'

const STORAGE_KEY = 'tcm_jev_chat'
const SUGGESTIONS = [
  "What's the latest in AI?",
  'Any remote software jobs?',
  'Latest cricket and IPL updates',
]

function loadHistory() {
  try {
    return JSON.parse(sessionStorage.getItem(STORAGE_KEY)) || []
  } catch {
    return []
  }
}

function saveHistory(messages) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-20)))
  } catch { /* ignore */ }
}

function Sources({ sources, onNavigate }) {
  if (!sources?.length) return null
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 10 }}>
      {sources.map(s => (
        <Link key={s.path} to={s.path} onClick={onNavigate} style={{
          display: 'flex', gap: 8, alignItems: 'center', padding: '8px 10px',
          background: '#fff', border: '1px solid var(--cm-border)', borderRadius: 10,
          color: 'var(--fg1)', fontSize: 12.5, fontWeight: 600, textDecoration: 'none',
          lineHeight: 1.35,
        }}>
          {s.type === 'job'
            ? <Briefcase size={14} style={{ flexShrink: 0, color: 'var(--cm-accent-2)' }} />
            : <Newspaper size={14} style={{ flexShrink: 0, color: 'var(--cm-accent)' }} />}
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{s.title}</span>
        </Link>
      ))}
    </div>
  )
}

// JEV AI chat panel. Lazy-loaded by ChatWidget on first open so the
// markdown renderer and this UI stay out of the initial page bundle.
function JevPanel({ onClose }) {
  const [messages, setMessages] = useState(loadHistory)
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const scrollRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => { inputRef.current?.focus() }, [])
  useEffect(() => {
    saveHistory(messages)
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, sending])

  const ask = async (text) => {
    const question = text.trim()
    if (!question || sending) return
    const next = [...messages, { role: 'user', content: question }]
    setMessages(next)
    setInput('')
    setSending(true)
    try {
      const history = next.filter(m => !m.error).map(({ role, content }) => ({ role, content }))
      const { data } = await jevApi.chat(history)
      setMessages([...next, { role: 'assistant', content: data.answer, sources: data.sources }])
    } catch (err) {
      const msg = err.response?.status === 429
        ? "You're asking faster than I can keep up — please wait a moment and try again."
        : "Sorry, I couldn't reach JEV AI right now. Please try again."
      // Flagged as error so it's never sent back to the API as history.
      setMessages([...next, { role: 'assistant', content: msg, error: true }])
    } finally {
      setSending(false)
    }
  }

  return (
    <div role="dialog" aria-label="JEV AI assistant" className="jev-panel" style={{
      position: 'fixed', bottom: 92, right: 24, zIndex: 60,
      width: 380, maxWidth: 'calc(100vw - 32px)', height: 560, maxHeight: 'calc(100vh - 120px)',
      background: 'var(--cm-card)', border: '1px solid var(--cm-border)', borderRadius: 20,
      boxShadow: 'var(--shadow-cta)', display: 'flex', flexDirection: 'column', overflow: 'hidden',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '14px 16px', background: 'var(--bg5)', color: '#fff' }}>
        <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'rgba(255,255,255,.14)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Sparkles size={17} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: 15 }}>JEV AI</div>
          <div style={{ fontSize: 11.5, opacity: .75 }}>Ask about AI, tech, cricket or jobs</div>
        </div>
        {messages.length > 0 && (
          <button onClick={() => setMessages([])} style={{ background: 'none', border: 'none', color: '#fff', opacity: .75, fontSize: 12, cursor: 'pointer', fontFamily: 'inherit' }}>
            Clear
          </button>
        )}
        <button onClick={onClose} aria-label="Close JEV AI" style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer', padding: 4, display: 'flex' }}>
          <X size={20} />
        </button>
      </div>

      <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {messages.length === 0 && (
          <div style={{ color: 'var(--fg4)', fontSize: 14, lineHeight: 1.55 }}>
            <p style={{ margin: '0 0 12px' }}>Hi! I'm <strong style={{ color: 'var(--fg1)' }}>JEV AI</strong>. I can answer questions using TheCloudMind's latest stories and job listings.</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {SUGGESTIONS.map(s => (
                <button key={s} onClick={() => ask(s)} style={{
                  textAlign: 'left', padding: '9px 12px', background: '#fff', border: '1px solid var(--cm-border)',
                  borderRadius: 12, fontSize: 13, color: 'var(--fg1)', cursor: 'pointer', fontFamily: 'inherit',
                }}>{s}</button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} style={{ alignSelf: m.role === 'user' ? 'flex-end' : 'stretch', maxWidth: m.role === 'user' ? '85%' : '100%' }}>
            {m.role === 'user' ? (
              <div style={{ background: 'var(--bg5)', color: '#fff', padding: '9px 13px', borderRadius: '14px 14px 4px 14px', fontSize: 14, lineHeight: 1.45, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {m.content}
              </div>
            ) : (
              <div>
                <div className="jev-answer" style={{ background: '#fff', border: '1px solid var(--cm-border)', padding: '10px 13px', borderRadius: '14px 14px 14px 4px', fontSize: 14, lineHeight: 1.55, color: m.error ? '#b91c1c' : 'var(--fg1)', wordBreak: 'break-word' }}
                  dangerouslySetInnerHTML={{ __html: renderArticleContent(m.content) }} />
                <Sources sources={m.sources} onNavigate={onClose} />
              </div>
            )}
          </div>
        ))}
        {sending && (
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', color: 'var(--fg4)', fontSize: 13 }}>
            <Loader size={15} className="animate-spin" /> JEV AI is thinking…
          </div>
        )}
      </div>

      <form onSubmit={e => { e.preventDefault(); ask(input) }} style={{ display: 'flex', gap: 8, padding: 12, borderTop: '1px solid var(--cm-border)' }}>
        <input
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          maxLength={1500}
          placeholder="Ask JEV AI…"
          aria-label="Message JEV AI"
          style={{ flex: 1, border: '1px solid #e2e8f0', background: '#fff', borderRadius: 12, padding: '10px 12px', fontSize: 14, fontFamily: 'inherit', outline: 'none', minWidth: 0 }}
        />
        <button type="submit" disabled={sending || !input.trim()} aria-label="Send" style={{
          background: 'var(--bg5)', color: '#fff', border: 'none', borderRadius: 12, width: 42,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: sending || !input.trim() ? 'default' : 'pointer', opacity: sending || !input.trim() ? .5 : 1,
        }}>
          <Send size={17} />
        </button>
      </form>
    </div>
  )
}

export default JevPanel
