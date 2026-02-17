import { babel } from '@rollup/plugin-babel'
import commonjs from '@rollup/plugin-commonjs'
import { nodeResolve } from '@rollup/plugin-node-resolve'
import terser from '@rollup/plugin-terser'

/**
 * Rollup config
 *
 * @type {RollupOptions}
 */
export default {
  input: 'manage_breast_screening/assets/js/index.js',

  output: {
    compact: true,
    format: 'es',
    file: 'manage_breast_screening/assets/compiled/js/bundle.js',

    plugins: [
      // Minification using terser
      terser({
        // Allow Terser to remove @preserve comments
        format: { comments: false },
        mangle: {
          keep_classnames: true,
          keep_fnames: true
        },

        // Include sources content from source maps to inspect
        // NHS.UK frontend and other dependencies' source code
        sourceMap: {
          includeSources: true
        },

        // Compatibility workarounds
        safari10: true
      })
    ]
  },
  plugins: [
    nodeResolve(),
    commonjs(),
    babel({
      babelHelpers: 'bundled'
    })
  ]
}

/**
 * @import { RollupOptions } from 'rollup'
 */
