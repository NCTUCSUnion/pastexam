import { defineConfig } from 'vite'
import { fileURLToPath, URL } from 'node:url'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'
import Components from 'unplugin-vue-components/vite'
import { PrimeVueResolver } from '@primevue/auto-import-resolver'
import eslintPlugin from 'vite-plugin-eslint'
import Sitemap from 'vite-plugin-sitemap'

export default defineConfig(({ mode }) => ({
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    host: true,
    port: 80,
    strictPort: true,
    hmr: { port: 24678, clientPort: 24678 },
  },
  plugins: [
    vue(),
    mode === 'development' && vueDevTools({ launchEditor: 'cursor' }),
    mode !== 'test' && eslintPlugin({ include: ['src/**/*.vue', 'src/**/*.js', 'src/**/*.ts'] }),
    tailwindcss(),
    Components({ resolvers: [PrimeVueResolver()] }),
    mode === 'production' &&
      Sitemap({
        hostname: 'https://pastexam.nctucsunion.me',
        dynamicRoutes: ['/archive', '/admin', '/login/callback'],
        changefreq: 'weekly',
        priority: 0.8,
        lastmod: new Date(),
        exclude: ['/login/callback', '/admin'],
        readable: true,
      }),
  ].filter(Boolean),
}))
