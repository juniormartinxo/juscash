import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'

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
    allowedHosts: ['juscash.juniormartins.dev'],
    // Importante: configurar para não interferir com o proxy reverso
    fs: {
      strict: false
    }
  },
  preview: {
    port: 5173,
    host: true,
    allowedHosts: ['juscash.juniormartins.dev'],
  },
  // Configurar para SPA mas não interceptar /api
  appType: 'spa',
  base: '/'
})