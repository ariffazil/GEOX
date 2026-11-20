import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig({
  plugins: [viteSingleFile()],
  build: {
    sourcemap: false,
    cssMinify: true,
    minify: true,
    outDir: "dist",
    emptyOutDir: true,
    rollupOptions: {
      input: "basin-panel.html",
    },
  },
});
