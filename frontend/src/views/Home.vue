<template>
  <div class="min-h-screen flex items-center justify-center code-background">
    <div class="text-left px-4 w-full max-w-2xl">
      <div class="title-container mb-8">
        <h1 class="text-2xl sm:text-3xl md:text-4xl font-bold tracking-wide">
          <span class="code-comment">/*</span>
          <span class="title-text">交大資工考古題系統</span>
          <span class="code-comment">*/</span>
        </h1>
      </div>
      <div class="code-container mt-8">
        <pre
          class="font-mono text-sm sm:text-base md:text-lg"
        ><span class="typewriter">{{ displayedText }}</span></pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";

const codeMemes = [
  `while (!coffee) {
  printf("Need more C0FF33\\n");
  productivity--;
  stress++;
}`,

  `// My code works - I don't know why
// My code doesn't work - I don't know why
// Programming in a nutshell`,

  `try {
  life();
} catch (err) {
  coffee.drink();
  life.retry();
}`,

  `function programmer() {
  eat();
  sleep();
  code();
  repeat();
}`,

  `// 99 bugs in the code
// Take one down, patch it around
// 127 bugs in the code`,

  `if (brain.available()) {
  code.write();
} else {
  coffee.consume();
}`,

  `// Two states of every programmer:
// 1. "I'm a coding genius"
// 2. "I have no idea what I'm doing"`,

  `class Student {
  constructor() {
    this.sleep = 0;
    this.stress = 100;
  }
}`,

  `// Debugging steps:
// 1. Cry
// 2. Google the error
// 3. Question career choices`,

  `const examTime = () => {
  panic();
  cram();
  return "Somehow passed";
};`,

  `// Elements of debugging:
// 20% skill
// 20% patience 
// 60% wondering how this ever worked`,

  `for (let i = 0; i < problems.length; i++) {
  if (problems[i].difficult) {
    return "I'll do it tomorrow";
  }
}`,

  `switch (mood) {
  case "happy": 
    code.works();
    break;
  default: // 99% of the time
    code.breaks();
}`,

  `// Comment your code
// Because what you write today,
// You won't understand tomorrow`,

  `let grades = [];
if (studyHours > 0) {
  grades.push("Pass");
} else {
  grades.push("Stack Overflow saves me");
}`,

  `function sleep() {
  return new Promise((resolve) => {
    // Never resolves for CS students
  });
}`,

  `// Why programmers prefer dark mode:
// 1. Less eye strain
// 2. Feels more "hacker-like"
// 3. Hides the tears`,

  `if (project.deadline.isToday()) {
  caffeine.consume(Infinity);
  efficiency.increase(100);
  sleep.disable();
}`,

  `class Assignment extends Torture {
  constructor() {
    super();
    this.deadline = "yesterday";
    this.complexity = "nightmare";
  }
}`,

  `// Types of errors:
// 1. Syntax errors
// 2. Logic errors
// 3. "It worked on my machine" errors`,

  `// Documentation is like good health insurance
// You hope you never need it,
// But you're glad it exists when you do`,

  `// Evolution of a programmer:
// Year 1: "I can solve anything!"
// Year 2: "I should plan before coding"
// Year 5: "Let's check Stack Overflow first"`,

  `const variable_names = [
  "temp", 
  "temp2", 
  "temp2Final",
  "temp2FinalREALLYFINAL",
  "temp2FinalREALLYFINAL_v2"
];`,

  `// Found in production code:
// Dear future me,
// I am sorry.
// Sincerely, past me.`,

  `let motivation = new Promise((resolve) => {
  setTimeout(resolve, Infinity);
  // Pending since 2020
});`,

  `// Before exam: "I got this!"
// During exam: "SELECT * FROM brain WHERE knowledge != NULL"
// After exam: "DROP TABLE sanity;"`,

  `function estimateProjectTime(hours) {
  return hours * 3; // The developer's constant
}`,
];

const selectedMeme = ref(
  codeMemes[Math.floor(Math.random() * codeMemes.length)]
);
const displayedText = ref("");
const fullText = computed(() => selectedMeme.value);

let charIndex = 0;
let typingInterval;

onMounted(() => {
  startTypewriter();
});

function startTypewriter() {
  clearInterval(typingInterval);
  charIndex = 0;
  displayedText.value = "";

  typingInterval = setInterval(() => {
    if (charIndex < fullText.value.length) {
      displayedText.value += fullText.value.charAt(charIndex);
      charIndex++;
    } else {
      clearInterval(typingInterval);
    }
  }, 50);
}
</script>

<style scoped>
.code-background {
  background-color: #1e1e1e;
  color: #f8f8f2;
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

.code-background > * {
  position: relative;
  z-index: 1;
}

.code-container {
  height: 180px;
  display: flex;
  align-items: flex-start;
}

pre {
  white-space: pre-wrap;
  text-align: left;
  background-color: #25272f;
  padding: 1.5rem;
  border-radius: 0.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin: 0;
  width: 100%;
  overflow: hidden;
  opacity: 0.8;
  color: rgba(248, 248, 242, 0.85);
}

.typewriter {
  border-right: 3px solid rgba(248, 248, 242, 0.7);
  animation: blink 0.75s step-end infinite;
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
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  margin-bottom: 2rem;
  text-align: center;
  -ms-overflow-style: none; /* IE and Edge */
  scrollbar-width: none; /* Firefox */
}

.title-container::-webkit-scrollbar {
  display: none;
}

.code-comment {
  color: #7c839b;
}

.title-text {
  background: linear-gradient(to right, #a2a9b0, #d5d9e0);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  padding: 0 0.5rem;
}
</style>
