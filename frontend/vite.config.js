import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'
import Components from 'unplugin-vue-components/vite'
import { PrimeVueResolver } from '@primevue/auto-import-resolver'
import eslintPlugin from 'vite-plugin-eslint'
import Sitemap from 'vite-plugin-sitemap'

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    host: true,
    port: 80,
    strictPort: true,
    hmr: {
      port: 24678,
      clientPort: 24678,
    },
  },
  plugins: [
    vue(),
    vueDevTools({
      launchEditor: 'cursor',
    }),
    eslintPlugin({
      include: ['src/**/*.vue', 'src/**/*.js', 'src/**/*.ts'],
    }),
    tailwindcss(),
    Components({
      resolvers: [PrimeVueResolver()],
    }),
    Sitemap({
      hostname: 'https://pastexam.nctucsunion.me',
      dynamicRoutes: ['/archive', '/admin', '/login/callback'],
      changefreq: 'weekly',
      priority: 0.8,
      lastmod: new Date(),
      exclude: ['/login/callback', '/admin'],
      readable: true,
    }),
  ],
})
