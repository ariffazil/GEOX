/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        geox: {
          seal: "#22c55e",
          hold: "#f59e0b",
          void: "#ef4444",
          partial: "#3b82f6",
          bg: "#0f1117",
          panel: "#1a1f2e",
          border: "#2d3348",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};
