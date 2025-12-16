<template>
  <div
    class="h-full flex flex-column align-items-center justify-content-center code-background relative"
    :class="{ 'text-gray-100': isDarkTheme, 'text-gray-900': !isDarkTheme }"
  >
    <div
      class="text-left px-4 w-full max-w-2xl relative z-1 flex-1 flex align-items-center justify-content-center"
      style="margin-top: -10vh"
    >
      <div class="w-full">
        <div class="title-container mb-4 w-full overflow-x-auto overflow-y-hidden text-center">
          <h1 class="text-2xl sm:text-3xl md:text-4xl font-bold tracking-wide">
            <span class="code-comment text-gray-500">/*</span>
            <span class="title-text px-2">交大資工考古題系統</span>
            <span class="code-comment text-gray-500">*/</span>
          </h1>
        </div>
        <div class="code-container mt-5 flex align-items-start relative">
          <template v-if="isLoading">
            <div
              class="w-full font-mono text-sm sm:text-base md:text-lg text-left p-4 border-round shadow-2 m-0"
              :style="{ backgroundColor: 'var(--code-bg)', opacity: 0.8 }"
            >
              <div class="code-compilation">
                <div class="compilation-line">> Initializing source...</div>
                <div class="compilation-line">> Parsing syntax...</div>
                <div class="compilation-line">
                  > Compiling code<span class="compilation-cursor"></span>
                </div>
              </div>
            </div>
          </template>
          <pre
            v-else
            class="font-mono text-sm sm:text-base md:text-lg whitespace-pre-wrap text-left p-4 border-round shadow-2 m-0 w-full overflow-hidden"
            :style="{ backgroundColor: 'var(--code-bg)', opacity: 0.8 }"
          ><code class="typewriter" v-html="highlightedCode"></code></pre>

          <div
            v-if="!isLoading"
            class="language-badge absolute top-0 right-0 py-1 px-2 text-xs uppercase tracking-wider"
            :style="{
              backgroundColor: isDarkTheme ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
              color: isDarkTheme ? 'rgba(255, 255, 255, 0.95)' : 'rgba(0, 0, 0, 0.9)',
              borderTopRightRadius: '0.5rem',
              borderBottomLeftRadius: '0.5rem',
              backdropFilter: 'blur(4px)',
              border: isDarkTheme
                ? '1px solid rgba(255, 255, 255, 0.2)'
                : '1px solid rgba(0, 0, 0, 0.1)',
            }"
          >
            {{ language }}
          </div>
        </div>
      </div>
    </div>

    <div class="statistics-panel absolute bottom-4 left-4 right-4 z-2">
      <div class="flex flex-wrap justify-content-center gap-3">
        <div
          v-for="(stat, index) in statistics"
          :key="stat.key"
          class="stat-card p-3 border-round shadow-3 backdrop-blur"
          :style="{
            backgroundColor: isDarkTheme ? 'rgba(255, 255, 255, 0.03)' : 'rgba(255, 255, 255, 0.4)',
            border: isDarkTheme
              ? '1px solid rgba(255, 255, 255, 0.2)'
              : '1px solid rgba(0, 0, 0, 0.1)',
            animationDelay: `${index * 0.1}s`,
          }"
          :class="{ 'animate-fade-in': statsLoaded }"
        >
          <div class="flex align-items-center gap-2">
            <i :class="stat.icon" class="text-lg" :style="{ color: stat.color }"></i>
            <div>
              <div
                class="font-bold text-sm"
                :style="{
                  color: isDarkTheme ? 'rgba(255, 255, 255, 0.9)' : 'rgba(0, 0, 0, 0.8)',
                }"
              >
                {{ stat.label }}
              </div>
              <div
                class="text-xs opacity-70"
                :style="{
                  color: isDarkTheme ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.6)',
                }"
              >
                {{ animatedValues[stat.key] }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({
  name: 'HomeView',
})

import { ref, onMounted, computed, watch, onUnmounted } from 'vue'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css'
import { useTheme } from '../utils/useTheme'
import { getCodeBgSvg } from '../utils/svgBg'
import { memeService, statisticsService } from '../api'

const { isDarkTheme } = useTheme()
const displayedText = ref('')
const highlightedCode = ref('')
const selectedMeme = ref({ code: '', language: '' })
const fullText = computed(() => selectedMeme.value.code)
const language = computed(() => selectedMeme.value.language)
const isLoading = ref(true)

const statisticsData = ref({
  totalUsers: 0,
  totalDownloads: 0,
  onlineUsers: 0,
  totalArchives: 0,
  totalCourses: 0,
  activeToday: 0,
})

const animatedValues = ref({
  totalUsers: 0,
  totalDownloads: 0,
  onlineUsers: 0,
  totalArchives: 0,
  totalCourses: 0,
  activeToday: 0,
})

const statsLoaded = ref(false)

const statistics = computed(() => [
  {
    key: 'totalUsers',
    label: '總用戶數',
    icon: 'pi pi-users',
    color: '#4FC3F7',
  },
  {
    key: 'totalDownloads',
    label: '總下載次數',
    icon: 'pi pi-download',
    color: '#66BB6A',
  },
  {
    key: 'onlineUsers',
    label: '在線用戶',
    icon: 'pi pi-circle-fill',
    color: '#FFA726',
  },
  {
    key: 'totalArchives',
    label: '考古題總數',
    icon: 'pi pi-file-pdf',
    color: '#EF5350',
  },
  {
    key: 'totalCourses',
    label: '課程總數',
    icon: 'pi pi-book',
    color: '#AB47BC',
  },
  {
    key: 'activeToday',
    label: '今日活躍',
    icon: 'pi pi-chart-line',
    color: '#26A69A',
  },
])

let charIndex = 0
let typingInterval
let statsInterval
let animationIntervals = {}

onMounted(async () => {
  await fetchRandomMeme()
  await fetchStatistics()
  setBg()
  // startStatsUpdates()
})

onUnmounted(() => {
  clearInterval(typingInterval)
  clearInterval(statsInterval)
  Object.values(animationIntervals).forEach(clearInterval)
})

watch(isDarkTheme, () => {
  setBg()
})

async function fetchRandomMeme() {
  isLoading.value = true
  try {
    const response = await memeService.getRandomMeme()

    if (response.data && response.data.content && response.data.language) {
      selectedMeme.value = {
        code: response.data.content,
        language: response.data.language,
      }
    } else {
      console.error('Invalid API response format:', response.data)
      throw new Error('Invalid API response format')
    }

    startTypewriter()
  } catch (error) {
    console.error('Error fetching meme:', error)
    selectedMeme.value = {
      code: "console.log('API connection failed');",
      language: 'javascript',
    }
    startTypewriter()
  } finally {
    isLoading.value = false
  }
}

function startTypewriter() {
  clearInterval(typingInterval)
  charIndex = 0
  displayedText.value = ''
  highlightedCode.value = ''

  if (!fullText.value) {
    console.error('fullText.value is undefined or empty')
    return
  }

  typingInterval = setInterval(() => {
    if (charIndex < fullText.value.length) {
      displayedText.value += fullText.value.charAt(charIndex)
      charIndex++

      highlightedCode.value = hljs.highlight(displayedText.value, {
        language: language.value || 'plaintext',
      }).value
    } else {
      clearInterval(typingInterval)
    }
  }, 30)
}

async function fetchStatistics() {
  try {
    const response = await statisticsService.getSystemStatistics()

    if (response.data && response.data.data) {
      statisticsData.value = response.data.data
      animateCounters()
      statsLoaded.value = true
    } else {
      console.error('Invalid API response format:', response.data)
      throw new Error('Invalid API response format')
    }
  } catch (error) {
    console.error('Error fetching statistics:', error)
    const nanData = {
      totalUsers: NaN,
      totalDownloads: NaN,
      onlineUsers: NaN,
      totalArchives: NaN,
      totalCourses: NaN,
      activeToday: NaN,
    }

    statisticsData.value = nanData
    animatedValues.value = {
      totalUsers: 'NaN',
      totalDownloads: 'NaN',
      onlineUsers: 'NaN',
      totalArchives: 'NaN',
      totalCourses: 'NaN',
      activeToday: 'NaN',
    }
    statsLoaded.value = true
  }
}

function animateCounters() {
  Object.keys(statisticsData.value).forEach((key) => {
    const targetValue = statisticsData.value[key]

    if (animationIntervals[key]) {
      clearInterval(animationIntervals[key])
    }

    animatedValues.value[key] = formatNumber(targetValue)
  })
}

function formatNumber(num) {
  if (isNaN(num) || num === null || num === undefined) {
    return 'NaN'
  }
  return num.toString()
}

// function startStatsUpdates() {
//   statsInterval = setInterval(async () => {
//     await fetchStatistics()
//   }, 30000)
// }

function setBg() {
  const el = document.querySelector('.code-background')
  if (el) {
    el.style.setProperty('background-image', getCodeBgSvg())
  }
}
</script>

<style scoped>
.code-background {
  position: relative;
}

.code-background::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;

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
  content: '';
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
  color: var(--code-text) !important;
}

