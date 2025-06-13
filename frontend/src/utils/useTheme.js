import { ref, watch } from "vue";

const THEME_KEY = "theme-preference";
const isDarkTheme = ref(
  localStorage.getItem(THEME_KEY)
    ? localStorage.getItem(THEME_KEY) === "dark"
    : true
);

export function useTheme() {
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
