import { Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import Footer from './components/Footer'
import ChatWidget from './components/ChatWidget'
import Home from './pages/Home'
import Article from './pages/Article'
import LatestNews from './pages/LatestNews'
import Jobs from './pages/Jobs'
import JobDetail from './pages/JobDetail'
import AdminLogin from './pages/AdminLogin'
import AdminDashboard from './pages/AdminDashboard'
import AdminJobs from './pages/AdminJobs'
import ContactUs from './pages/ContactUs'
import AboutUs from './pages/AboutUs'

function App() {
  return (
    <div style={{ minHeight: '100vh', background: 'var(--cm-bg)', display: 'flex', flexDirection: 'column' }}>
      <Header />
      <main className="flex-grow">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/article/:slug" element={<Article />} />
          <Route path="/latest-news" element={<LatestNews />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/jobs/:slug" element={<JobDetail />} />
          <Route path="/contact" element={<ContactUs />} />
          <Route path="/about" element={<AboutUs />} />
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/jobs" element={<AdminJobs />} />
        </Routes>
      </main>
      <Footer />
      <ChatWidget />
    </div>
  )
}

export default App
