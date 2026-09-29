import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { ArrowDown, ArrowRight, ArrowUpRight, AudioLines, Cpu, Globe2, Loader, Pause, Play, Search, Sparkles, TrendingUp, Trophy } from 'lucide-react'
import IntelligenceGlobe from '../components/IntelligenceGlobe'
import NewsCard from '../components/NewsCard'
import { newsApi, getLocalCache, setLocalCache } from '../lib/api'

const PAGE_SIZE = 12
const topics = [['', 'All stories'], ['AI', 'Artificial intelligence'], ['Cricket', 'Cricket'], ['Finance', 'Financial news']]

function NewsFeed({ search, active, clear }) {
  const cacheKey = search ? null : `news_home:${active}`
  const [articles, setArticles] = useState(() => (cacheKey && getLocalCache(cacheKey)) || [])
  const [loading, setLoading] = useState(() => !(cacheKey && getLocalCache(cacheKey)))
  const [error, setError] = useState('')
  const [hasMore, setHasMore] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [retry, setRetry] = useState(0)
  const mounted = useRef(false)

  useEffect(() => {
    let cancelled = false
    mounted.current = true
    newsApi.getAll(search, active, { limit: PAGE_SIZE }).then(({ data }) => {
      if (cancelled) return
      setArticles(data)
      setHasMore(data.length === PAGE_SIZE)
      if (cacheKey) setLocalCache(cacheKey, data)
      setError('')
    }).catch(() => {
      if (!cancelled) setError('We couldn’t refresh the stories. Please try again.')
    }).finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true; mounted.current = false }
  }, [search, active, cacheKey, retry])

  const loadMore = async () => {
    setLoadingMore(true)
    setError('')
    try {
      const { data } = await newsApi.getAll(search, active, { limit: PAGE_SIZE, offset: articles.length })
      if (!mounted.current) return
      setArticles(previous => { const seen = new Set(previous.map(a => a.id)); return [...previous, ...data.filter(a => !seen.has(a.id))] })
      setHasMore(data.length === PAGE_SIZE)
    } catch {
      if (mounted.current) setError('More stories couldn’t be loaded. Please try again.')
    } finally {
      if (mounted.current) setLoadingMore(false)
    }
  }

  return <div aria-busy={loading || loadingMore}>
    {error && <div className="feed-notice" role="alert"><span>{error}</span><button onClick={() => { setLoading(true); setRetry(r => r + 1) }}>Retry</button></div>}
    {loading && articles.length === 0 ? <div className="story-grid skeleton-grid" role="status"><span className="sr-only">Loading stories</span>{[0, 1, 2].map(i => <div className="story-skeleton" key={i}><div /><span /><span /></div>)}</div> : articles.length === 0 ? <div className="empty-feed"><Search size={28} /><h3>{error ? 'The newsroom is temporarily unavailable.' : active === 'Finance' && !search ? 'Financial news is on its way.' : 'No stories found.'}</h3><p>{error ? 'You can retry in a moment.' : active === 'Finance' && !search ? 'Published financial stories will appear here. Explore our other topics in the meantime.' : 'Try another topic or a different search.'}</p>{(search || active) && <button className="button button-dark" onClick={clear}>Clear filters <ArrowRight size={16} /></button>}</div> : <>
      <div className="story-grid">{articles.map((article, index) => <NewsCard article={article} key={article.id} featured={index === 0 && !search} />)}</div>
      {hasMore && <div className="load-more"><button className="button button-outline" onClick={loadMore} disabled={loadingMore}>{loadingMore ? <Loader className="animate-spin" size={17} /> : <ArrowDown size={17} />}{loadingMore ? 'Loading stories…' : 'More to discover'}</button><span>There’s always another perspective.</span></div>}
    </>}
  </div>
}

