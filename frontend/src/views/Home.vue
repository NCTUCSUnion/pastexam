<template>
  <div class="h-full flex items-center justify-center code-background">
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
        ><code class="typewriter" v-html="highlightedCode"></code></pre>

        <div class="language-badge">{{ language }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watchEffect } from "vue";
import hljs from "highlight.js";
import "highlight.js/styles/atom-one-dark.css"; // You can choose different themes

const codeMemes = [
  {
    code: `while (!coffee) {
  printf("Need more C0FF33\\n");
  productivity--;
  stress++;
}`,
    language: "c",
  },
  {
    code: `# Python developers be like
import solution
from stackoverflow import code

def actual_work():
    pass  # TODO: Implement later`,
    language: "python",
  },
  {
    code: `try {
  life();
} catch (err) {
  coffee.drink();
  life.retry();
}`,
    language: "javascript",
  },
  {
    code: `/* CSS: The blessing and curse */
#submit-button {
  display: block;
  margin: 0 auto;
  position: relative !important;
  z-index: 999; /* Please work */
}`,
    language: "css",
  },
  {
    code: `// 99 bugs in the code
// Take one down, patch it around
// 127 bugs in the code`,
    language: "javascript",
  },
  {
    code: `def time_estimate(task):
    """Estimates completion time"""
    realistic = calculate_hours(task)
    return realistic * 3  # Developer's constant`,
    language: "python",
  },
  {
    code: `if (brain.available()) {
  code.write();
} else {
  coffee.consume();
}`,
    language: "javascript",
  },
  {
    code: `class Student {
  constructor() {
    this.sleep = 0;
    this.stress = 100;
  }
}`,
    language: "javascript",
  },
  {
    code: `SELECT motivation
FROM student
WHERE deadline < CURRENT_DATE
AND hours_slept > 3
-- Returns empty set`,
    language: "sql",
  },
  {
    code: `const examTime = () => {
  panic();
  cram();
  return "Somehow passed";
};`,
    language: "javascript",
  },
  {
    code: `fn main() {
    let code_quality = 100;
    let deadline = true;
    
    if deadline {
        println!("Who needs clean code anyway?");
        code_quality -= 80;
    }
}`,
    language: "rust",
  },
  {
    code: `// Bash script for finals week
#!/bin/bash

while true; do
  if [ "$(coffee_level)" -lt 50 ]; then
    echo "CRITICAL: Coffee low!"
    make_coffee
  fi
done`,
    language: "bash",
  },
  {
    code: `switch (mood) {
  case "happy": 
    code.works();
    break;
  default: // 99% of the time
    code.breaks();
}`,
    language: "javascript",
  },
  {
    code: `package main

import "fmt"

func main() {
    expectations := []string{"Easy A"}
    reality := []string{"Curve graded", "All-nighter"}
    fmt.Println("Gap:", len(reality) - len(expectations))
}`,
    language: "go",
  },
  {
    code: `class MyCat < Pet
  def initialize
    @helps_coding = false
  end
  
  def sit_on_keyboard
    puts "kjasdhIHDIhaoiy87yh" # Commit this
  end
end`,
    language: "ruby",
  },
  {
    code: `function sleep() {
  return new Promise((resolve) => {
    // Never resolves for CS students
  });
}`,
    language: "javascript",
  },
  {
    code: `<!-- Types of HTML elements -->
<div>What I wanted</div>
<div style="position:absolute;top:-500px;">
  What the designer wanted
</div>
<marquee>What the client asked for</marquee>`,
    language: "html",
  },
  {
    code: `#include <iostream>

void debugCode() {
  std::cout << "This should work..." << std::endl;
  std::cout << "WHY doesn't it work?" << std::endl;
  std::cout << "Oh, semicolon missing" << std::endl;
}`,
    language: "cpp",
  },
  {
    code: `<?php
// The official debugging technique
@$result = dangerous_function();
echo $result ?? "It broke again!";
// Add more @ symbols until it works
?>`,
    language: "php",
  },
  {
    code: `// Types of errors:
// 1. Syntax errors
// 2. Logic errors 
// 3. "It worked on my machine" errors`,
    language: "javascript",
  },
  {
    code: `fun main() {
    val states = listOf("It works!", "It doesn't work", 
                      "WHY doesn't it work??")
    println("Current: \${states.random()}")
}`,
    language: "kotlin",
  },
  {
    code: `// Found in production code:
// Dear future me,
// I am sorry.
// Sincerely, past me.`,
    language: "javascript",
  },
  {
    code: `let motivation = new Promise((resolve) => {
  setTimeout(resolve, Infinity);
  // Pending since 2020
});`,
    language: "javascript",
  },
  {
    code: `-- SQL: Debugging in production
BEGIN TRANSACTION;
UPDATE users SET admin = TRUE;
-- TODO: Add WHERE clause
-- ...forgot to add it
COMMIT;`,
    language: "sql",
  },
  {
    code: `function estimateProjectTime(hours) {
  return hours * 3; // The developer's constant
}`,
    language: "javascript",
  },
];

const selectedMeme = ref(
  codeMemes[Math.floor(Math.random() * codeMemes.length)]
);
const displayedText = ref("");
const highlightedCode = ref("");
const fullText = computed(() => selectedMeme.value.code);
const language = computed(() => selectedMeme.value.language);

let charIndex = 0;
let typingInterval;

onMounted(() => {
  startTypewriter();
});

function startTypewriter() {
  clearInterval(typingInterval);
  charIndex = 0;
  displayedText.value = "";
  highlightedCode.value = "";

  typingInterval = setInterval(() => {
    if (charIndex < fullText.value.length) {
      displayedText.value += fullText.value.charAt(charIndex);
      charIndex++;

      highlightedCode.value = hljs.highlight(displayedText.value, {
        language: language.value,
      }).value;
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
  position: relative;
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
}

.typewriter::after {
  content: "";
  border-right: 3px solid rgba(248, 248, 242, 0.7);
  animation: blink 0.75s step-end infinite;
}

.language-badge {
  position: absolute;
  top: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.9);
  opacity: 0.7;
  padding: 2px 8px;
  border-radius: 0 0.5rem 0 0.5rem;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 1px;
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
