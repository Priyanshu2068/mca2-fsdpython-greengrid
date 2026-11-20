import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const DJANGO = 'http://127.0.0.1:8000';

// Relative base allows the built React client to work seamlessly on both
// Vercel root (https://app.vercel.app/) and Django (/app/).
export default defineConfig({
  base: './',
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Same-origin session + CSRF auth: forward API calls to Django and present its own origin.
      '/api': { target: DJANGO, changeOrigin: true, headers: { Origin: DJANGO } },
    },
  },
  build: { outDir: 'dist', emptyOutDir: true },
});
