<template>
  <div id="app" class="flex flex-column">
    <Toast position="bottom-right" />
    <ConfirmDialog />
    <Navbar class="navbar px-1" @toggle-sidebar="toggleSidebar" />
    <div class="content-container">
      <router-view />
    </div>
  </div>
</template>

<script>
import Navbar from './components/Navbar.vue'
import { provide, ref } from 'vue'
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import { setGlobalToast } from './utils/toast'

export default {
  components: {
    Navbar,
    Toast,
    ConfirmDialog,
  },
  setup() {
    const sidebarVisible = ref(true)
    const toast = useToast()
    const confirm = useConfirm()

    setGlobalToast(toast)

    provide('sidebarVisible', sidebarVisible)
    provide('toast', toast)
    provide('confirm', confirm)

    const toggleSidebar = () => {
      sidebarVisible.value = !sidebarVisible.value
    }

    return {
      toggleSidebar,
    }
  },
}
</script>

<style>
:root {
  --navbar-height: 60px;
}

html,
body,
#app {
  height: 100%;
  margin: 0;
  padding: 0;
}

#app {
  display: flex;
  flex-direction: column;
}

.navbar {
  height: var(--navbar-height);
  z-index: 100;
}

.content-container {
  height: calc(100vh - var(--navbar-height));
  overflow-y: auto;
}
</style>
