import { defineConfig, configDefaults } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { PrimeVueResolver } from '@primevue/auto-import-resolver'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [
    vue(),
    Components({ resolvers: [PrimeVueResolver()] }),
  ],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['tests/unit/**/*.{test,spec}.{js,ts,tsx}'],
    exclude: [...configDefaults.exclude, 'tests/e2e/**', 'playwright-report/**'],
    coverage: {
      provider: 'v8',
      reportsDirectory: 'coverage',
      reporter: ['text', 'lcov', 'html'],
      include: ['src/**/*.{js,ts,tsx,vue}'],
      exclude: [
        'src/main.*',
        'src/App.vue',
        'src/**/index.*',
        'src/**/types/**',
        'src/**/__mocks__/**',
        '**/*.d.ts',
        'tests/**',
      ],
    },
  },
})
