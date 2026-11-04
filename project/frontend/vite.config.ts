import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// 后端地址可由环境变量覆盖，避免"手动起 8765"与"start.py 起 8000"两套端口
// 错配导致前端 /api 请求打到死端口而表现为超时（见 ISSUES #17）。
// 默认 http://localhost:8000 与 start.py 的 --port 8000 一致；
// 若手动用其它端口起后端，在 frontend/.env 设 VITE_API_TARGET 即可。
const apiTarget = process.env.VITE_API_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
        // SSE 长连接：compiler 单跑 ~100s、全 DAG 3-4 分钟。
        timeout: 600000,
        proxyTimeout: 0,
      },
    },
  },
})
