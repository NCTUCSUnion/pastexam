import js from '@eslint/js'
import globals from 'globals'
import vue from 'eslint-plugin-vue'
import vueParser from 'vue-eslint-parser'
import json from '@eslint/json'
import tseslint from 'typescript-eslint'

export default [
  { languageOptions: { globals: globals.browser } },

  js.configs.recommended,

  ...vue.configs['flat/essential'],

  ...tseslint.configs.recommended,

  json.configs.recommended,

  {
    files: ['**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        parser: tseslint.parser,
        extraFileExtensions: ['.vue'],
      },
    },
    plugins: { '@typescript-eslint': tseslint.plugin },
  },
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        project: false,
      },
    },
    plugins: { '@typescript-eslint': tseslint.plugin },
  },
]
