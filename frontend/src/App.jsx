import { lazy, Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import Footer from './components/Footer'
import ChatWidget from './components/ChatWidget'
import Home from './pages/Home'

// Route-level code splitting: only the homepage ships in the main bundle.
// Every other page (and heavy deps like marked/DOMPurify used by Article and
// JobDetail) is fetched on demand when the route is first visited.
const Article = lazy(() => import('./pages/Article'))
const LatestNews = lazy(() => import('./pages/LatestNews'))
const Jobs = lazy(() => import('./pages/Jobs'))
const JobDetail = lazy(() => import('./pages/JobDetail'))
const AdminLogin = lazy(() => import('./pages/AdminLogin'))
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'))
const AdminJobs = lazy(() => import('./pages/AdminJobs'))
const ContactUs = lazy(() => import('./pages/ContactUs'))
const AboutUs = lazy(() => import('./pages/AboutUs'))

function PageFallback() {
  return <div style={{ minHeight: '60vh' }} aria-busy="true" />
}

function App() {
  return (
    <div style={{ minHeight: '100vh', background: 'var(--cm-bg)', display: 'flex', flexDirection: 'column' }}>
      <Header />
      <main className="flex-grow">
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route path="/" element={<Home />} />
            {/* Canonical dated article path */}
            <Route path="/news/:year/:month/:slug" element={<Article />} />
            {/* Legacy — redirects to the dated path */}
            <Route path="/article/:slug" element={<Article />} />
            <Route path="/latest-news" element={<LatestNews />} />
            <Route path="/jobs" element={<Jobs />} />
            {/* Canonical dated job path */}
            <Route path="/jobs/:year/:month/:slug" element={<JobDetail />} />
            {/* Legacy — redirects to the dated path */}
            <Route path="/jobs/:slug" element={<JobDetail />} />
            <Route path="/contact" element={<ContactUs />} />
            <Route path="/about" element={<AboutUs />} />
            <Route path="/admin/login" element={<AdminLogin />} />
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/admin/jobs" element={<AdminJobs />} />
          </Routes>
        </Suspense>
      </main>
      <Footer />
      <ChatWidget />
    </div>
  )
}

export default App
