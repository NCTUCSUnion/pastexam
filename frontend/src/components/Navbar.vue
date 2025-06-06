<template>
  <div class="card">
    <Menubar :model="items">
      <template #start>
        <span class="font-bold text-xl pl-2 title-text"
          >交大資工考古題系統</span
        >
      </template>
      <template #end>
        <div v-if="isAuthenticated" class="flex align-items-center gap-2">
          <span class="user-name flex align-items-center text-gray-300 mr-2">{{
            userData?.name || "User"
          }}</span>
          <Button
            icon="pi pi-sign-out"
            label="登出"
            @click="handleLogout"
            severity="secondary"
            size="small"
            outlined
            aria-label="Logout"
          />
        </div>
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
      </template>
    </Menubar>

    <Dialog
      v-model:visible="loginVisible"
      header="登入"
      :modal="true"
      :draggable="false"
      :dismissableMask="true"
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

    handleLogout() {
      localStorage.removeItem("authToken");
      this.isAuthenticated = false;
      this.userData = null;
      this.$router.push("/");
    },
  },
};
</script>

<style scoped>
.p-dialog .p-dialog-content {
  padding: 1.5rem;
}

.title-text {
  background: linear-gradient(to right, #a2a9b0, #d5d9e0);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  padding: 0 0.5rem;
}

.card {
  height: var(--navbar-height);
  display: flex;
  align-items: center;
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
