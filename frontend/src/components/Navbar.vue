<template>
  <div class="card">
    <Menubar :model="items">
      <template #start>
        <Button
          v-if="$route.path === '/archive'"
          :icon="'pi pi-bars'"
          severity="secondary"
          size="small"
          outlined
          class="mr-2"
          @click="$emit('toggle-sidebar')"
        />
        <span
          class="font-bold text-lg md:text-xl pl-2 title-text clickable-title flex align-items-center"
          @click="handleTitleClick"
        >
          <img
            :src="
              isDarkTheme
                ? '/favicon-dark/android-chrome-192x192.png'
                : '/favicon-bright/android-chrome-192x192.png'
            "
            alt="favicon"
            class="mr-2 hidden md:block"
            style="width: 24px; height: 24px; vertical-align: middle; display: inline-block"
          />
          交大資工考古題系統
        </span>
      </template>
      <template #end>
        <div class="flex align-items-center gap-2">
          <div class="hidden md:flex align-items-center gap-2">
            <span
              v-if="isAuthenticated"
              class="user-name flex align-items-center mr-2"
              :style="{ color: 'var(--text-secondary)' }"
              >{{ userData?.name || 'User' }}</span
            >
            <Button
              v-if="isAuthenticated && userData?.is_admin"
              icon="pi pi-cog"
              label="系統管理"
              @click="handleNavigateAdmin"
              severity="secondary"
              size="small"
              outlined
            />
            <Button
              v-if="isAuthenticated"
              icon="pi pi-comments"
              label="問題回報"
              @click="openIssueReportDialog"
              severity="secondary"
              size="small"
              outlined
              aria-label="Report Issue"
            />
            <Button
              v-if="isAuthenticated"
              icon="pi pi-sparkles"
              label="AI 生成試題"
              @click="openAIExamDialog"
              severity="info"
              size="small"
              outlined
              aria-label="Generate AI Exam"
            />
            <Button
              v-if="isAuthenticated"
              icon="pi pi-sign-out"
              label="登出"
              @click="handleLogout"
              severity="secondary"
              size="small"
              outlined
              aria-label="Logout"
            />
            <Button
              v-else
              icon="pi pi-sign-in"
              label="登入"
              @click="openLoginDialog"
              severity="secondary"
              size="small"
              outlined
              aria-label="Login"
            />
          </div>

          <div class="flex md:hidden align-items-center gap-2">
            <Button
              v-if="isAuthenticated"
              icon="pi pi-sign-out"
              label="登出"
              @click="handleLogout"
              severity="secondary"
              size="small"
              outlined
              aria-label="Logout"
            />
            <Button
              v-else
              icon="pi pi-sign-in"
              label="登入"
              @click="openLoginDialog"
              severity="secondary"
              size="small"
              outlined
              aria-label="Login"
            />
          </div>

          <Button
            :icon="isDarkTheme ? 'pi pi-sun' : 'pi pi-moon'"
            severity="secondary"
            size="small"
            outlined
            @click="handleToggleTheme"
          />
        </div>
      </template>
    </Menubar>

    <Dialog
      :visible="loginVisible"
      @update:visible="loginVisible = $event"
      header="登入"
      :modal="true"
      :draggable="false"
      :closeOnEscape="false"
      :style="{ width: '350px', maxWidth: '85vw' }"
      :autoFocus="false"
    >
      <div class="p-fluid w-full">
        <div class="field mt-2 w-full">
          <FloatLabel variant="on" class="w-full">
            <InputText
              id="username"
              v-model="username"
              class="w-full"
              @keyup.enter="handleLocalLogin"
            />
            <label for="username">帳號</label>
          </FloatLabel>
        </div>
        <div class="field mt-3 w-full">
          <FloatLabel variant="on" class="w-full">
            <Password
              id="password"
              v-model="password"
              toggleMask
              :feedback="false"
              class="w-full"
              inputClass="w-full"
              @keyup.enter="handleLocalLogin"
            />
            <label for="password">密碼</label>
          </FloatLabel>
        </div>
        <div class="field mt-4">
          <Button
            label="登入"
            type="submit"
            class="p-button-primary w-full"
            @click="handleLocalLogin"
            :loading="loading"
          />
        </div>

        <div class="field mt-3">
          <Divider align="center">
            <span class="text-sm text-600">OR</span>
          </Divider>
        </div>

        <div class="flex justify-content-between mt-3">
          <Button
            icon="pi pi-graduation-cap"
            label="NYCU OAuth"
            class="p-button-secondary p-button-outlined w-full"
            @click="handleOAuthLogin"
          />
        </div>
      </div>
    </Dialog>

    <Dialog
      :visible="issueReportVisible"
      @update:visible="handleIssueReportDialogClose"
      header="問題回報"
      :modal="true"
      :draggable="false"
      :closeOnEscape="true"
      :style="{ width: '700px', maxWidth: '90vw' }"
      class="issue-report-dialog"
    >
      <div class="p-fluid w-full">
        <div class="field">
          <label for="issue-type" class="font-semibold">問題類型</label>
          <Select
            id="issue-type"
            v-model="issueForm.type"
            :options="issueTypes"
            optionLabel="label"
            optionValue="value"
            placeholder="選擇問題類型"
            class="w-full mt-2"
          />
        </div>

        <div class="field mt-3">
          <label for="issue-title" class="font-semibold">問題標題</label>
          <InputText
            id="issue-title"
            v-model="issueForm.title"
            placeholder="簡短描述遇到的問題"
            class="w-full mt-2"
            :maxlength="100"
          />
          <small class="text-gray-500">{{ issueForm.title.length }}/100</small>
        </div>

        <div class="field mt-3">
          <label for="issue-description" class="font-semibold">詳細描述</label>
          <Textarea
            id="issue-description"
            v-model="issueForm.description"
            placeholder="請詳細描述遇到的問題，包括：&#10;1. 操作步驟&#10;2. 預期結果&#10;3. 實際結果"
            class="w-full mt-2"
            rows="8"
            :maxlength="2000"
          />
          <small class="text-gray-500">{{ issueForm.description.length }}/2000</small>
        </div>

        <div class="field mt-3">
          <label for="user-info" class="font-semibold">聯絡方式 (選填)</label>
          <InputText
            id="user-info"
            v-model="issueForm.contact"
            placeholder="Email 或其他聯絡方式，方便我們回覆"
            class="w-full mt-2"
          />
        </div>

        <div class="flex justify-between gap-3 mt-4">
          <Button
            label="取消"
            severity="secondary"
            outlined
            @click="closeIssueReportDialog"
            class="flex-1"
          />
          <Button
            label="提交到 GitHub"
            icon="pi pi-external-link"
            @click="submitIssueReport"
            :disabled="!canSubmitIssue"
            class="flex-1"
          />
        </div>

        <div class="mt-3 p-3 bg-blue-50 border-round text-sm flex align-items-center">
          <i class="pi pi-info-circle text-blue-600 mr-2"></i>
          <span class="text-blue-800">
            點擊「提交到 GitHub」將會跳轉到 GitHub 頁面，您可以在那裡完成問題提交
          </span>
        </div>
      </div>
    </Dialog>

    <!-- AI 生成模擬試題 Modal -->
    <GenerateAIExamModal
      :visible="aiExamDialogVisible"
      @update:visible="aiExamDialogVisible = $event"
      :coursesList="coursesList"
    />
  </div>
