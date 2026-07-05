import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    // Disable CSS minification — Vite 8 uses lightningcss by default,
    // but the Linux binary is not installed. Setting false avoids the crash.
    cssMinify: false,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
