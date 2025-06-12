<template>
  <div id="app" class="flex flex-column">
    <Navbar class="navbar px-1" @toggle-drawer="toggleDrawer" />
    <div class="content-container">
      <router-view />
    </div>
  </div>
</template>

<script>
import Navbar from "./components/Navbar.vue";
import { ref, provide } from "vue";

export default {
  components: {
    Navbar,
  },
  setup() {
    const drawerVisible = ref(true);
    provide("drawerVisible", drawerVisible);

    const toggleDrawer = () => {
      drawerVisible.value = !drawerVisible.value;
    };

    return {
      toggleDrawer,
    };
  },
};
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
