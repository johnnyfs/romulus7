import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '..', ['BACKEND_'])
  const backendPort = env.BACKEND_PORT || '8000'
  const backendOrigin = env.BACKEND_ORIGIN || 'http://localhost'

  return {
    plugins: [react()],
    server: {
      proxy: {
        '/api': {
          target: `${backendOrigin}:${backendPort}`,
          changeOrigin: true,
        },
      },
    },
  }
})
