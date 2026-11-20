import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const DJANGO = 'http://127.0.0.1:8000';

// Django serves the production build at /app/ (see backend/config/urls.py).
export default defineConfig({
  base: '/app/',
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
