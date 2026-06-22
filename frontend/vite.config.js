import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://backend_api:8000',
        changeOrigin: true,
        secure: false,
      },
      '^/ws/.*': {
        target: 'http://backend_api:8000',
        ws: true,
        changeOrigin: true,
        rewrite: (path) => path,
      },
      '^/whep/.*': {
        target: 'http://mediamtx:8889',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/whep/, ''),
      }
    }
  }
})