import js from '@eslint/js'
import globals from 'globals'
import eslintPluginTS from 'typescript-eslint'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'

// Destructure the parts we need from typescript-eslint
const { configs: tsConfigs, plugin: tsPlugin, parser: tsParser } = eslintPluginTS

export default [
  // Global ignore patterns
  {
    ignores: [
      '**/dist/**',
      '**/e2e/**',
      'playwright.config.ts',
    ],
  },

  // TypeScript / React files configuration
  {
    files: ['src/**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.browser,
        React: 'readonly', // React 19 using ES modules doesn't need imports
      },
      parser: tsParser,
      parserOptions: {
        project: './tsconfig.app.json',
      },
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
      react,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
    rules: {
      // Base recommended rules
      ...js.configs.recommended.rules,
      ...tsConfigs.recommended.rules,
      ...tsConfigs.stylistic.rules,

      // React and React Hooks recommended rules
      ...react.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,

      // TypeScript rules for modern projects
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/explicit-function-return-type': ['error', {
        allowExpressions: true,
        allowHigherOrderFunctions: true,
        allowTypedFunctionExpressions: true,
      }],
      '@typescript-eslint/consistent-type-imports': ['error', {
        prefer: 'type-imports',
        fixStyle: 'separate-type-imports',
      }],
      '@typescript-eslint/no-unused-vars': ['error', { 
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
      }],
      '@typescript-eslint/consistent-type-exports': ['error', {
        fixMixedExportsWithInlineTypeSpecifier: true,
      }],

      // React specific rules for React 19
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'off', // TypeScript handles prop types
      'react/jsx-uses-react': 'off',
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],

      // General code quality rules
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'prefer-const': 'error',
      'eqeqeq': ['error', 'smart'],
    },
  },

  // JavaScript/JSX files (fallback)
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.browser,
        React: 'readonly',
      },
    },
    rules: {
      ...js.configs.recommended.rules,
      'react/react-in-jsx-scope': 'off',
      'no-console': ['warn', { allow: ['warn', 'error'] }],
    },
  },
]
