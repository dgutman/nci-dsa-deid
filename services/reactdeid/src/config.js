// Configuration for ReactDeID app
// In development, this points to a remote DSA instance
// In production (Docker), this uses the relative path which nginx proxies

const config = {
  // DSA API Base URL
  // For local dev: set to your remote DSA instance (e.g., 'http://bdsa.pathology.emory.edu:8080/api/v1')
  // For production: use relative path '/dsa/api/v1' which nginx will proxy
  get apiBaseUrl() {
    // If we're running in the browser on HTTPS (production), always use relative path
    // This ensures nginx can proxy the request, avoiding mixed content errors
    if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
      return '/dsa/api/v1'
    }
    
    // Check environment variable
    const envUrl = import.meta.env.VITE_DSA_API_URL
    
    // If env var is set but it's an internal Docker URL (http://girder:8080 or similar),
    // and we're in the browser, use relative path instead
    if (envUrl && typeof window !== 'undefined') {
      if (envUrl.startsWith('http://') && 
          (envUrl.includes('girder') || envUrl.includes('docker-') || envUrl.includes(':8080'))) {
        // Internal Docker URL - use relative path so nginx can proxy
        return '/dsa/api/v1'
      }
    }
    
    // Use env var if set, otherwise use defaults
    return envUrl || 
      (import.meta.env.DEV 
        ? 'http://bdsa.pathology.emory.edu:8080/api/v1'  // Default remote dev server
        : '/dsa/api/v1'  // Production uses nginx proxy
      )
  },

  /**
   * Base URL for the DSA web client (hash routes like #item/ID), e.g. /dsa or https://host/dsa.
   * Derived from apiBaseUrl so "View in DSA" matches the API you are using (no hardcoded host).
   */
  get dsaWebBaseUrl() {
    const api = this.apiBaseUrl
    if (!api) return '/dsa'
    if (api.startsWith('/')) {
      return api.replace(/\/api\/v1\/?$/, '') || '/dsa'
    }
    try {
      const u = new URL(api, typeof window !== 'undefined' ? window.location.href : 'http://localhost')
      return `${u.origin}/dsa`
    } catch {
      return '/dsa'
    }
  }
}

export default config

