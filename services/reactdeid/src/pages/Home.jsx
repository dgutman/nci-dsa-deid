import { Navigate } from 'react-router-dom'

function Home() {
  // Simple redirect - Navigate with replace prevents adding to history
  return <Navigate to="/slides" replace />
}

export default Home

