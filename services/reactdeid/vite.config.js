import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Use /deid/ base path for production (behind nginx), / for local dev
  // Can override with VITE_BASE_PATH env var
  const base = process.env.VITE_BASE_PATH || (mode === 'production' ? '/deid/' : '/')

  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      strictPort: true,
      // TEMPORARILY DISABLED: HMR was causing page refresh loops
      // Configure HMR WebSocket to work through nginx proxy
      // When running behind nginx (production-like setup), HMR needs to connect through the proxy
      hmr: false, // Disabled to debug refresh loop
      // Also disable HMR client connection attempts
      // This prevents the client from trying to connect to WebSocket
      // The client will still work, just without hot module replacement
      // Watch options to prevent false positives from file system events
      // In Docker with bind mounts, file system events can be unreliable and cause false positives
      watch: {
        // Aggressively ignore directories that might have changing files
        ignored: [
          '**/node_modules/**',
          '**/dist/**',
          '**/.vite/**',
          '**/.git/**',
          '**/logs/**',
          '**/*.log',
          '**/.DS_Store',
          '**/Thumbs.db',
          '**/package-lock.json',
          '**/.env*',
          '**/CURSOR_INTEGRATION.md', // Cursor might be updating this
          '**/API_ENDPOINTS.md',
        ],
        // In Docker, file system events from bind mounts can be unreliable
        // Polling is more reliable but uses more CPU
        // Try false first, if still having issues, set to true
        usePolling: false,
        // Only watch src directory explicitly to avoid watching everything
        // This prevents watching the entire mounted volume
        include: ['src/**'],
      },
      // hmr: process.env.VITE_HMR_HOST ? {
      //   host: process.env.VITE_HMR_HOST,
      //   protocol: 'wss', // Use WSS when behind nginx with HTTPS
      //   clientPort: 443, // nginx listens on 443 for HTTPS
      //   // Note: Vite HMR WebSocket path is automatically handled by nginx proxy
      //   // The path will be /deid/ which matches our base path
      // } : undefined, // Let Vite auto-detect in local dev
      // Proxy is only used if using relative /dsa path
      // If VITE_DSA_API_URL is set to a full URL, proxy won't be needed
      proxy: process.env.VITE_DSA_API_URL?.startsWith('/') ? {
        '/dsa': {
          target: process.env.VITE_DSA_PROXY_TARGET || 'http://localhost:8080',
          changeOrigin: true,
          secure: false,
        },
      } : undefined,
    },
    base,
    build: {
      outDir: 'dist',
      sourcemap: true,
    },
  }
})

