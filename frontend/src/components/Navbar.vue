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
        <span class="font-bold text-xl pl-2 title-text"
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
      v-model:visible="loginVisible"
      header="登入"
      :modal="true"
      :draggable="false"
      :closeOnEscape="true"
      :style="{ width: '350px' }"
    >
      <div class="p-fluid w-full">
        <div class="field mt-2 w-full">
          <FloatLabel variant="on" class="w-full">
            <InputText id="username" v-model="username" class="w-full" />
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
            />
            <label for="password">密碼</label>
          </FloatLabel>
        </div>
        <div class="field mt-4">
          <Button label="登入" type="submit" class="p-button-primary w-full" />
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
import { getCurrentUser, isAuthenticated } from "../utils/auth.js";
import { useTheme } from "../utils/useTheme";
import { api } from "../services/api";
import { useRouter } from "vue-router";

export default {
  data() {
    return {
      items: [],
      loginVisible: false,
      username: "",
      password: "",
      isAuthenticated: false,
      userData: null,
    };
  },
  setup() {
    const { isDarkTheme, toggleTheme } = useTheme();
    const router = useRouter();
    return {
      isDarkTheme,
      toggleTheme,
      router,
    };
  },
  mounted() {
    this.checkAuthentication();
  },

  watch: {
    $route: {
      immediate: true,
      handler() {
        this.checkAuthentication();
      },
    },
  },
  methods: {
    openLoginDialog() {
      this.loginVisible = true;
    },

    handleOAuthLogin() {
      this.loginVisible = false;
      window.location.href = `${import.meta.env.VITE_API_BASE_URL}/oauth/login`;
    },

    checkAuthentication() {
      this.isAuthenticated = isAuthenticated();
      if (this.isAuthenticated) {
        const user = getCurrentUser();
        if (user) {
          this.userData = user;
        } else {
          this.isAuthenticated = false;
          this.userData = null;
        }
      } else {
        this.isAuthenticated = false;
        this.userData = null;
      }
    },

    async handleLogout() {
      try {
        await api.post("/oauth/logout");
        sessionStorage.removeItem("authToken");
        this.isAuthenticated = false;
        this.userData = null;
        await this.$router.push("/");
      } catch (error) {
        console.error("Logout failed:", error);
        sessionStorage.removeItem("authToken");
        this.isAuthenticated = false;
        this.userData = null;
        await this.$router.push("/");
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
</style>