</template>

<script>
import { getCurrentUser, isAuthenticated, setToken } from '../utils/auth.js'
import { useTheme } from '../utils/useTheme'
import { authService } from '../api'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { trackEvent, EVENTS } from '../utils/analytics'
import GenerateAIExamModal from './GenerateAIExamModal.vue'

export default {
  name: 'AppNavbar',
  components: {
    GenerateAIExamModal,
  },
  emits: ['toggle-sidebar'],
  data() {
    return {
      items: [],
      loginVisible: false,
      username: '',
      password: '',
      isAuthenticated: false,
      userData: null,
      loading: false,
      issueReportVisible: false,
      issueForm: {
        type: '',
        title: '',
        description: '',
        contact: '',
      },
      issueTypes: [
        { label: 'Bug / 程式錯誤', value: 'bug' },
        { label: '功能建議', value: 'enhancement' },
        { label: '效能問題', value: 'performance' },
        { label: 'UI/UX 問題', value: 'ui-ux' },
        { label: '其他問題', value: 'question' },
      ],
      aiExamDialogVisible: false,
      coursesList: null,
    }
  },
  setup() {
    const { isDarkTheme, toggleTheme } = useTheme()
    const router = useRouter()
    const toast = useToast()

    return {
      isDarkTheme,
      toggleTheme,
      router,
      toast,
    }
  },
  mounted() {
    this.checkAuthentication()

    setInterval(() => {
      const focusedElements = document.querySelectorAll(
        '.p-menubar .p-focus, .p-menubar .p-highlight, .p-menubar [tabindex="0"]'
      )
      focusedElements.forEach((el) => {
        el.classList.remove('p-focus', 'p-highlight')
        if (el.tabIndex >= 0) {
          el.blur()
        }
      })
    }, 500)
  },

  watch: {
    $route: {
      immediate: true,
      handler() {
        this.checkAuthentication()
        this.$nextTick(() => {
          const focusedElements = document.querySelectorAll(
            '.p-menubar .p-menuitem-content, .p-menubar .p-menuitem-link, .p-menubar .p-focus, .p-menubar .p-highlight'
          )
          focusedElements.forEach((el) => {
            el.blur()
            el.classList.remove('p-focus', 'p-highlight')
          })
        })
      },
    },
  },
  methods: {
    handleToggleTheme() {
      trackEvent(EVENTS.TOGGLE_THEME, {
        from: this.isDarkTheme ? 'dark' : 'light',
        to: this.isDarkTheme ? 'light' : 'dark',
      })
      this.toggleTheme()
    },

    openLoginDialog() {
      this.loginVisible = true
      trackEvent(EVENTS.LOGIN, { type: 'dialog-open' })
    },

    async handleLocalLogin() {
      if (!this.username || !this.password) {
        this.toast.add({
          severity: 'error',
          summary: '錯誤',
          detail: '請輸入帳號和密碼',
          life: 3000,
        })
        return
      }

      this.loading = true
      try {
        const response = await authService.localLogin(this.username, this.password)
        setToken(response.access_token)
        this.loginVisible = false
        this.checkAuthentication()
        this.username = ''
        this.password = ''

        trackEvent(EVENTS.LOGIN_LOCAL, { success: true })

        await this.router.push('/archive')
      } catch (error) {
        console.error('Login failed:', error)
        trackEvent(EVENTS.LOGIN_LOCAL, { success: false })
        this.toast.add({
          severity: 'error',
          summary: '登入失敗',
          detail: '帳號或密碼錯誤',
          life: 3000,
        })
      } finally {
        this.loading = false
      }
    },

    handleOAuthLogin() {
      this.loginVisible = false
      trackEvent(EVENTS.LOGIN_OAUTH, { provider: 'NYCU' })
      authService.login()
    },

    checkAuthentication() {
      this.isAuthenticated = isAuthenticated()
      if (this.isAuthenticated) {
        const user = getCurrentUser()
        if (user) {
          this.userData = user
          this.updateMenuItems()
        } else {
          this.isAuthenticated = false
          this.userData = null
          this.items = []
        }
      } else {
        this.isAuthenticated = false
        this.userData = null
        this.items = []
      }
    },

    updateMenuItems() {
      this.items = []
    },

    async handleLogout() {
      try {
        await authService.logout()
        trackEvent(EVENTS.LOGOUT, { success: true })
      } catch (error) {
        console.error('Logout API failed:', error)
        trackEvent(EVENTS.LOGOUT, { success: false })
      }

      sessionStorage.removeItem('authToken')
      localStorage.removeItem('selectedSubject')
      localStorage.removeItem('adminCurrentTab')
      this.isAuthenticated = false
      this.userData = null

      await this.$router.push('/')
    },

    handleTitleClick() {
      if (this.isAuthenticated) {
        trackEvent(EVENTS.NAVIGATE_ARCHIVE, { from: 'title-click' })
        this.$router.push('/archive')
      }
    },

    handleNavigateAdmin() {
      trackEvent(EVENTS.NAVIGATE_ADMIN, { from: 'navbar' })
      this.$router.push('/admin')
    },

    openIssueReportDialog() {
      this.issueReportVisible = true
      trackEvent(EVENTS.OPEN_ISSUE_REPORT)
    },

    closeIssueReportDialog() {
      this.issueReportVisible = false
      this.issueForm = {
        type: '',
        title: '',
        description: '',
        contact: '',
      }
    },

    async openAIExamDialog() {
      this.aiExamDialogVisible = true
      if (!this.coursesList) {
        try {
          const { courseService } = await import('../api')
          const { data } = await courseService.listCourses()
          this.coursesList = data
        } catch (error) {
          console.error('Failed to load courses:', error)
          this.toast.add({
            severity: 'error',
            summary: '載入失敗',
            detail: '無法載入課程列表',
            life: 3000,
          })
        }
      }
    },

    handleIssueReportDialogClose(visible) {
      this.issueReportVisible = visible
      if (!visible) {
        this.issueForm = {
          type: '',
          title: '',
          description: '',
          contact: '',
        }
      }
    },

    submitIssueReport() {
      const { type, title, description, contact } = this.issueForm

      trackEvent(EVENTS.SUBMIT_ISSUE_REPORT, {
        type,
        hasContact: !!contact,
        titleLength: title.length,
        descriptionLength: description.length,
      })

      const systemInfo = this.getSystemInfo()
      const issueBody = this.formatIssueBody(description, contact, systemInfo, type)
      const repoOwner = 'nctucsunion'
      const repoName = 'pastexam'
      const githubUrl =
        `https://github.com/${repoOwner}/${repoName}/issues/new?` +
        `title=${encodeURIComponent(title)}&` +
        `body=${encodeURIComponent(issueBody)}`

      window.open(githubUrl, '_blank')

      this.closeIssueReportDialog()
      this.toast.add({
        severity: 'success',
        summary: '已跳轉到 GitHub',
        detail: '請在 GitHub 頁面完成問題提交',
        life: 3000,
      })
    },

    getSystemInfo() {
      const nav = navigator
      return {
        userAgent: nav.userAgent,
        platform: nav.platform,
        language: nav.language,
        url: window.location.href,
        timestamp: new Date().toISOString(),
      }
    },

    getBrowserInfo(userAgent) {
      if (userAgent.includes('Chrome') && !userAgent.includes('Edge')) {
        const chromeMatch = userAgent.match(/Chrome\/(\d+\.\d+)/)
        return chromeMatch ? `Chrome ${chromeMatch[1]}` : 'Chrome'
      } else if (userAgent.includes('Firefox')) {
        const firefoxMatch = userAgent.match(/Firefox\/(\d+\.\d+)/)
        return firefoxMatch ? `Firefox ${firefoxMatch[1]}` : 'Firefox'
      } else if (userAgent.includes('Safari') && !userAgent.includes('Chrome')) {
        const safariMatch = userAgent.match(/Safari\/(\d+\.\d+)/)
        return safariMatch ? `Safari ${safariMatch[1]}` : 'Safari'
      } else if (userAgent.includes('Edge')) {
        const edgeMatch = userAgent.match(/Edge\/(\d+\.\d+)/)
        return edgeMatch ? `Edge ${edgeMatch[1]}` : 'Edge'
      }
      return 'Unknown Browser'
    },

    getOSInfo(platform, userAgent) {
      if (userAgent.includes('Mac OS X')) {
        const macMatch = userAgent.match(/Mac OS X (\d+_\d+)/)
        if (macMatch) {
          const version = macMatch[1].replace('_', '.')
          return `macOS ${version}`
        }
        return 'macOS'
      } else if (userAgent.includes('Windows')) {
        if (userAgent.includes('Windows NT 10.0')) return 'Windows 10/11'
        if (userAgent.includes('Windows NT 6.3')) return 'Windows 8.1'
        if (userAgent.includes('Windows NT 6.1')) return 'Windows 7'
        return 'Windows'
      } else if (userAgent.includes('Linux')) {
        return 'Linux'
      } else if (userAgent.includes('Android')) {
        const androidMatch = userAgent.match(/Android (\d+\.\d+)/)
        return androidMatch ? `Android ${androidMatch[1]}` : 'Android'
      } else if (userAgent.includes('iPhone') || userAgent.includes('iPad')) {
        const iosMatch = userAgent.match(/OS (\d+_\d+)/)
        if (iosMatch) {
          const version = iosMatch[1].replace('_', '.')
          return `iOS ${version}`
        }
        return 'iOS'
      }
      return platform || 'Unknown System'
    },

    formatTimestamp(timestamp) {
      const date = new Date(timestamp)
      const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZone: 'Asia/Taipei',
        hour12: false,
      }
      return date.toLocaleString('zh-TW', options) + ' (UTC+8)'
    },

    formatIssueBody(description, contact, systemInfo, type) {
      let body = ''

      body += `<!-- type: ${type || 'question'} -->\n\n`

      body += '## 問題描述\n\n' + description + '\n\n'

      if (contact) {
        body += '## 聯絡方式\n\n' + contact + '\n\n'
      }

      const browserInfo = this.getBrowserInfo(systemInfo.userAgent)
      const osInfo = this.getOSInfo(systemInfo.platform, systemInfo.userAgent)
      const formattedTime = this.formatTimestamp(systemInfo.timestamp)

      body += '## 環境資訊\n\n'
      body += `| 項目 | 資訊 |\n`
      body += `|------|------|\n`
      body += `| 瀏覽器 | ${browserInfo} |\n`
      body += `| 作業系統 | ${osInfo} |\n`
      body += `| 語言設定 | ${systemInfo.language} |\n`
      body += `| 頁面位置 | ${systemInfo.url} |\n`
      body += `| 回報時間 | ${formattedTime} |\n\n`

      body += '<details>\n<summary>詳細系統資訊</summary>\n\n'
      body += '```\n'
      body += `User Agent: ${systemInfo.userAgent}\n`
      body += `Platform: ${systemInfo.platform}\n`
      body += `Timestamp: ${systemInfo.timestamp}\n`
      body += '```\n'
      body += '</details>\n\n'

      body += '---\n*此問題由交大資工考古題系統自動產生*'

      return body
    },
  },

  computed: {
    canSubmitIssue() {
      return this.issueForm.type && this.issueForm.title.trim() && this.issueForm.description.trim()
    },
  },
}
</script>

