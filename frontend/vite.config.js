import { defineConfig, loadEnv } from 'vite'
import { fileURLToPath, URL } from 'node:url'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'
import Components from 'unplugin-vue-components/vite'
import { PrimeVueResolver } from '@primevue/auto-import-resolver'
import eslintPlugin from 'vite-plugin-eslint'
import Sitemap from 'vite-plugin-sitemap'
import viteCompression from 'vite-plugin-compression'

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
      sourcemap: true,
      minify: 'esbuild',
      esbuildOptions: {
        drop: mode === 'production' ? ['debugger'] : [],
        pure: mode === 'production' ? ['console.log', 'console.debug'] : [],
      },
    },
    plugins: [
      vue(),
      mode === 'development' && vueDevTools({ launchEditor: 'zed' }),
      mode !== 'test' && eslintPlugin({ include: ['src/**/*.vue', 'src/**/*.js', 'src/**/*.ts'] }),
      tailwindcss(),
      Components({ resolvers: [PrimeVueResolver()] }),
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
        viteCompression({
          algorithm: 'gzip',
          ext: '.gz',
          threshold: 10240,
          deleteOriginFile: false,
        }),
    ].filter(Boolean),
  }
})
