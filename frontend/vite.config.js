import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发服务器 5173，/api 反向代理到 Spring Boot 8080，规避跨域
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    chunkSizeWarningLimit: 1500
  }
})
