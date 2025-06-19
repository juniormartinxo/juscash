import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,
    allowedHosts: ['juscash.juniormartins.dev', "localhost:5173"],
    fs: {
      strict: false
    }
  },
  preview: {
    port: 5173,
    host: true,
    allowedHosts: ['juscash.juniormartins.dev', "localhost:5173"],
  },
  appType: 'spa',
  base: '/'
})