<style scoped>
.p-dialog .p-dialog-content {
  padding: 1.5rem;
}

.title-text {
  background: linear-gradient(to right, var(--title-gradient-start), var(--title-gradient-end));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  padding: 0 0.5rem;
}

.clickable-title {
  cursor: pointer;
  transition: transform 0.2s ease;
}

.clickable-title:hover {
  transform: scale(1.02);
}

.card {
  height: var(--navbar-height);
  display: flex;
  align-items: center;
  background-color: var(--bg-primary);
}

.user-name {
  display: flex;
  align-items: center;
  line-height: 1;
  margin: auto 0;
}

:deep(.p-menubar-end) > div {
  display: flex;
  align-items: center;
  height: 100%;
}

:deep(.p-menubar) {
  width: 100%;
  padding: 0.5rem 1rem;
}

:deep(.p-password) {
  width: 100%;
}

:deep(.p-password-input) {
  width: 100%;
}

:deep(.p-inputtext) {
  width: 100%;
}

:deep(.p-float-label) {
  width: 100%;
}

:deep(.p-menubar .p-menubar-root-list > .p-menuitem > .p-menuitem-content) {
  transition: background-color 0.2s ease;
  background: transparent !important;
}

:deep(.p-menubar .p-menubar-root-list > .p-menuitem > .p-menuitem-content:hover) {
  background: var(--highlight-bg) !important;
}

