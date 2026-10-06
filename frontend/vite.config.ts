import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      // 开发环境代理到 FastAPI，规避跨域
      '/api': 'http://localhost:8000',
    },
  },
})