:deep(.hljs-keyword),
:deep(.hljs-selector-tag),
:deep(.hljs-subst) {
  color: var(--code-keyword) !important;
}

:deep(.hljs-string),
:deep(.hljs-doctag) {
  color: var(--code-string) !important;
}

:deep(.hljs-title),
:deep(.hljs-section),
:deep(.hljs-selector-id) {
  color: var(--code-title) !important;
}

:deep(.hljs-comment),
:deep(.hljs-quote) {
  color: var(--code-comment) !important;
}

:deep(.hljs-number),
:deep(.hljs-literal) {
  color: var(--code-number) !important;
}

:deep(.hljs-type),
:deep(.hljs-class .hljs-title) {
  color: var(--code-type) !important;
}

:deep(.hljs-attribute),
:deep(.hljs-name),
:deep(.hljs-regexp),
:deep(.hljs-link) {
  color: var(--code-attribute) !important;
}

:deep(.hljs-symbol),
:deep(.hljs-bullet) {
  color: var(--code-symbol) !important;
}

:deep(.hljs-built_in),
:deep(.hljs-builtin-name) {
  color: var(--code-builtin) !important;
}

:deep(.hljs-meta) {
  color: var(--code-meta) !important;
}

:deep(.hljs-deletion) {
  background: var(--code-deletion-bg) !important;
}

