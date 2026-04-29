import { Helmet } from 'react-helmet-async'
import { Target, Users, Zap, Brain, TrendingUp } from 'lucide-react'
import logo from '../assets/logo.png'

const values = [
  { icon: Brain, title: 'Expert Knowledge', color: 'teal', description: 'Deep understanding of AI technology and its implications for the future.' },
  { icon: TrendingUp, title: 'Latest Updates', color: 'blue', description: 'Timely coverage of breaking AI news and developments worldwide.' },
  { icon: Users, title: 'Community Focused', color: 'teal', description: 'Building a community of AI enthusiasts, researchers, and professionals.' },
  { icon: Zap, title: 'Innovation First', color: 'blue', description: 'Highlighting cutting-edge breakthroughs in artificial intelligence.' },
]

const colorMap = {
  teal: { bg: 'var(--teal-50)', fg: 'var(--cm-accent)' },
  blue: { bg: 'var(--blue-50, #eff6ff)', fg: 'var(--cm-accent-2)' },
}

function AboutUs() {
  return (
    <>
      <Helmet>
        <title>About Us - TheCloudMind.ai | Our Mission & Story</title>
        <meta name="description" content="Learn about TheCloudMind.ai - democratizing AI knowledge through expert coverage of artificial intelligence news, machine learning developments, and GenAI innovations." />
        <meta name="keywords" content="about TheCloudMind.ai, AI news platform, AI community, AI knowledge" />
        <meta property="og:title" content="About Us - TheCloudMind.ai" />
        <meta property="og:description" content="Democratizing AI knowledge through expert coverage and insights." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://cloudmindai.in/about" />
        <meta name="twitter:card" content="summary_large_image" />
        <link rel="canonical" href="https://cloudmindai.in/about" />
      </Helmet>
      <div style={{ maxWidth: 820, margin: '0 auto', padding: '48px 24px' }}>
        {/* Hero */}
        <section style={{ textAlign: 'center', marginBottom: 48 }}>
          <img src={logo} alt="TheCloudMind.ai" style={{ height: 100, width: 100, borderRadius: '50%', objectFit: 'cover', display: 'inline-block' }} />
          <div style={{ marginTop: 18 }}><div className="eyebrow">ABOUT US</div></div>
          <h1 style={{ margin: '8px 0 0', fontSize: 'clamp(32px, 5vw, 44px)', fontWeight: 700, letterSpacing: '-.015em', color: 'var(--fg1)' }}>
            TheCloudMind.ai
          </h1>
          <p style={{ margin: '18px auto 0', maxWidth: 520, fontFamily: 'var(--font-serif)', fontSize: 19, lineHeight: 1.8, color: 'var(--fg4)' }}>
            Your trusted source for AI news — direct from publishers, rewritten for clarity.
          </p>
        </section>

        {/* Mission */}
        <section style={{ background: 'var(--cm-card)', border: '1px solid #e2e8f0', borderRadius: 32, padding: 36, boxShadow: 'var(--shadow-card)', marginBottom: 20 }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
            <div style={{ background: 'var(--teal-50)', color: 'var(--cm-accent)', padding: 12, borderRadius: 16, flexShrink: 0 }}>
              <Target size={26} />
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: 24, fontWeight: 700, letterSpacing: '-.01em', color: 'var(--fg1)' }}>Our Mission</h2>
              <p style={{ margin: '10px 0 0', fontFamily: 'var(--font-serif)', fontSize: 17, lineHeight: 1.8, color: 'var(--fg4)' }}>
                To democratize access to AI knowledge by providing accurate, timely, and insightful coverage.
                We pull directly from publishers, extract the real story, and rewrite it into a cleaner editorial
                format so you get the information without the noise.
              </p>
            </div>
          </div>
        </section>

        {/* Values */}
        <section style={{ marginBottom: 20 }}>
          <div className="eyebrow">WHAT WE STAND FOR</div>
          <h2 style={{ margin: '4px 0 22px', fontSize: 24, fontWeight: 700, color: 'var(--fg1)' }}>Built on four principles</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }} className="values-grid">
            {values.map(v => (
              <div key={v.title} style={{ background: 'var(--cm-card)', border: '1px solid rgba(226,232,240,.8)', borderRadius: 28, padding: 24, boxShadow: 'var(--shadow-rest)' }}>
                <div style={{ background: colorMap[v.color].bg, color: colorMap[v.color].fg, padding: 10, borderRadius: 16, width: 'fit-content' }}>
                  <v.icon size={22} />
                </div>
                <h3 style={{ margin: '14px 0 6px', fontSize: 18, fontWeight: 700, color: 'var(--fg1)' }}>{v.title}</h3>
                <p style={{ margin: 0, fontSize: 14, lineHeight: 1.6, color: 'var(--fg4)' }}>{v.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section style={{ background: 'var(--bg5)', color: '#fff', padding: 44, borderRadius: 32, textAlign: 'center', boxShadow: 'var(--shadow-cta)' }}>
          <h2 style={{ margin: 0, fontSize: 26, fontWeight: 700, color: '#fff' }}>Stay in the loop</h2>
          <p style={{ margin: '10px auto 24px', maxWidth: 420, color: '#94a3b8', fontSize: 14, lineHeight: 1.7 }}>
            Follow us on YouTube and Instagram for daily AI briefs, highlights, and behind-the-scenes content.
          </p>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <a href="https://www.youtube.com/@CloudMindAI" target="_blank" rel="noopener noreferrer"
              style={{ display: 'inline-flex', gap: 8, alignItems: 'center', padding: '10px 22px', background: '#fff', color: 'var(--bg5)', borderRadius: 9999, fontSize: 14, fontWeight: 600, textDecoration: 'none' }}>
              YouTube
            </a>
            <a href="https://www.instagram.com/thecloudmind.ai/" target="_blank" rel="noopener noreferrer"
              style={{ display: 'inline-flex', gap: 8, alignItems: 'center', padding: '10px 22px', background: 'transparent', color: '#fff', border: '1px solid rgba(255,255,255,.2)', borderRadius: 9999, fontSize: 14, fontWeight: 600, textDecoration: 'none' }}>
              Instagram
            </a>
          </div>
        </section>
      </div>
    </>
  )
}

export default AboutUs
