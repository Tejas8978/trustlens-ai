import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  css: {
    // Force PostCSS transformer — Vite 8 defaults to lightningcss which uses
    // a native binary that crashes on Vercel's Linux build environment
    // (only the Windows binary is installed in node_modules).
    transformer: 'postcss',
  },
  build: {
    // Also disable CSS minification to avoid any lightningcss binary loading.
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
