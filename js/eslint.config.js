import js from '@eslint/js'
import globals from 'globals'
import tseslint from 'typescript-eslint'

// 2 spaces, single quotes, no semicolons, explicit return types.
export default tseslint.config(
  { ignores: ['**/node_modules/**', '**/dist/**', '**/generated/**'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    languageOptions: { globals: { ...globals.node, ...globals.browser } },
    rules: {
      indent: ['error', 2, { SwitchCase: 1 }],
      quotes: ['error', 'single', { avoidEscape: true }],
      semi: ['error', 'never'],
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_', ignoreRestSiblings: true }],
    },
  },
  {
    files: ['**/*.ts', '**/*.tsx'],
    rules: {
      '@typescript-eslint/explicit-function-return-type': ['error', { allowExpressions: true }],
    },
  },
)
