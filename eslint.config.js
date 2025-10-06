import { join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import { includeIgnoreFile } from '@eslint/compat'
import eslint from '@eslint/js'
import pluginMarkdown from '@eslint/markdown'
import { defineConfig, globalIgnores } from 'eslint/config'
import configPrettier from 'eslint-config-prettier/flat'
import pluginESx from 'eslint-plugin-es-x'
import pluginImport from 'eslint-plugin-import'
import pluginJest from 'eslint-plugin-jest'
import pluginJestDom from 'eslint-plugin-jest-dom'
import pluginJsdoc from 'eslint-plugin-jsdoc'
import pluginNode from 'eslint-plugin-n'
import pluginPromise from 'eslint-plugin-promise'
import globals from 'globals'
import pluginTypeScript from 'typescript-eslint'

const rootPath = resolve(fileURLToPath(new URL('.', import.meta.url)))
const gitignorePath = join(rootPath, '.gitignore')

export default defineConfig([
  {
    files: ['**/*.{cjs,js,mjs}'],
    extends: [
      eslint.configs.recommended,
      pluginImport.flatConfigs.recommended,
      pluginImport.flatConfigs.typescript,
      pluginJsdoc.configs['flat/recommended-typescript-flavor'],
      pluginPromise.configs['flat/recommended'],
      pluginTypeScript.configs.strict,
      pluginTypeScript.configs.stylistic,
      configPrettier
    ],
    languageOptions: {
      parserOptions: {
        ecmaVersion: 'latest',
        projectService: true,
        tsconfigRootDir: rootPath
      }
    },
    rules: {
      // Check import or require statements are A-Z ordered
      'import/order': [
        'error',
        {
          'alphabetize': { order: 'asc' },
          'newlines-between': 'always'
        }
      ],

      // Check for valid formatting
      'jsdoc/check-line-alignment': [
        'warn',
        'never',
        {
          wrapIndent: '  '
        }
      ],

      // JSDoc blocks are optional by default
      'jsdoc/require-jsdoc': 'off',

      // Require hyphens before param description
      // Aligns with TSDoc style: https://tsdoc.org/pages/tags/param/
      'jsdoc/require-hyphen-before-param-description': 'warn',

      // JSDoc @param required in (optional) blocks but
      // @param description is not necessary by default
      'jsdoc/require-param-description': 'off',
      'jsdoc/require-param-type': 'error',
      'jsdoc/require-param': 'off',

      // JSDoc @returns is optional
      'jsdoc/require-returns-description': 'off',
      'jsdoc/require-returns-type': 'off',
      'jsdoc/require-returns': 'off',

      // Maintain new line after description
      'jsdoc/tag-lines': [
        'warn',
        'never',
        {
          startLines: 1
        }
      ],

      // Automatically use template strings
      'no-useless-concat': 'error',
      'prefer-template': 'error',

      // Flow control – avoid continue and else blocks after return statements
      // in if statements
      'no-continue': 'error',
      'no-else-return': 'error',

      // Avoid hard to read multi assign statements
      'no-multi-assign': 'error',

      // Prefer rules that are type aware
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': ['error']
    }
  },
  {
    // CommonJS modules allow require statements
    files: ['**/*.cjs'],
    rules: {
      '@typescript-eslint/no-require-imports': 'off',
      '@typescript-eslint/no-var-requires': 'off'
    }
  },
  {
    // ES modules mandatory file extensions
    files: ['**/*.{js,mjs}'],
    rules: {
      'import/extensions': [
        'error',
        'always',
        {
          ignorePackages: true,
          pattern: {
            cjs: 'always',
            js: 'always',
            mjs: 'always'
          }
        }
      ]
    }
  },
  {
    // Configure ESLint for Node.js
    files: ['**/*.{cjs,js,mjs}'],
    ignores: ['**/assets/js/**'],
    extends: [pluginNode.configs['flat/recommended']],
    languageOptions: {
      globals: globals.node
    }
  },
  {
    // Configure ESLint for browsers
    files: ['**/assets/js/**/*.js'],
    ignores: ['**/*.test.js'],
    extends: [
      pluginTypeScript.configs.strictTypeChecked,
      pluginTypeScript.configs.stylisticTypeChecked,
      pluginESx.configs['flat/restrict-to-es2015']
    ],
    languageOptions: {
      globals: globals.browser,
      parserOptions: {
        // Note: Allow ES2015 for import/export syntax
        ecmaVersion: 2015
      }
    },
    rules: {
      // Allow void return shorthand in arrow functions
      '@typescript-eslint/no-confusing-void-expression': [
        'error',
        {
          ignoreArrowShorthand: true
        }
      ],

      // Check type support for template string implicit `.toString()`
      '@typescript-eslint/restrict-template-expressions': [
        'error',
        {
          allowBoolean: true,
          allowNumber: true
        }
      ],

      // Promise.prototype.catch() errors cannot be typed in JavaScript
      '@typescript-eslint/use-unknown-in-catch-callback-variable': 'off',

      // Babel transpiles ES2020 class fields
      'es-x/no-class-fields': 'off',

      // Babel transpiles ES2022 class instance fields
      'es-x/no-class-instance-fields': 'off',

      // Babel transpiles ES2022 class static fields
      'es-x/no-class-static-fields': 'off',

      // ES modules include ES2016 '[].includes()' coverage
      // https://browsersl.ist/#q=supports+es6-module+and+not+supports+array-includes
      'es-x/no-array-prototype-includes': 'off',

      // Babel transpiles ES2020 `??` nullish coalescing
      'es-x/no-nullish-coalescing-operators': 'off',

      // ES modules include ES2017 'Object.entries()' coverage
      // https://browsersl.ist/#q=supports+es6-module+and+not+supports+object-entries
      'es-x/no-object-entries': 'off',

      // Babel transpiles ES2020 optional chaining
      'es-x/no-optional-chaining': 'off',

      // JSDoc blocks are optional but must be valid
      'jsdoc/require-jsdoc': [
        'error',
        {
          enableFixer: false,
          require: {
            FunctionDeclaration: false
          }
        }
      ],

      // JSDoc @param types are mandatory for JavaScript
      'jsdoc/require-param-description': 'off',
      'jsdoc/require-param-type': 'error',
      'jsdoc/require-param': 'off',

      // JSDoc @returns is optional
      'jsdoc/require-returns-description': 'off',
      'jsdoc/require-returns-type': 'off',
      'jsdoc/require-returns': 'off'
    }
  },
  {
    // Configure ESLint in test files
    files: [
      '**/*.test.{cjs,js,mjs}',
      'jest?(.*).config.*',
      'jest?(.*).setup.*'
    ],
    extends: [
      pluginJest.configs['flat/recommended'],
      pluginJest.configs['flat/style'],
      pluginJestDom.configs['flat/recommended']
    ],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...pluginJest.environments.globals.globals
      }
    },
    rules: {
      '@typescript-eslint/no-empty-function': 'off',
      'promise/always-return': 'off',
      'promise/catch-or-return': 'off'
    }
  },
  {
    // Configure ESLint in Markdown files
    files: ['**/*.md'],
    extends: [
      pluginMarkdown.configs.recommended,
      pluginMarkdown.configs.processor
    ],
    language: 'markdown/gfm',
    plugins: { markdown: pluginMarkdown }
  },
  {
    // Configure ESLint in Markdown code blocks
    files: ['**/*.md/*.{cjs,js,mjs}'],
    extends: [pluginTypeScript.configs.disableTypeChecked],
    languageOptions: {
      globals: globals.browser
    },
    rules: {
      '@typescript-eslint/no-unused-vars': 'off',
      'import/no-unresolved': 'off',
      'n/no-missing-import': 'off',
      'prefer-template': 'off'
    }
  },
  globalIgnores([
    '**/compiled/**',
    '**/coverage/**',
    '**/staticfiles/**',
    'htmlcov/**',
    '.mypy_cache/**',

    // Enable dotfile linting
    '!.*',
    'node_modules',
    'node_modules/.*',

    // Prevent CHANGELOG history changes
    'CHANGELOG.md'
  ]),
  includeIgnoreFile(gitignorePath, 'Imported .gitignore patterns')
])
