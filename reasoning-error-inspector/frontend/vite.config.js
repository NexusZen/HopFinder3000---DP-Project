import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Build output is consumed directly by the FastAPI backend (backend/main.py),
// which serves ../dist as static files and falls back to dist/index.html.
export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
