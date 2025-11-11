import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { DsaAuthManager, dsaAuthStore } from 'bdsa-react-components'
import config from '../config'
import nciLogo from '../assets/NCI-logo-300x165.jpg'
import './Layout.css'

function Layout({ children }) {
  const location = useLocation()
  const [activeTab, setActiveTab] = useState(location.pathname)
  const [authUser, setAuthUser] = useState(null)

  // Configure auth store with API URL on mount
  useEffect(() => {
    // Extract base URL from apiBaseUrl (remove /api/v1 if present)
    let baseUrl = config.apiBaseUrl
    if (baseUrl.endsWith('/api/v1')) {
      baseUrl = baseUrl.replace('/api/v1', '')
    } else if (baseUrl.endsWith('/api/v1/')) {
      baseUrl = baseUrl.replace('/api/v1/', '')
    }
    
    // Configure the auth store
    dsaAuthStore.updateConfig({ baseUrl })
    
    // Subscribe to auth changes
    const unsubscribe = dsaAuthStore.subscribe(() => {
      const status = dsaAuthStore.getStatus()
      setAuthUser(status.user?.name || null)
    })
    
    // Initial user check
    const status = dsaAuthStore.getStatus()
    setAuthUser(status.user?.name || null)

    return unsubscribe
  }, [])

  const tabs = [
    { path: '/slides', label: 'Slides For DeID' },
    { path: '/metadata', label: 'Slide Metadata' },
    { path: '/merged', label: 'Merged Data' },
    { path: '/instructions', label: 'Instructions' },
  ]

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <div className="header-title-section">
            <img src={nciLogo} alt="NCI Logo" className="nci-logo" />
            <h1>NCI DSA DeID</h1>
          </div>
          <nav className="tabs">
            {tabs.map((tab) => (
              <Link
                key={tab.path}
                to={tab.path}
                className={`tab ${location.pathname === tab.path ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.path)}
              >
                {tab.label}
              </Link>
            ))}
          </nav>
          <div className="auth-section">
            <DsaAuthManager compact={true} />
          </div>
        </div>
      </header>
      <main className="main-content">
        {children}
      </main>
    </div>
  )
}

export default Layout

