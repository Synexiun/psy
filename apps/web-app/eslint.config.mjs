import js from '@eslint/js';
import tsParser from '@typescript-eslint/parser';
import tsPlugin from '@typescript-eslint/eslint-plugin';
import reactPlugin from 'eslint-plugin-react';
import discipline from '@disciplineos/eslint-plugin-discipline';

// Browser + Node globals that client components legitimately use.
// Next.js server components may also use fetch, crypto, etc. at the edge.
const BROWSER_GLOBALS = {
  window: 'readonly',
  document: 'readonly',
  navigator: 'readonly',
  fetch: 'readonly',
  setTimeout: 'readonly',
  clearTimeout: 'readonly',
  setInterval: 'readonly',
  clearInterval: 'readonly',
  localStorage: 'readonly',
  sessionStorage: 'readonly',
  URL: 'readonly',
  URLSearchParams: 'readonly',
  Blob: 'readonly',
  File: 'readonly',
  FormData: 'readonly',
  Request: 'readonly',
  Response: 'readonly',
  Headers: 'readonly',
  AbortController: 'readonly',
  AbortSignal: 'readonly',
  console: 'readonly',
  btoa: 'readonly',
  atob: 'readonly',
  crypto: 'readonly',
  performance: 'readonly',
  location: 'readonly',
  history: 'readonly',
  CustomEvent: 'readonly',
  Event: 'readonly',
  EventTarget: 'readonly',
  MutationObserver: 'readonly',
  IntersectionObserver: 'readonly',
  ResizeObserver: 'readonly',
  requestAnimationFrame: 'readonly',
  cancelAnimationFrame: 'readonly',
  HTMLElement: 'readonly',
  Element: 'readonly',
  Node: 'readonly',
  NodeList: 'readonly',
  SVGElement: 'readonly',
};

export default [
  js.configs.recommended,
  {
    files: ['src/**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        project: './tsconfig.json',
        ecmaFeatures: { jsx: true },
      },
      globals: { React: 'readonly', process: 'readonly', ...BROWSER_GLOBALS },
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
      react: reactPlugin,
    },
    settings: {
      react: { version: 'detect' },
    },
    rules: {
      ...tsPlugin.configs.recommended.rules,
      'react/react-in-jsx-scope': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
  {
    files: ['src/**/*.test.{ts,tsx}'],
    languageOptions: {
      globals: {
        describe: 'readonly',
        it: 'readonly',
        expect: 'readonly',
        beforeEach: 'readonly',
      },
    },
    rules: {
      'no-undef': 'off',
    },
  },
  {
    files: ['src/**/*.{ts,tsx}'],
    plugins: { '@disciplineos/discipline': discipline },
    rules: {
      '@disciplineos/discipline/no-physical-tailwind-properties': 'error',
      '@disciplineos/discipline/clinical-numbers-must-format': 'error',
      '@disciplineos/discipline/no-llm-on-crisis-route': 'error',
    },
  },
];
