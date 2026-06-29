import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Forwards /api/* to the Flask backend during `npm run dev`, so the
      // browser sees same-origin requests (localhost:5173) and the
      // session/CSRF cookies behave exactly like they will in production
      // with no CORS configuration needed in dev.
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
})
