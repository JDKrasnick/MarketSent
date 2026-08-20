import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

/**
 * Vite Configuration for MarketSent Dashboard
 *
 * Development server runs on port 5173 by default.
 * Market data is loaded from public/data/marketsent.json.
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
  },

  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
