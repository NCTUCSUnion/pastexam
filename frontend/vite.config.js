import { defineConfig, loadEnv } from 'vite'
import { fileURLToPath, URL } from 'node:url'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'
import Components from 'unplugin-vue-components/vite'
import { PrimeVueResolver } from '@primevue/auto-import-resolver'
import Sitemap from 'vite-plugin-sitemap'
import { compression } from 'vite-plugin-compression2'

export default defineConfig(({ mode }) => {
  const root = fileURLToPath(new URL('.', import.meta.url))
  const env = loadEnv(mode, root, '')
  const siteHostname = env.VITE_SITE_HOSTNAME?.trim()

  return {
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },
    server: {
      host: true,
      port: 80,
      strictPort: true,
      hmr: { port: 24678, clientPort: 24678 },
    },
    build: {
      cssCodeSplit: true,
      chunkSizeWarningLimit: 600,
      // Emit maps for debugging without referencing them from the served bundles
      sourcemap: 'hidden',
      rolldownOptions: {
        treeshake:
          mode === 'production' ? { manualPureFunctions: ['console.log', 'console.debug'] } : {},
      },
    },
    plugins: [
      vue(),
      mode === 'development' && vueDevTools({ launchEditor: 'zed' }),
      tailwindcss(),
      // Only auto-import PrimeVue; local components are imported explicitly so they can be lazy loaded
      Components({ dirs: [], resolvers: [PrimeVueResolver()] }),
      mode === 'production' &&
        siteHostname &&
        Sitemap({
          hostname: siteHostname,
          dynamicRoutes: ['/archive', '/admin', '/login/callback'],
          changefreq: 'weekly',
          priority: 0.8,
          lastmod: new Date(),
          exclude: ['/login/callback', '/admin'],
          readable: true,
        }),
      mode === 'production' &&
        // nginx:alpine only ships gzip_static, so precompress with gzip only
        compression({
          algorithms: ['gzip'],
          threshold: 10240,
          deleteOriginalAssets: false,
        }),
    ].filter(Boolean),
  }
})
