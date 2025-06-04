<template>
  <div class="card">
    <Menubar :model="items">
      <template #start>
        <span class="font-bold text-xl pl-2 title-text"
          >交大資工考古題系統</span
        >
      </template>
      <template #end>
        <Button
          icon="pi pi-sign-in"
          @click="openLoginDialog"
          text
          rounded
          aria-label="Login"
        />
      </template>
    </Menubar>

    <Dialog
      v-model:visible="loginVisible"
      header="Login"
      :modal="true"
      :closable="true"
      :style="{ width: '350px' }"
    >
      <div class="p-fluid w-full">
        <div class="field mt-2 w-full">
          <FloatLabel variant="on" class="w-full">
            <InputText id="username" v-model="username" class="w-full" />
            <label for="username">Username</label>
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
            <label for="password">Password</label>
          </FloatLabel>
        </div>
        <div class="field mt-4">
          <Button label="Login" type="submit" class="p-button-primary w-full" />
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
            class="p-button-secondary p-button-outlined w-full mr-3"
          />
          <Button
            icon="pi pi-building"
            label="CSIT OAuth"
            class="p-button-secondary p-button-outlined w-full"
          />
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script>
export default {
  data() {
    return {
      items: [],
      loginVisible: false,
      username: "",
      password: "",
    };
  },
  methods: {
    openLoginDialog() {
      this.loginVisible = true;
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

.oauth-icon {
  width: 24px;
  height: 24px;
  display: inline-block;
  vertical-align: middle;
}

.card {
  height: var(--navbar-height);
  display: flex;
  align-items: center;
}

:deep(.p-menubar) {
  width: 100%;
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
