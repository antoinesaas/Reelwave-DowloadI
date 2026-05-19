import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          three:  ['three', '@react-three/fiber', '@react-three/drei'],
          motion: ['framer-motion'],
          react:  ['react', 'react-dom'],
        },
      },
    },
    chunkSizeWarningLimit: 700,
  },
})
