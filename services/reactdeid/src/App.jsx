import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import SlidesForDeID from './pages/SlidesForDeID'
import SlideMetadata from './pages/SlideMetadata'
import MergedData from './pages/MergedData'
import Instructions from './pages/Instructions'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/slides" element={<SlidesForDeID />} />
        <Route path="/metadata" element={<SlideMetadata />} />
        <Route path="/merged" element={<MergedData />} />
        <Route path="/instructions" element={<Instructions />} />
      </Routes>
    </Layout>
  )
}

export default App

