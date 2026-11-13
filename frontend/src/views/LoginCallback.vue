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
        <ProgressSpinner class="app-progress-spinner mb-4" :strokeWidth="8" aria-label="驗證中" />
        <p>驗證中...</p>
      </div>
    </div>
  </div>
</template>

<script>
import { useTheme } from '../utils/useTheme'
import { getCodeBgSvg } from '../utils/svgBg'
import { setToken } from '../utils/auth'
import { authService } from '../api'

// Error codes sent by the backend OAuth callback
const LOGIN_ERROR_MESSAGES = {
  denied: '已取消 NYCU 授權，請重新登入。',
  state: '登入逾時，或已在其他分頁重新登入，請重新登入。',
  provider: '無法向 NYCU 取得帳號資料，請稍後再試。',
  suspended: '此帳號已被停權，如有疑問請聯絡管理員。',
  conflict: '此 NYCU 帳號的名稱或信箱已被其他帳號使用，請聯絡管理員。',
}
const DEFAULT_ERROR_MESSAGE = '驗證失敗，請重試或聯絡管理員。'

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
    const urlParams = new URLSearchParams(window.location.search)
    const error = urlParams.get('error')
    const code = urlParams.get('code')
    if (error || !code) {
      this.errorMessage = LOGIN_ERROR_MESSAGES[error] ?? DEFAULT_ERROR_MESSAGE
      return
    }
    try {
      const { access_token: token } = await authService.exchangeOAuthCode(code)
      setToken(token)
      this.$router.replace('/archive')
    } catch (err) {
      console.error('Login callback error:', err)
      this.errorMessage = '登入連結已失效，請重新登入。'
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
