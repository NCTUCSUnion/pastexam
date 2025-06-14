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
          class="font-bold text-xl pl-2 title-text clickable-title"
          @click="handleTitleClick"
          >交大資工考古題系統</span
        >
      </template>
      <template #end>
        <div class="flex align-items-center gap-2">
          <span
            v-if="isAuthenticated"
            class="user-name flex align-items-center mr-2"
            :style="{ color: 'var(--text-secondary)' }"
            >{{ userData?.name || "User" }}</span
          >
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
          <Button
            :icon="isDarkTheme ? 'pi pi-sun' : 'pi pi-moon'"
            severity="secondary"
            size="small"
            outlined
            @click="toggleTheme"
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
      :style="{ width: '400px' }"
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
  </div>
</template>

<script>
import { getCurrentUser, isAuthenticated, setToken } from "../utils/auth.js";
import { useTheme } from "../utils/useTheme";
import { authService } from "../api";
import { useRouter } from "vue-router";
import { useToast } from "primevue/usetoast";

export default {
  name: "AppNavbar",
  data() {
    return {
      items: [],
      loginVisible: false,
      username: "",
      password: "",
      isAuthenticated: false,
      userData: null,
      loading: false,
    };
  },
  setup() {
    const { isDarkTheme, toggleTheme } = useTheme();
    const router = useRouter();
    const toast = useToast();
    return {
      isDarkTheme,
      toggleTheme,
      router,
      toast,
    };
  },
  mounted() {
    this.checkAuthentication();

    // Continuously clear focus states from menubar
    setInterval(() => {
      const focusedElements = document.querySelectorAll(
        '.p-menubar .p-focus, .p-menubar .p-highlight, .p-menubar [tabindex="0"]'
      );
      focusedElements.forEach((el) => {
        el.classList.remove("p-focus", "p-highlight");
        if (el.tabIndex >= 0) {
          el.blur();
        }
      });
    }, 500);
  },

  watch: {
    $route: {
      immediate: true,
      handler() {
        this.checkAuthentication();
        // Force remove focus from menubar items when route changes
        this.$nextTick(() => {
          const focusedElements = document.querySelectorAll(
            ".p-menubar .p-menuitem-content, .p-menubar .p-menuitem-link, .p-menubar .p-focus, .p-menubar .p-highlight"
          );
          focusedElements.forEach((el) => {
            el.blur();
            el.classList.remove("p-focus", "p-highlight");
          });
        });
      },
    },
  },
  methods: {
    openLoginDialog() {
      this.loginVisible = true;
    },

    async handleLocalLogin() {
      if (!this.username || !this.password) {
        this.toast.add({
          severity: "error",
          summary: "錯誤",
          detail: "請輸入帳號和密碼",
          life: 3000,
        });
        return;
      }

      this.loading = true;
      try {
        const response = await authService.localLogin(
          this.username,
          this.password
        );
        setToken(response.access_token);
        this.loginVisible = false;
        this.checkAuthentication();
        this.username = "";
        this.password = "";
        await this.router.push("/archive");
      } catch (error) {
        console.error("Login failed:", error);
        this.toast.add({
          severity: "error",
          summary: "登入失敗",
          detail: "帳號或密碼錯誤",
          life: 3000,
        });
      } finally {
        this.loading = false;
      }
    },

    handleOAuthLogin() {
      this.loginVisible = false;
      authService.login();
    },

    checkAuthentication() {
      this.isAuthenticated = isAuthenticated();
      if (this.isAuthenticated) {
        const user = getCurrentUser();
        if (user) {
          this.userData = user;
          this.updateMenuItems(user);
        } else {
          this.isAuthenticated = false;
          this.userData = null;
          this.items = [];
        }
      } else {
        this.isAuthenticated = false;
        this.userData = null;
        this.items = [];
      }
    },

    updateMenuItems(user) {
      this.items = [];

      if (this.isAuthenticated && user.is_admin) {
        this.items.push({
          label: "系統管理",
          icon: "pi pi-cog",
          command: () => {
            this.$router.push("/admin");
          },
        });
      }
    },

    async handleLogout() {
      try {
        await authService.logout();
      } catch (error) {
        console.error("Logout API failed:", error);
      }

      sessionStorage.removeItem("authToken");
      this.isAuthenticated = false;
      this.userData = null;

      await this.$router.push("/");
    },

    handleTitleClick() {
      if (this.isAuthenticated) {
        this.$router.push("/archive");
      }
    },
  },
};
</script>

<style scoped>
.p-dialog .p-dialog-content {
  padding: 1.5rem;
}

.title-text {
  background: linear-gradient(
    to right,
    var(--title-gradient-start),
    var(--title-gradient-end)
  );
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

/* Fix menubar item hover state */
:deep(.p-menubar .p-menubar-root-list > .p-menuitem > .p-menuitem-content) {
  transition: background-color 0.2s ease;
  background: transparent !important;
}

:deep(
  .p-menubar .p-menubar-root-list > .p-menuitem > .p-menuitem-content:hover
) {
  background: var(--highlight-bg) !important;
}

:deep(
  .p-menubar .p-menubar-root-list > .p-menuitem > .p-menuitem-content:focus
) {
  outline: none !important;
  box-shadow: none !important;
  background: transparent !important;
}

:deep(
  .p-menubar .p-menubar-root-list > .p-menuitem > .p-menuitem-content:active
) {
  background: transparent !important;
}

:deep(
  .p-menubar .p-menubar-root-list > .p-menuitem > .p-menuitem-content.p-focus
) {
  background: transparent !important;
}

:deep(.p-menubar .p-menubar-root-list > .p-menuitem-link) {
  background: transparent !important;
}

:deep(.p-menubar .p-menubar-root-list > .p-menuitem-link:focus) {
  background: transparent !important;
  box-shadow: none !important;
}

/* Additional rules to prevent active state persistence */
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

/* Override all possible PrimeVue focus states */
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
