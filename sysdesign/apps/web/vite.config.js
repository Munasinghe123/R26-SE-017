import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],

  server: {
    port: 5173,
    proxy: {
      // Orchestrator (pipeline jobs, SSE stream)
      '/jobs': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      // Auth routes (register / login)
      '/register':     { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/login':        { target: 'http://127.0.0.1:8001', changeOrigin: true },
      // Agent 1 — Requirements Intelligence (all original routes)
      '/requirements/': { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/refine-reqs':  { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/approve-reqs': { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/projects':             { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/auth':                 { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/extract-requirements': { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/users':                { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/livekit':              { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/test/':                 { target: 'http://127.0.0.1:8001', changeOrigin: true },
    },
  },

  // Expose env vars to the frontend (VITE_ prefix)
  // These are read from the root .env file
  envDir: '../../',   // ← repo root where .env lives
})
