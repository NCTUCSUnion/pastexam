import { createApp } from 'vue'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import './style.css'
import 'primeicons/primeicons.css'
import './styles/primeflex-legacy.css'

import App from './App.vue'
import router from './router'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'

// After a deploy, a tab opened earlier asks for chunks that no longer exist.
// Reload to get the new build, at most once a minute so a real outage cannot loop.
window.addEventListener('vite:preloadError', (event) => {
  const key = 'pastexam-chunk-reload-at'
  try {
    const last = Number(sessionStorage.getItem(key) || 0)
    if (Date.now() - last < 60_000) return
    sessionStorage.setItem(key, String(Date.now()))
  } catch {
    return
  }
  event.preventDefault()
  window.location.reload()
})

const app = createApp(App)

app.use(router)
app.use(PrimeVue, {
  license: import.meta.env.VITE_PRIMEUI_LICENSE_KEY,
  theme: {
    preset: Aura,
    options: {
      prefix: 'p',
      darkModeSelector: '.dark',
      cssLayer: false,
    },
  },
})
app.use(ToastService)
app.use(ConfirmationService)

app.mount('#app')