:deep(.hljs-addition) {
  background: var(--code-addition-bg) !important;
}

:deep(.hljs-emphasis) {
  font-style: italic !important;
}

:deep(.hljs-strong) {
  font-weight: bold !important;
}

@keyframes blink {
  from,
  to {
    opacity: 0;
  }
  50% {
    opacity: 1;
  }
}

.title-container {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.title-container::-webkit-scrollbar {
  display: none;
}

.title-text {
  background: linear-gradient(to right, var(--title-gradient-start), var(--title-gradient-end));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.code-compilation {
  font-family: monospace;
  text-align: left;
  width: 100%;
  color: var(--text-secondary);
}

.compilation-line {
  padding: 3px 0;
}

.compilation-line:last-child {
  color: #e0e0e0;
}

.compilation-cursor {
  display: inline-block;
  height: 1.2em;
  border-right: 3px solid rgba(248, 248, 242, 0.7);
  animation: blink 0.75s step-end infinite;
  vertical-align: text-bottom;
  margin-left: 2px;
  position: relative;
}

/* Statistics Panel Styles */
.statistics-panel {
  z-index: 10;
}

.stat-card {
  min-width: 140px;
  transition:
    transform 0.3s ease,
    box-shadow 0.3s ease;
  backdrop-filter: blur(10px);
  opacity: 0;
  transform: translateY(-20px);
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transition: left 0.5s;
}

.stat-card:hover::before {
  left: 100%;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.animate-fade-in {
  animation: fadeInUp 0.6s ease forwards;
}

@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stat-card:has([class*='pi-circle-fill']) .pi-circle-fill {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .statistics-panel {
    bottom: 2rem;
    left: 1rem;
    right: 1rem;
  }

  .stat-card {
    min-width: 120px;
    padding: 0.75rem !important;
  }

  .stat-card .text-lg {
    font-size: 1rem !important;
  }

  .stat-card .text-sm {
    font-size: 0.75rem !important;
  }

  .stat-card .text-xs {
    font-size: 0.625rem !important;
  }
}

@media (max-width: 480px) {
  .statistics-panel {
    bottom: 1rem;
    left: 0.5rem;
    right: 0.5rem;
  }

  .stat-card {
    min-width: 100px;
    padding: 0.5rem !important;
  }

  .stat-card .flex.gap-2 {
    gap: 0.5rem !important;
  }
}
</style>
