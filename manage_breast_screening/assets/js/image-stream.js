import { ConfigurableComponent, ElementError } from 'nhsuk-frontend'

/**
 * Connect to an SSE endpoint and update the image container when new images arrive.
 *
 * @augments {ConfigurableComponent<ImageStreamConfig>}
 */
export class ImageStream extends ConfigurableComponent {
  /**
   * @param {Element | null} $root - HTML element to use for component
   * @param {Partial<ImageStreamConfig>} [config] - Image stream config
   */
  constructor($root, config) {
    super($root, config)

    const { streamUrl } = this.config
    if (!streamUrl) {
      throw new ElementError({
        component: ImageStream,
        identifier: 'Root element (`$root`) attribute (`data-stream-url`)'
      })
    }

    this.streamUrl = streamUrl
    this.eventSource = null
    this.connect()
  }

  connect() {
    this.eventSource = new EventSource(this.streamUrl)

    this.eventSource.addEventListener(
      'images',
      /** @param {MessageEvent<string>} event */ (event) => {
        this.$root.innerHTML = event.data
      }
    )

    this.eventSource.addEventListener('error', () => {
      console.warn('ImageStream: SSE connection error, reconnecting...')
    })
  }

  disconnect() {
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
  }

  /**
   * Name for the component used when initialising using data-module attributes
   */
  static moduleName = 'app-image-stream'

  /**
   * Image stream default config
   *
   * @see {@link ImageStreamConfig}
   * @constant
   * @type {ImageStreamConfig}
   */
  static defaults = Object.freeze({})

  /**
   * Image stream config schema
   *
   * @constant
   * @satisfies {Schema<ImageStreamConfig>}
   */
  static schema = Object.freeze({
    properties: {
      streamUrl: { type: 'string' }
    }
  })
}

/**
 * Image stream config
 *
 * @typedef {object} ImageStreamConfig
 * @property {string} [streamUrl] - The SSE endpoint URL for streaming images
 */

/**
 * @import { Schema } from 'nhsuk-frontend/dist/nhsuk/common/configuration/index.mjs'
 */
