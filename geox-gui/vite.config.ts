import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/mcp": {
        target: "http://localhost:8100",
        changeOrigin: true,
      },
    },
  },
  define: {
    CESIUM_BASE_URL: JSON.stringify("/cesium"),
  },
});
