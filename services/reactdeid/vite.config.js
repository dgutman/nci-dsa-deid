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

