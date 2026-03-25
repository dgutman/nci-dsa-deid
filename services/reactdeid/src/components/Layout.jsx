import { useState, useEffect, useRef } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { dsaAuthStore } from 'bdsa-react-components'
import config from '../config'
import nciLogo from '../assets/NCI-logo-300x165.jpg'
import UnaAuthButton from './UnaAuthButton'
import SimpleLogin from './SimpleLogin'
import './Layout.css'

function Layout({ children }) {
  const location = useLocation()
  const [activeTab, setActiveTab] = useState(location.pathname)
  const [authUser, setAuthUser] = useState(null)
  const tokenProcessedRef = useRef(false) // Track if we've already processed the token

  // Configure auth store and handle OAuth token on mount
  useEffect(() => {
    // Configure the store
    let baseUrl = config.apiBaseUrl
    if (baseUrl.endsWith('/api/v1')) {
      baseUrl = baseUrl.replace('/api/v1', '')
    } else if (baseUrl.endsWith('/api/v1/')) {
      baseUrl = baseUrl.replace('/api/v1/', '')
    }

    dsaAuthStore.updateConfig({ baseUrl })

    // Subscribe to auth store changes to keep authUser in sync
    const unsubscribe = dsaAuthStore.subscribe((status) => {
      // Add null/undefined check to prevent errors
      if (!status) {
        return
      }
      if (status.isAuthenticated && status.user) {
        setAuthUser(status.user.name || status.user.login || 'User')
      } else if (!status.isAuthenticated) {
        setAuthUser(null)
      }
    })

    // Initial check of auth status
    const initialStatus = dsaAuthStore.getStatus()
    if (initialStatus.isAuthenticated && initialStatus.user) {
      setAuthUser(initialStatus.user.name || initialStatus.user.login || 'User')
    }

    // Handle girderToken from OAuth redirect (only once)
    if (tokenProcessedRef.current) {
      return // Already processed, don't run again
    }

    const urlParams = new URLSearchParams(window.location.search)
    const girderToken = urlParams.get('girderToken') || urlParams.get('token')

    if (girderToken) {
      tokenProcessedRef.current = true // Mark as processed immediately

      // Token found in URL, processing...

      // Store token in localStorage
      localStorage.setItem('girderToken', girderToken)

      // Verify token and get user info
      const verifyToken = async () => {
        try {
          const response = await fetch(`${baseUrl}/api/v1/user/me`, {
            headers: {
              'Girder-Token': girderToken
            },
            credentials: 'include'
          })

          if (response.ok) {
            const user = await response.json()
            // Token verified successfully
            setAuthUser(user.login || user.name || 'User')

            // The store has properties: token, userInfo, isAuthenticated
            // Try to set them directly and trigger updates
            try {
              // Try authenticateWithToken method first if it exists (preferred)
              if (dsaAuthStore.authenticateWithToken && typeof dsaAuthStore.authenticateWithToken === 'function') {
                dsaAuthStore.authenticateWithToken(girderToken, user)
              } else {
                // Fallback: Set properties directly
                if ('token' in dsaAuthStore) {
                  dsaAuthStore.token = girderToken
                }
                if ('userInfo' in dsaAuthStore) {
                  dsaAuthStore.userInfo = user
                }
                if ('isAuthenticated' in dsaAuthStore) {
                  dsaAuthStore.isAuthenticated = true
                }
                if (dsaAuthStore.setToken && typeof dsaAuthStore.setToken === 'function') {
                  dsaAuthStore.setToken(girderToken)
                }
                if (dsaAuthStore.notify && typeof dsaAuthStore.notify === 'function') {
                  dsaAuthStore.notify()
                }
                if (dsaAuthStore.update && typeof dsaAuthStore.update === 'function') {
                  dsaAuthStore.update()
                }
              }
            } catch (e) {
              console.error('Error setting store properties:', e)
            }
          } else {
            console.error('Token verification failed:', response.statusText)
            localStorage.removeItem('girderToken')
            setAuthUser(null)
          }
        } catch (err) {
          console.error('Error verifying token:', err)
          localStorage.removeItem('girderToken')
          setAuthUser(null)
        }
      }

      verifyToken()

      // Clean up URL (remove token parameter) - do this after a small delay
      // to ensure state is set, but use replaceState which doesn't trigger navigation
      setTimeout(() => {
        const cleanUrl = window.location.pathname + (window.location.hash || '')
        window.history.replaceState({}, document.title, cleanUrl)
      }, 100)
    } else {
      // No token in URL, check if we have one in localStorage
      const storedToken = localStorage.getItem('girderToken')
      if (storedToken) {
        tokenProcessedRef.current = true
        // Verify existing token
        const verifyToken = async () => {
          try {
            const response = await fetch(`${baseUrl}/api/v1/user/me`, {
              headers: {
                'Girder-Token': storedToken
              },
              credentials: 'include'
            })

            if (response.ok) {
              const user = await response.json()
              setAuthUser(user.login || user.name || 'User')

              // Set store properties directly
              try {
                if ('token' in dsaAuthStore) {
                  dsaAuthStore.token = storedToken
                }
                if ('userInfo' in dsaAuthStore) {
                  dsaAuthStore.userInfo = user
                }
                if ('isAuthenticated' in dsaAuthStore) {
                  dsaAuthStore.isAuthenticated = true
                }

                // Try methods if they exist
                if (dsaAuthStore.setToken && typeof dsaAuthStore.setToken === 'function') {
                  dsaAuthStore.setToken(storedToken)
                }
                if (dsaAuthStore.authenticateWithToken && typeof dsaAuthStore.authenticateWithToken === 'function') {
                  dsaAuthStore.authenticateWithToken(storedToken, user)
                }
                if (dsaAuthStore.checkAuth && typeof dsaAuthStore.checkAuth === 'function') {
                  dsaAuthStore.checkAuth()
                }
              } catch (e) {
                console.error('Error setting store properties for stored token:', e)
              }
            } else {
              // Token invalid, remove it
              localStorage.removeItem('girderToken')
              setAuthUser(null)
            }
          } catch (err) {
            console.error('Error verifying stored token:', err)
            localStorage.removeItem('girderToken')
            setAuthUser(null)
          }
        }
        verifyToken()
      }
    }

    // Cleanup subscription on unmount
    return () => {
      unsubscribe()
    }
  }, []) // Empty deps - only run once on mount

  // Routes are relative - React Router will prepend basename (/deid in production)
  // So /slides becomes /deid/slides automatically
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
            {authUser ? (
              // Show user info and logout when authenticated
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span style={{ color: '#666', fontSize: '0.9rem' }}>{authUser}</span>
                <button
                  onClick={async () => {
                    try {
                      // Get base URL for logout
                      let baseUrl = config.apiBaseUrl
                      if (baseUrl.endsWith('/api/v1')) {
                        baseUrl = baseUrl.replace('/api/v1', '')
                      } else if (baseUrl.endsWith('/api/v1/')) {
                        baseUrl = baseUrl.replace('/api/v1/', '')
                      }

                      // Get token for logout request
                      const token = localStorage.getItem('girderToken')

                      // Call Girder logout endpoint
                      // For OAuth tokens, we need to include the token in the request
                      const headers = {
                        'Content-Type': 'application/json',
                      }
                      if (token) {
                        headers['Girder-Token'] = token
                      }

                      try {
                        await fetch(`${baseUrl}/api/v1/user/authentication`, {
                          method: 'DELETE',
                          headers: headers,
                          credentials: 'include'
                        })
                      } catch (fetchErr) {
                        // Even if the API call fails, we should still clear local state
                        console.warn('Logout API call failed, clearing local state anyway:', fetchErr)
                      }

                      // Clear auth state (always do this, even if API call failed)
                      dsaAuthStore.logout()
                      setAuthUser(null)
                      localStorage.removeItem('girderToken')

                      // For OAuth, we might want to redirect to OAuth provider's logout
                      // but that's usually optional - clearing the token is sufficient
                      // If needed, we could redirect to: https://auth.ncats.nih.gov/logout

                      // No reload needed - state update will refresh UI
                    } catch (err) {
                      console.error('Logout error:', err)
                      // Still try to clear local state
                      dsaAuthStore.logout()
                      setAuthUser(null)
                      localStorage.removeItem('girderToken')
                      // No reload - just clear state
                    }
                  }}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: '#dc3545',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                    fontWeight: '500'
                  }}
                >
                  Logout
                </button>
              </div>
            ) : (
              // Show UNA and local login when not authenticated
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <UnaAuthButton />
                <span style={{ color: '#999', fontSize: '0.85rem' }}>or</span>
                <SimpleLogin onLoginSuccess={(user) => {
                  setAuthUser(user.login || user.name || 'User')
                }} />
              </div>
            )}
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

