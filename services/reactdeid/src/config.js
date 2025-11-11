// Configuration for ReactDeID app
// In development, this points to a remote DSA instance
// In production (Docker), this uses the relative path which nginx proxies

const config = {
  // DSA API Base URL
  // For local dev: set to your remote DSA instance (e.g., 'http://bdsa.pathology.emory.edu:8080/api/v1')
  // For production: use relative path '/dsa/api/v1' which nginx will proxy
  apiBaseUrl: import.meta.env.VITE_DSA_API_URL || 
    (import.meta.env.DEV 
      ? 'http://bdsa.pathology.emory.edu:8080/api/v1'  // Default remote dev server
      : '/dsa/api/v1'  // Production uses nginx proxy
    ),
}

export default config

