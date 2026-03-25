import { useState } from 'react'
import config from '../config'
import { dsaAuthStore } from 'bdsa-react-components'

/**
 * Simple login component that uses config.apiBaseUrl automatically
 * No server URL field needed - it's all configured via environment variables
 */
function SimpleLogin({ onLoginSuccess }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      // Get API URL from config (respects environment variables)
      const apiUrl = config.apiBaseUrl
      
      // Ensure we have the full endpoint path
      const authEndpoint = apiUrl.endsWith('/api/v1')
        ? `${apiUrl}/user/authentication`
        : apiUrl.endsWith('/api/v1/')
          ? `${apiUrl}user/authentication`
          : `${apiUrl}/api/v1/user/authentication`

      // Basic auth login to Girder
      const response = await fetch(authEndpoint, {
        method: 'GET',
        headers: {
          'Authorization': 'Basic ' + btoa(`${username}:${password}`)
        },
        credentials: 'include'
      })

      if (!response.ok) {
        throw new Error('Invalid username or password')
      }

      const data = await response.json()
      
      // Store token
      const token = data.authToken?.token || data.token
      if (token) {
        localStorage.setItem('girderToken', token)
        
        // Update auth store
        try {
          if (dsaAuthStore.authenticateWithToken) {
            dsaAuthStore.authenticateWithToken(token, data.user)
          } else {
            if ('token' in dsaAuthStore) {
              dsaAuthStore.token = token
            }
            if ('userInfo' in dsaAuthStore) {
              dsaAuthStore.userInfo = data.user
            }
            if ('isAuthenticated' in dsaAuthStore) {
              dsaAuthStore.isAuthenticated = true
            }
            if (dsaAuthStore.setToken) {
              dsaAuthStore.setToken(token)
            }
            if (dsaAuthStore.notify) {
              dsaAuthStore.notify()
            }
          }
        } catch (e) {
          console.error('Error updating auth store:', e)
        }

        if (onLoginSuccess) {
          onLoginSuccess(data.user)
        }
      }
    } catch (err) {
      console.error('Login error:', err)
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleLogin} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        disabled={loading}
        style={{
          padding: '6px 10px',
          border: '1px solid #ddd',
          borderRadius: '4px',
          fontSize: '13px',
          width: '120px'
        }}
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        disabled={loading}
        style={{
          padding: '6px 10px',
          border: '1px solid #ddd',
          borderRadius: '4px',
          fontSize: '13px',
          width: '120px'
        }}
      />
      <button
        type="submit"
        disabled={loading || !username || !password}
        style={{
          padding: '6px 12px',
          backgroundColor: loading ? '#999' : '#28a745',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: loading || !username || !password ? 'not-allowed' : 'pointer',
          fontSize: '13px',
          fontWeight: '500'
        }}
      >
        {loading ? 'Logging in...' : 'Login'}
      </button>
      {error && (
        <span style={{ color: '#dc3545', fontSize: '12px', marginLeft: '0.5rem' }}>
          {error}
        </span>
      )}
    </form>
  )
}

export default SimpleLogin
