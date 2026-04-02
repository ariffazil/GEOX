import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import cesium from 'vite-plugin-cesium';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    cesium(), // For CesiumJS 3D globe
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // Proxy GEOX MCP requests in development
      '/geox': {
        target: 'https://geoxarifOS.fastmcp.app',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/geox/, ''),
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'maplibre': ['maplibre-gl'],
          'cesium': ['cesium'],
          'd3': ['d3'],
        },
      },
    },
  },
  optimizeDeps: {
    exclude: ['cesium'], // Cesium is handled by vite-plugin-cesium
  },
});