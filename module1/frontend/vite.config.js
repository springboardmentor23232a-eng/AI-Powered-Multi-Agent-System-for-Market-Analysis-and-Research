import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In dev, /api is proxied to FastAPI so the browser sees ONE origin (cookies + CSRF just work).
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { "/api": "http://localhost:8000" } },
  // Plotly's prebuilt bundle is only parseable by Vite's dev-server import analysis once minified.
  optimizeDeps: { include: ["plotly.js-finance-dist-min"], esbuildOptions: { minify: true } },
});
