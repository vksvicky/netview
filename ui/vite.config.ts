import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5170,
    host: true
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts']
  }
})