export default function Home() {
  const [active, setActive] = useState('')
  const [input, setInput] = useState('')
  const [search, setSearch] = useState('')
  const [paused, setPaused] = useState(false)
  const homeRef = useRef(null)
  useEffect(() => {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('is-visible'); observer.unobserve(entry.target) }
    }), { threshold: 0, rootMargin: '0px 0px -30px 0px' })
    homeRef.current.querySelectorAll('[data-reveal]').forEach(element => observer.observe(element))
    return () => observer.disconnect()
  }, [])
  const chooseTopic = topic => {
    setActive(topic)
    setSearch('')
    setInput('')
    document.getElementById('the-edit')?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' })
  }
  const clear = () => { setActive(''); setSearch(''); setInput('') }

  return <div className="home" ref={homeRef} data-paused={paused}>
    <Helmet>
      <title>TheCloudMind.ai — Stay curious. Think ahead.</title>
      <meta name="description" content="Discover the ideas shaping tomorrow. Fresh perspectives on artificial intelligence, financial news, cricket, and careers from TheCloudMind.ai." />
      <meta property="og:title" content="TheCloudMind.ai — Stay curious. Think ahead." />
      <meta property="og:description" content="Your daily perspective on AI, finance, sport and what comes next." />
      <meta property="og:type" content="website" />
      <meta property="og:url" content="https://cloudmindai.in/" />
      <meta name="twitter:card" content="summary_large_image" />
      <link rel="canonical" href="https://cloudmindai.in/" />
    </Helmet>
    <section className="hero site-width" aria-labelledby="hero-title">
      <div className="hero-topline"><span><span className="status-dot" /> INDEPENDENT PERSPECTIVES. CONNECTED MINDS.</span><span className="hero-edition">AI · FINANCE · SPORT · OPPORTUNITY</span></div>
      <div className="hero-main">
        <div className="hero-copy">
          <div className="hero-eyebrow"><span className="short-rule" /> YOUR NEXT PERSPECTIVE STARTS HERE</div>
          <h1 id="hero-title">Stay curious.<br /><em>Think ahead.</em><span className="title-asterisk" aria-hidden="true">✳</span></h1>
          <p>The ideas. The breakthroughs. The moments that matter.<br className="desktop-break" /> A clearer view of a world moving at the speed of AI.</p>
          <div className="hero-buttons"><a href="#the-edit" className="button button-orange">Explore the stories <ArrowUpRight size={18} /></a><Link to="/about" className="text-link">Meet CloudMind <ArrowRight size={17} /></Link></div>
          <div className="hero-footnote"><span className="mini-orbits" aria-hidden="true"><i /><i /><i /></span><span>A little more informed.<br /><strong>A lot more inspired.</strong></span></div>
        </div>
        <div className="hero-visual">
          <span className="visual-cross cross-one" aria-hidden="true">+</span><span className="visual-cross cross-two" aria-hidden="true">+</span>
          <div className="visual-coordinate">CM / INTELLIGENCE IN ORBIT</div>
          <IntelligenceGlobe paused={paused} />
          <div className="orbital-label label-ai"><span><Cpu size={17} /></span><div>Signals of tomorrow<small>ARTIFICIAL INTELLIGENCE</small></div><span className="tiny-dot" /></div>
          <div className="orbital-label label-connected"><Globe2 size={17} /><span>A world of possibilities</span><ArrowUpRight size={15} /></div>
          <div className="globe-caption"><span className="status-dot" /> A CONNECTED WORLD, A CURIOUS MIND</div>
          <button className="motion-toggle" onClick={() => setPaused(!paused)} aria-label={paused ? 'Play animations' : 'Pause animations'} aria-pressed={paused}>{paused ? <Play size={13} /> : <Pause size={13} />}<span>{paused ? 'Play motion' : 'Pause motion'}</span></button>
        </div>
      </div>
      <div className="hero-bottom"><span><Sparkles size={14} /> A FRESH PERSPECTIVE, EVERY DAY</span><a href="#the-edit">SCROLL TO DISCOVER <ArrowDown size={14} /></a></div>
    </section>

    <section className="topic-strip" aria-label="Explore our coverage">
      <div className="site-width topic-strip-inner"><span className="topic-strip-title">FOLLOW YOUR<br /><strong>CURIOSITY.</strong></span><button onClick={() => chooseTopic('AI')}><Cpu size={21} /><span>Artificial intelligence</span><ArrowUpRight size={16} /></button><button onClick={() => chooseTopic('Cricket')}><Trophy size={21} /><span>Beyond the boundary</span><ArrowUpRight size={16} /></button><button onClick={() => chooseTopic('Finance')}><TrendingUp size={21} /><span>Financial news</span><ArrowUpRight size={16} /></button></div>
    </section>

    <section className="news-section site-width" id="the-edit" aria-labelledby="edit-title" data-reveal>
      <div className="section-heading"><div><span className="section-kicker"><span /> THE CLOUDMIND EDIT</span><h2 id="edit-title">Worth your <em>attention.</em></h2></div><p>Fresh thinking. Real stories.<br />Your daily dose of perspective.</p></div>
      <div className="news-toolbar"><div className="topic-filters" role="group" aria-label="Filter stories by topic">{topics.map(([value, label]) => <button key={value} className={active === value ? 'is-active' : ''} aria-pressed={active === value} onClick={() => setActive(value)}>{label}{active === value && <span />}</button>)}</div><form className="news-search" role="search" onSubmit={e => { e.preventDefault(); setSearch(input.trim()) }}><input aria-label="Search stories" placeholder="Find your next read…" value={input} onChange={e => setInput(e.target.value)} /><button aria-label="Submit search" type="submit"><Search size={18} /></button></form></div>
      {search && <div className="search-summary" role="status">Results for “{search}”<button onClick={() => { setSearch(''); setInput('') }}>Clear search ×</button></div>}
      <NewsFeed key={`${active}:${search}`} active={active} search={search} clear={clear} />
    </section>

    <section className="perspective-section site-width" data-reveal><div className="perspective-card"><div className="perspective-art" aria-hidden="true"><div /><div /><div /><AudioLines size={62} strokeWidth={1} /></div><div className="perspective-copy"><span className="section-kicker">THE WORLD KEEPS MOVING. SO CAN YOU.</span><h2>Big ideas.<br /><em>Bigger possibilities.</em></h2><p>Discover opportunities at the intersection of technology and ambition. Your next chapter could start here.</p><Link className="button button-dark" to="/jobs">Explore careers <ArrowUpRight size={18} /></Link></div><span className="perspective-index" aria-hidden="true">THE NEXT CHAPTER ↗</span></div></section>
    <section className="community-section site-width" data-reveal><div><span className="section-kicker">GOOD IDEAS DESERVE GOOD COMPANY</span><h2>Keep your curiosity <em>close.</em></h2><p>More perspectives, conversations and discoveries. Find us where you scroll.</p></div><div className="community-links"><a className="button button-outline" href="https://www.instagram.com/thecloudmind.ai/" target="_blank" rel="noopener noreferrer">Instagram <ArrowUpRight size={17} /></a><a className="button button-orange" href="https://www.youtube.com/@CloudMindAI" target="_blank" rel="noopener noreferrer">YouTube <ArrowUpRight size={17} /></a></div></section>
  </div>
}
