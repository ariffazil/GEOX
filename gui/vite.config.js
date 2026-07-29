import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/gui/',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/mcp': {
        target: 'http://127.0.0.1:8081',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8081',
        changeOrigin: true,
      },
    },
  },
})
