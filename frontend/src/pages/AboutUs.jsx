import { Helmet } from 'react-helmet-async'
import { Link } from 'react-router-dom'
import { Target, Users, Zap, Brain, TrendingUp, ArrowRight } from 'lucide-react'
import logo from '../assets/logo.jpg'

const VALUES = [
  {
    icon: Brain,
    label: 'Expert Knowledge',
    color: 'teal',
    description: 'Deep understanding of AI technology and its implications for the future.',
  },
  {
    icon: TrendingUp,
    label: 'Latest Updates',
    color: 'blue',
    description: 'Timely coverage of breaking AI news and developments worldwide.',
  },
  {
    icon: Users,
    label: 'Community Focused',
    color: 'teal',
    description: 'Building a community of AI enthusiasts, researchers, and professionals.',
  },
  {
    icon: Zap,
    label: 'Innovation First',
    color: 'blue',
    description: 'Highlighting cutting-edge breakthroughs in artificial intelligence.',
  },
]

const COLOR = {
  teal: { bg: 'bg-teal-50', icon: 'text-teal-600', badge: 'bg-teal-600' },
  blue: { bg: 'bg-blue-50', icon: 'text-blue-600', badge: 'bg-blue-600' },
}

function AboutUs() {
  return (
    <>
      <Helmet>
        <title>About — TheCloudMind.ai</title>
        <meta
          name="description"
          content="Learn about TheCloudMind.ai — AI and sports coverage built from direct sources and rewritten for clarity."
        />
        <meta name="keywords" content="about TheCloudMind.ai, AI news platform, AI community" />
        <meta property="og:title" content="About — TheCloudMind.ai" />
        <meta
          property="og:description"
          content="Direct-source AI and sports coverage, rewritten into concise original analysis."
        />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://cloudmindai.in/about" />
        <meta name="twitter:card" content="summary_large_image" />
        <link rel="canonical" href="https://cloudmindai.in/about" />
      </Helmet>

      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 sm:py-14">

        {/* Hero */}
        <section className="mb-12 text-center">
          <img
            src={logo}
            alt="TheCloudMind.ai"
            className="mx-auto mb-5 h-24 w-24 rounded-[28px] object-cover shadow-[0_24px_80px_rgba(15,23,42,0.12)] ring-2 ring-white"
          />
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
            About us
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950 sm:text-5xl">
            TheCloudMind.ai
          </h1>
          <p className="font-editorial mx-auto mt-5 max-w-2xl text-xl leading-9 text-slate-600">
            Your trusted source for AI and sports news — direct from publishers, rewritten for
            clarity.
          </p>
        </section>

        {/* Mission */}
        <section className="mb-8">
          <div className="rounded-[32px] border border-slate-200 bg-white/90 p-7 shadow-[0_22px_65px_rgba(15,23,42,0.06)] sm:p-10">
            <div className="flex items-start gap-4">
              <div className="rounded-2xl bg-teal-50 p-3">
                <Target className="h-7 w-7 text-teal-600" />
              </div>
              <div>
                <h2 className="text-2xl font-bold tracking-tight text-slate-950">Our Mission</h2>
                <p className="font-editorial mt-3 text-lg leading-8 text-slate-600">
                  To democratize access to AI and sports knowledge by providing accurate,
                  timely, and insightful coverage. We pull directly from publishers, extract
                  the real story, and rewrite it into a cleaner editorial format — so you get
                  the information without the noise.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Values */}
        <section className="mb-8">
          <div className="mb-6">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
              What we stand for
            </p>
            <h2 className="mt-1 text-2xl font-bold tracking-tight text-slate-950">
              Built on four principles
            </h2>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {VALUES.map((v) => {
              const c = COLOR[v.color]
              const Icon = v.icon
              return (
                <div
                  key={v.label}
                  className="rounded-[28px] border border-slate-200/80 bg-white/90 p-6 shadow-[0_18px_55px_rgba(15,23,42,0.05)] transition hover:-translate-y-0.5 hover:shadow-[0_24px_65px_rgba(15,23,42,0.09)]"
                >
                  <div className={`w-fit rounded-2xl p-3 ${c.bg}`}>
                    <Icon className={`h-6 w-6 ${c.icon}`} />
                  </div>
                  <h3 className="mt-4 text-lg font-bold text-slate-950">{v.label}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{v.description}</p>
                </div>
              )
            })}
          </div>
        </section>

        {/* Story */}
        <section className="mb-8">
          <div className="rounded-[32px] border border-slate-200 bg-white/90 p-7 shadow-[0_22px_65px_rgba(15,23,42,0.06)] sm:p-10">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">
              Our story
            </p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950">
              How we got here
            </h2>
            <div className="font-editorial mt-5 space-y-5 text-lg leading-9 text-slate-600">
              <p>
                TheCloudMind.ai was created to make AI news simple and accessible for everyone.
                As AI started reshaping every industry, people needed a reliable source that
                explained developments clearly — without the jargon or the clickbait.
              </p>
              <p>
                We built an automated newsroom that pulls from direct publisher feeds, extracts
                article content, and rewrites each story with OpenAI into a structured, readable
                format. Whether you are an engineer, a founder, or just curious — we keep you
                informed about what matters in AI and sports.
              </p>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="rounded-[32px] bg-slate-950 p-8 text-center shadow-[0_24px_80px_rgba(15,23,42,0.14)] sm:p-12">
          <h2 className="text-2xl font-bold text-white sm:text-3xl">Stay in the loop</h2>
          <p className="mx-auto mt-3 max-w-md text-sm leading-7 text-slate-400">
            Follow us on YouTube and Instagram for daily briefs, highlights, and behind-the-scenes
            AI content.
          </p>
          <div className="mt-7 flex flex-wrap justify-center gap-4">
            <a
              href="https://www.youtube.com/@CloudMindAI"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-semibold text-slate-950 transition hover:bg-slate-100"
            >
              YouTube <ArrowRight className="h-4 w-4" />
            </a>
            <a
              href="https://www.instagram.com/thecloudmind.ai/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-full border border-white/20 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
            >
              Instagram <ArrowRight className="h-4 w-4" />
            </a>
            <Link
              to="/"
              className="inline-flex items-center gap-2 rounded-full border border-white/20 px-6 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
            >
              Read the news <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </section>

      </div>
    </>
  )
}

export default AboutUs
