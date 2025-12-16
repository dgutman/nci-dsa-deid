import { useState, useEffect } from 'react'
import config from '../config'

/**
 * Custom UNA OAuth button component
 * Uses the same redirect URI as Girder's OAuth provider
 * No new redirect URI registration needed - reuses /dsa/api/v1/oauth/una/callback
 */
function UnaAuthButton({ className = '' }) {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    // Get the OAuth URL from Girder's provider endpoint
    const initiateUnaLogin = async () => {
        setLoading(true)
        setError(null)

        try {
            // Construct the redirect URL - where to return after OAuth
            const redirectUrl = window.location.origin + window.location.pathname

            // Get API URL from config (config now handles HTTPS/production detection)
            const apiUrl = config.apiBaseUrl

            // Ensure we have the full endpoint path
            const oauthProviderUrl = apiUrl.endsWith('/api/v1')
                ? `${apiUrl}/oauth/provider`
                : apiUrl.endsWith('/api/v1/')
                    ? `${apiUrl}oauth/provider`
                    : apiUrl.endsWith('/api')
                        ? `${apiUrl}/v1/oauth/provider`
                        : `${apiUrl}/api/v1/oauth/provider`

            // Query Girder's OAuth provider endpoint to get the UNA authorization URL
            // This uses the same redirect URI that's already registered: /dsa/api/v1/oauth/una/callback
            const response = await fetch(
                `${oauthProviderUrl}?redirect=${encodeURIComponent(redirectUrl)}&list=true`,
                {
                    credentials: 'include' // Include cookies for CORS
                }
            )

            if (!response.ok) {
                throw new Error(`Failed to get OAuth providers: ${response.statusText}`)
            }

            const providers = await response.json()

            // Find the UNA provider
            const unaProvider = providers.find(p =>
                p.id === 'una' ||
                p.name?.toLowerCase().includes('una') ||
                p.name?.toLowerCase().includes('nci-dmap')
            )

            if (!unaProvider) {
                throw new Error('UNA OAuth provider is not enabled in Girder. Please enable it in the OAuth plugin settings.')
            }

            // Redirect to UNA authorization URL
            // The URL already includes the correct redirect_uri pointing to Girder's callback
            window.location.href = unaProvider.url

        } catch (err) {
            console.error('UNA OAuth error:', err)
            setError(err.message || 'Failed to initiate UNA login')
            setLoading(false)
        }
    }

    // Check if we're returning from OAuth callback
    // DISABLED: This was causing refresh loops with history.replaceState
    // The girderToken handling in Layout.jsx will pick up the token instead
    // useEffect(() => {
    //   const urlParams = new URLSearchParams(window.location.search)
    //   const code = urlParams.get('code')
    //   const state = urlParams.get('state')
    //   const error = urlParams.get('error')

    //   if (error) {
    //     setError(`OAuth error: ${error}`)
    //     return
    //   }

    //   // If we have a code, we're being redirected back from OAuth
    //   // But since we're using Girder's callback, Girder should have already handled it
    //   // and set the session. We just need to refresh the auth state.
    //   if (code && state) {
    //     // The callback was handled by Girder, so we should already be authenticated
    //     // Just trigger a refresh of auth state
    //     if (onAuthSuccess) {
    //       onAuthSuccess()
    //     }
    //   }
    // }, [onAuthSuccess])

    return (
        <div className={`una-auth-button ${className}`}>
            <button
                onClick={initiateUnaLogin}
                disabled={loading}
                className="una-login-btn"
                style={{
                    padding: '8px 16px',
                    backgroundColor: '#0066cc',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    fontSize: '14px',
                    fontWeight: '500',
                    opacity: loading ? 0.6 : 1
                }}
            >
                {loading ? 'Connecting...' : 'Login with UNA'}
            </button>
            {error && (
                <div style={{
                    marginTop: '8px',
                    color: '#d32f2f',
                    fontSize: '12px'
                }}>
                    {error}
                </div>
            )}
        </div>
    )
}

export default UnaAuthButton

