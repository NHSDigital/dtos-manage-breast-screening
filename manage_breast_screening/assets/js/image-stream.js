import { Component, ElementError } from 'nhsuk-frontend'

/**
 * Connect to an SSE endpoint and update the image container when new images arrive.
 */
export class ImageStream extends Component {
  /**
   * @param {Element | null} $root - HTML element to use for component
   */
  constructor($root) {
    super($root)

    const streamUrl = this.$root.getAttribute('data-stream-url')
    if (!streamUrl) {
      throw new ElementError({
        element: $root,
        component: ImageStream,
        identifier: 'data-stream-url attribute'
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
}
