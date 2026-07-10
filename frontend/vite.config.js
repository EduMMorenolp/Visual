import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    port: 8080,
    proxy: {
      '/comfy': {
        target: 'http://localhost:8188',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/comfy/, ''),
      },
      '/ws': {
        target: 'ws://localhost:8188',
        ws: true,
      },
    },
  },
})
