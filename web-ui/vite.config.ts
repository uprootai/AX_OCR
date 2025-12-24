/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    fs: {
      // Allow serving files from the parent docs folder via symlinks
      // Paths are relative to vite.config.ts (web-ui/)
      // '../docs' = /home/uproot/ax/poc/docs/
      allow: ['..', '../docs'],
      strict: false,
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // React 코어
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          // 차트
          'vendor-recharts': ['recharts'],
          // Mermaid (대형)
          'vendor-mermaid': ['mermaid'],
          // ReactFlow
          'vendor-flow': ['reactflow'],
          // 유틸리티
          'vendor-utils': ['axios', 'zustand', 'date-fns', 'i18next', 'react-i18next'],
          // Lucide 아이콘
          'vendor-icons': ['lucide-react'],
        },
      },
    },
    chunkSizeWarningLimit: 800,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
  },
})
