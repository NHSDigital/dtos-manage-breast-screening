import autoprefixer from 'autoprefixer'
import cssnano from 'cssnano'

/**
 * PostCSS config
 *
 * @type {ProcessOptions & { plugins: AcceptedPlugin[] }}
 */
export default {
  map: {
    inline: false
  },
  plugins: [
    // Add vendor prefixes
    autoprefixer({
      env: 'stylesheets'
    }),

    // Minify CSS
    cssnano({
      preset: ['default', { env: 'stylesheets' }]
    })
  ]
}

/**
 * @import { AcceptedPlugin, ProcessOptions } from 'postcss'
 */
