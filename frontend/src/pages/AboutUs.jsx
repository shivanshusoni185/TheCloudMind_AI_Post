import { Helmet } from 'react-helmet-async'
import { Target, Users, Zap, Brain, TrendingUp } from 'lucide-react'
import logo from '../assets/logo.jpg'

const values = [
  { icon: Brain, title: 'Expert Knowledge', description: 'Deep understanding of AI technology and its implications for the future.' },
  { icon: TrendingUp, title: 'Latest Updates', description: 'Timely coverage of breaking AI news and developments worldwide.' },
  { icon: Users, title: 'Community Focused', description: 'Building a community of AI enthusiasts, researchers, and professionals.' },
  { icon: Zap, title: 'Innovation', description: 'Highlighting cutting-edge innovations and breakthroughs in artificial intelligence.' },
]

function AboutUs() {
  return (
    <>
      <Helmet>
        <title>About Us - TheCloudMind.ai | Our Mission & Story</title>
        <meta name="description" content="Learn about TheCloudMind.ai - democratizing AI knowledge through expert coverage of artificial intelligence news, machine learning developments, and GenAI innovations." />
        <meta name="keywords" content="about TheCloudMind.ai, AI news platform, AI community, AI knowledge, artificial intelligence insights" />
        <meta property="og:title" content="About Us - TheCloudMind.ai" />
        <meta property="og:description" content="Democratizing AI knowledge through expert coverage and insights for everyone from beginners to experts." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://cloudmindai.in/about" />
        <meta name="twitter:card" content="summary_large_image" />
        <link rel="canonical" href="https://cloudmindai.in/about" />
      </Helmet>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
        {/* Hero */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-20">
          <div className="max-w-7xl mx-auto px-4 text-center">
            <div className="flex justify-center mb-6">
              <img src={logo} alt="TheCloudMind.ai" className="h-32 w-32 rounded-full object-cover shadow-2xl ring-4 ring-white/30" />
            </div>
            <h1 className="text-5xl md:text-6xl font-bold mb-6">About TheCloudMind.ai</h1>
            <p className="text-xl md:text-2xl max-w-3xl mx-auto opacity-90">
              Your trusted source for AI news, insights, and innovations
            </p>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 py-16">
          {/* Mission */}
          <div className="max-w-4xl mx-auto mb-16">
            <div className="bg-white rounded-2xl shadow-lg p-8">
              <div className="flex items-center gap-4 mb-4">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Target className="w-8 h-8 text-blue-600" />
                </div>
                <h2 className="text-3xl font-bold text-gray-900">Our Mission</h2>
              </div>
              <p className="text-gray-600 text-lg leading-relaxed">
                To democratize access to artificial intelligence knowledge by providing accurate,
                timely, and insightful news coverage. We strive to make AI developments
                understandable and accessible to everyone, from beginners to experts.
              </p>
            </div>
          </div>

          {/* Values */}
          <div className="mb-16">
            <h2 className="text-4xl font-bold text-center mb-4">
              <span className="bg-gradient-to-r from-cyan-500 via-blue-600 to-purple-600 bg-clip-text text-transparent">
                What We Do
              </span>
            </h2>
            <p className="text-xl text-gray-600 text-center max-w-3xl mx-auto mb-12">
              We curate, analyze, and deliver the most important AI news and developments from around the world
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {values.map((value, index) => (
                <div key={index} className="bg-white rounded-xl shadow-md p-6 hover:shadow-xl transition-shadow">
                  <div className="p-3 bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg w-fit mb-4">
                    <value.icon className="w-8 h-8 text-blue-600" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">{value.title}</h3>
                  <p className="text-gray-600">{value.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Story */}
          <div className="bg-white rounded-2xl shadow-lg p-8 md:p-12">
            <h2 className="text-4xl font-bold text-center mb-8">
              <span className="bg-gradient-to-r from-cyan-500 via-blue-600 to-purple-600 bg-clip-text text-transparent">
                Our Story
              </span>
            </h2>
            <div className="max-w-3xl mx-auto text-center">
              <p className="text-xl text-gray-600 leading-relaxed mb-6">
                TheCloudMind.ai was created to make AI news simple and accessible for everyone.
                We saw that AI is changing the world fast, and people needed a reliable source to stay updated.
              </p>
              <p className="text-xl text-gray-600 leading-relaxed">
                Our team loves AI and technology. We bring you the latest AI news, breakthroughs,
                and insights in a way that's easy to understand. Whether you're an expert or just
                getting started, we're here to keep you informed about the future of AI.
              </p>
            </div>
          </div>

          {/* CTA */}
          <div className="mt-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl shadow-xl p-8 md:p-12 text-white text-center">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Join Our Community</h2>
            <p className="text-xl mb-8 opacity-90">Stay updated with the latest AI news and insights. Follow us on social media!</p>
            <div className="flex justify-center gap-4">
              <a href="https://www.youtube.com/@CloudMindAI" target="_blank" rel="noopener noreferrer" className="px-8 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-gray-100 transition-colors">YouTube</a>
              <a href="https://www.instagram.com/thecloudmind.ai/" target="_blank" rel="noopener noreferrer" className="px-8 py-3 bg-white text-purple-600 rounded-lg font-semibold hover:bg-gray-100 transition-colors">Instagram</a>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

export default AboutUs
