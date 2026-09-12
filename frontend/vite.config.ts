import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  base: './',
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/health': 'http://127.0.0.1:8000',
      '/transactions': 'http://127.0.0.1:8000',
      '/analytics': 'http://127.0.0.1:8000',
      '/alerts': 'http://127.0.0.1:8000',
      '/reviews': 'http://127.0.0.1:8000',
      '/otp': 'http://127.0.0.1:8000',
      '/simulator': 'http://127.0.0.1:8000',
      '/search': 'http://127.0.0.1:8000',
      '/users': 'http://127.0.0.1:8000',
      '/metrics': 'http://127.0.0.1:8000',
    },
  },
})