:deep(.p-menubar .p-menubar-root-list > .p-menuitem > .p-menuitem-content:focus) {
  outline: none !important;
  box-shadow: none !important;
  background: transparent !important;
}

:deep(.p-menubar .p-menubar-root-list > .p-menuitem > .p-menuitem-content:active) {
  background: transparent !important;
}

:deep(.p-menubar .p-menubar-root-list > .p-menuitem > .p-menuitem-content.p-focus) {
  background: transparent !important;
}

:deep(.p-menubar .p-menubar-root-list > .p-menuitem-link) {
  background: transparent !important;
}

:deep(.p-menubar .p-menubar-root-list > .p-menuitem-link:focus) {
  background: transparent !important;
  box-shadow: none !important;
}

:deep(.p-menubar .p-menuitem) {
  outline: none !important;
  background: transparent !important;
}

:deep(.p-menubar .p-menuitem:focus) {
  background: transparent !important;
  outline: none !important;
}

:deep(.p-menubar .p-menuitem:focus-visible) {
  background: transparent !important;
  outline: none !important;
  box-shadow: none !important;
}

:deep(.p-menubar .p-menuitem.p-focus) {
  background: transparent !important;
}

:deep(.p-menubar .p-menuitem.p-highlight) {
  background: transparent !important;
}

:deep(.p-menubar) {
  outline: none;
}

:deep(.p-menubar *:focus) {
  background: transparent !important;
  outline: none !important;
  box-shadow: none !important;
}

:deep(.p-menubar *.p-focus) {
  background: transparent !important;
}

:deep(.p-menubar *.p-highlight) {
  background: transparent !important;
}
</style>
