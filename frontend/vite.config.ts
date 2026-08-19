import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

/**
 * Vite Configuration for MarketSent Dashboard
 *
 * Development server runs on port 5173 by default
 * API proxy forwards /api requests to Flask backend on port 5000
 */
export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },

  server: {
    port: 5173,
    // Proxy API requests to Flask backend during development
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },

  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
