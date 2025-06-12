import { ref, watch } from "vue";
import { usePrimeVue } from "primevue/config";

const THEME_KEY = "theme-preference";
const isDarkTheme = ref(localStorage.getItem(THEME_KEY) === "dark");

export function useTheme() {
  const primevue = usePrimeVue();

  const toggleTheme = () => {
    isDarkTheme.value = !isDarkTheme.value;
    localStorage.setItem(THEME_KEY, isDarkTheme.value ? "dark" : "light");
  };

  watch(
    isDarkTheme,
    (newValue) => {
      if (newValue) {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
    },
    { immediate: true }
  );

  return {
    isDarkTheme,
    toggleTheme,
  };
}
