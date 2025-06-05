<template>
  <div
    class="login-callback code-background h-full flex align-items-center justify-content-center"
  >
    <div class="text-center px-4 w-full max-w-md">
      <div v-if="loading" class="loading-container">
        <ProgressSpinner strokeWidth="4" class="mb-4" />
        <p class="text-gray-300">驗證中...</p>
      </div>
      <div v-else-if="errorMessage">
        <Card class="bg-gray-900 border-round shadow-2">
          <template #title>
            <div class="text-red-400 text-xl mb-1">登入失敗</div>
          </template>
          <template #content>
            <p class="text-gray-300 mb-4">{{ errorMessage }}</p>
            <Button
              label="返回首頁"
              icon="pi pi-home"
              @click="goToHome"
              class="p-button-secondary"
            />
          </template>
        </Card>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      loading: true,
      errorMessage: "",
    };
  },
  methods: {
    goToHome() {
      this.$router.push("/");
    },
  },
  async mounted() {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const token = urlParams.get("token");

      if (!token) {
        throw new Error("No authentication token received");
      }

      localStorage.setItem("authToken", token);

      this.$router.push("/archive");
    } catch (error) {
      console.error("Login callback error:", error);
      this.errorMessage = "驗證失敗，請重試或聯絡管理員。";
    } finally {
      this.loading = false;
    }
  },
};
</script>

<style scoped>
.code-background {
  position: relative;
}

.code-background::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><text x="20" y="30" font-family="monospace" font-size="10" fill="rgba(255,255,255,0.05)">{}</text><text x="170" y="80" font-family="monospace" font-size="10" fill="rgba(255,255,255,0.05)">for()</text><text x="60" y="150" font-family="monospace" font-size="10" fill="rgba(255,255,255,0.05)">if()</text><text x="200" y="200" font-family="monospace" font-size="10" fill="rgba(255,255,255,0.05)">while</text><text x="120" y="240" font-family="monospace" font-size="10" fill="rgba(255,255,255,0.05)">;</text><text x="40" y="100" font-family="monospace" font-size="10" fill="rgba(255,255,255,0.05)">==</text></svg>');
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
  background-color: #25272f;
  color: #f8f8f2;
}

:deep(.p-card .p-card-title) {
  text-align: center;
}

:deep(.p-card .p-card-content) {
  padding-bottom: 0;
  text-align: center;
}
</style>
