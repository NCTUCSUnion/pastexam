<template>
  <div
    class="h-full flex align-items-center justify-content-center code-background relative text-gray-100"
  >
    <div class="text-left px-4 w-full max-w-2xl relative z-1">
      <div
        class="title-container mb-4 w-full overflow-x-auto overflow-y-hidden text-center"
      >
        <h1 class="text-2xl sm:text-3xl md:text-4xl font-bold tracking-wide">
          <span class="code-comment text-gray-500">/*</span>
          <span class="title-text px-2">交大資工考古題系統</span>
          <span class="code-comment text-gray-500">*/</span>
        </h1>
      </div>
      <div class="code-container mt-5 flex align-items-start relative">
        <template v-if="isLoading">
          <div class="w-full flex flex-column align-items-center justify-content-center gap-3 bg-gray-900 p-4 border-round">
            <ProgressSpinner strokeWidth="4" />
          </div>
        </template>
        <pre v-else
          class="font-mono text-sm sm:text-base md:text-lg whitespace-pre-wrap text-left bg-gray-900 p-4 border-round shadow-2 m-0 w-full overflow-hidden opacity-80"
        ><code class="typewriter" v-html="highlightedCode"></code></pre>

        <div
          class="language-badge absolute top-0 right-0 bg-white-alpha-10 text-white-alpha-70 py-1 px-2 text-xs uppercase tracking-wider"
        >
          {{ language }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watchEffect } from "vue";
import hljs from "highlight.js";
import "highlight.js/styles/atom-one-dark.css";
import axios from "axios";

const displayedText = ref("");
const highlightedCode = ref("");
const selectedMeme = ref({ code: "", language: "" });
const fullText = computed(() => selectedMeme.value.code);
const language = computed(() => selectedMeme.value.language);
const isLoading = ref(true);

let charIndex = 0;
let typingInterval;

onMounted(async () => {
  await fetchRandomMeme();
});

async function fetchRandomMeme() {
  isLoading.value = true;
  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/meme`
    );

    if (response.data && response.data.content && response.data.language) {
      selectedMeme.value = {
        code: response.data.content,
        language: response.data.language,
      };
      // console.log("API response:", response.data);
    } else {
      console.error("Invalid API response format:", response.data);
      throw new Error("Invalid API response format");
    }

    startTypewriter();
  } catch (error) {
    console.error("Error fetching meme:", error);
    selectedMeme.value = {
      code: "console.log('API connection failed');",
      language: "javascript",
    };
    startTypewriter();
  } finally {
    isLoading.value = false;
  }
}

function startTypewriter() {
  clearInterval(typingInterval);
  charIndex = 0;
  displayedText.value = "";
  highlightedCode.value = "";

  if (!fullText.value) {
    console.error("fullText.value is undefined or empty");
    return;
  }

  typingInterval = setInterval(() => {
    if (charIndex < fullText.value.length) {
      displayedText.value += fullText.value.charAt(charIndex);
      charIndex++;

      highlightedCode.value = hljs.highlight(displayedText.value, {
        language: language.value || "plaintext",
      }).value;
    } else {
      clearInterval(typingInterval);
    }
  }, 30);
}
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

.code-container {
  height: 180px;
}

.typewriter::after {
  content: "";
  border-right: 3px solid rgba(248, 248, 242, 0.7);
  animation: blink 0.75s step-end infinite;
}

.language-badge {
  border-top-right-radius: 0.5rem;
  border-bottom-left-radius: 0.5rem;
  border-top-left-radius: 0;
  border-bottom-right-radius: 0;
}

:deep(.hljs) {
  background-color: transparent !important;
  padding: 0 !important;
}

@keyframes blink {
  from,
  to {
    border-color: transparent;
  }
  50% {
    border-color: rgba(248, 248, 242, 0.7);
  }
}

.title-container {
  -ms-overflow-style: none; /* IE and Edge */
  scrollbar-width: none; /* Firefox */
}

.title-container::-webkit-scrollbar {
  display: none;
}

.title-text {
  background: linear-gradient(to right, #a2a9b0, #d5d9e0);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
</style>
