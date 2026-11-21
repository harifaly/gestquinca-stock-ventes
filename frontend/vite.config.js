import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Le port 5173 est celui autorisé par l'API (CORS_ORIGINS dans backend/.env).
export default defineConfig({
  plugins: [vue()],
  server: { port: 5173, strictPort: true },
})
