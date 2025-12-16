import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import 'bdsa-react-components/styles.css'
import './index.css'

// Use VITE_BASE_PATH if set, otherwise /deid for production, / for local dev
// VITE_BASE_PATH is set to /deid/ in docker-compose, so we need to remove trailing slash
const basename = import.meta.env.VITE_BASE_PATH
  ? import.meta.env.VITE_BASE_PATH.replace(/\/$/, '') // Remove trailing slash
  : (import.meta.env.PROD ? '/deid' : '/')

ReactDOM.createRoot(document.getElementById('root')).render(
  // StrictMode temporarily disabled - was causing double renders/refresh loops
  <BrowserRouter basename={basename}>
    <App />
  </BrowserRouter>
)

