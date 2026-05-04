import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/**
 * Proxy to FastAPI (default port 8000). Use 127.0.0.1 — not "localhost" —
 * so Node hits IPv4; uvicorn binds 127.0.0.1 and on Windows `localhost`
 * often resolves to ::1 first, causing ECONNREFUSED and broken /api calls.
 */
const proxyToApi = {
  '/api': {
    target: 'http://127.0.0.1:8000',
    changeOrigin: true,
  },
  '/uploads': {
    target: 'http://127.0.0.1:8000',
    changeOrigin: true,
  },
} as const

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: proxyToApi,
  },
  preview: {
    proxy: proxyToApi,
  },
})
