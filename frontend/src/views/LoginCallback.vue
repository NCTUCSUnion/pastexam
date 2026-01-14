<template>
  <div class="login-callback code-background h-full flex align-items-center justify-content-center">
    <div class="text-center px-4 w-full max-w-md" :style="{ color: 'var(--text-secondary)' }">
      <div v-if="errorMessage">
        <Card class="border-round shadow-2" :style="{ backgroundColor: 'var(--bg-secondary)' }">
          <template #title>
            <div class="text-red-400 text-xl mb-1">登入失敗</div>
          </template>
          <template #content>
            <p :style="{ color: 'var(--text-secondary)' }" class="mb-4">
              {{ errorMessage }}
            </p>
            <Button
              label="返回首頁"
              icon="pi pi-home"
              @click="goToHome"
              class="p-button-secondary"
            />
          </template>
        </Card>
      </div>
      <div v-else class="loading-container">
        <ProgressSpinner strokeWidth="4" class="mb-4" />
        <p>驗證中...</p>
      </div>
    </div>
  </div>
</template>

<script>
import { useTheme } from '../utils/useTheme'
import { getCodeBgSvg } from '../utils/svgBg'
import { STORAGE_KEYS, setSessionItem } from '../utils/storage'

export default {
  data() {
    return {
      errorMessage: '',
    }
  },
  setup() {
    const { isDarkTheme } = useTheme()
    return {
      isDarkTheme,
    }
  },
  methods: {
    goToHome() {
      this.$router.push('/')
    },
    setBg() {
      const el = document.querySelector('.code-background')
      if (el) {
        el.style.setProperty('background-image', getCodeBgSvg())
      }
    },
  },
  async mounted() {
    this.setBg()
    try {
      const urlParams = new URLSearchParams(window.location.search)
      const token = urlParams.get('token')

      if (!token) {
        throw new Error('No authentication token received')
      }

      setSessionItem(STORAGE_KEYS.session.AUTH_TOKEN, token)
      this.$router.replace('/archive')
    } catch (error) {
      console.error('Login callback error:', error)
      this.errorMessage = '驗證失敗，請重試或聯絡管理員。'
    }
  },
  watch: {
    isDarkTheme() {
      this.setBg()
    },
  },
}
</script>

<style scoped>
.code-background {
  position: relative;
}

.code-background::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;

  animation: scrollBackground 120s linear infinite;
  pointer-events: none;
  z-index: 0;
}

@keyframes scrollBackground {
  from {
    background-position: 0 0;
  }
  to {
    background-position: 300% 300%;
  }
}

.code-background > div {
  position: relative;
  z-index: 1;
}

:deep(.p-card) {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

:deep(.p-card .p-card-title) {
  text-align: center;
}

:deep(.p-card .p-card-content) {
  padding-bottom: 0;
  text-align: center;
}
</style>
