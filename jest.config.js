/**
 * Jest project config defaults
 *
 * @type {ProjectConfig}
 */
const config = {
  cacheDirectory: '<rootDir>/.cache/jest',
  coveragePathIgnorePatterns: ['.eslintrc.js', '.test.(cjs|js)'],

  // Enable Babel transforms until Jest supports ESM and `import()`
  // See: https://jestjs.io/docs/ecmascript-modules
  transform: {
    '^.+\\.(cjs|js)$': ['babel-jest', { rootMode: 'upward' }]
  }
}

/**
 * Jest config
 *
 * @type {Config}
 */
export default {
  collectCoverageFrom: ['**/assets/js/**/*.{cjs,js}'],
  coverageProvider: 'v8',
  projects: [
    {
      ...config,
      displayName: 'JavaScript behaviour tests',
      setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
      testEnvironment: 'jsdom',
      testMatch: ['<rootDir>/**/*.test.{cjs,js}']
    }
  ],

  // Reset mocks between tests
  resetMocks: true,
  resetModules: true,
  restoreMocks: true,
  clearMocks: true,

  // Enable GitHub Actions reporter UI and xunit
  reporters: [
    'default',
    'github-actions',
    [
      'jest-junit',
      {
        outputFile: 'reports/test-js-units.xml'
      }
    ]
  ]
}

/**
 * @typedef {Exclude<Config['projects'][0], string>} ProjectConfig
 */

/**
 * @import { Config } from 'jest'
 */
