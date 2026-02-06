import { createAll } from 'nhsuk-frontend'

import { ImageStream } from './image-stream.js'

describe('ImageStream', () => {
  /** @type {jest.Mock} */
  let MockEventSource

  /** @type {Record<string, (...args: unknown[]) => void>} */
  let eventListeners

  /** @type {jest.Mock} */
  let closeMock

  beforeEach(() => {
    eventListeners = {}
    closeMock = jest.fn()

    MockEventSource = jest.fn().mockImplementation(() => ({
      addEventListener: jest.fn((event, handler) => {
        eventListeners[event] = handler
      }),
      close: closeMock
    }))

    Object.defineProperty(window, 'EventSource', {
      configurable: true,
      writable: true,
      value: MockEventSource
    })

    jest.spyOn(console, 'log').mockImplementation(() => {})
    jest.spyOn(console, 'warn').mockImplementation(() => {})
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('connects to the stream URL on initialization', () => {
    document.body.innerHTML = `
      <div data-module="${ImageStream.moduleName}" data-stream-url="/api/images/stream">
        <p>No images yet</p>
      </div>
    `

    createAll(ImageStream)

    expect(MockEventSource).toHaveBeenCalledWith('/api/images/stream')
  })

  it('logs an error when data-stream-url attribute is missing', () => {
    document.body.innerHTML = `
      <div data-module="${ImageStream.moduleName}">
        <p>No images yet</p>
      </div>
    `

    createAll(ImageStream)

    expect(console.log).toHaveBeenCalledWith(
      expect.objectContaining({
        message: expect.stringContaining('data-stream-url')
      })
    )
  })

  it('updates innerHTML when receiving an images event', () => {
    document.body.innerHTML = `
      <div data-module="${ImageStream.moduleName}" data-stream-url="/api/images/stream">
        <p>No images yet</p>
      </div>
    `

    createAll(ImageStream)

    const container = document.querySelector(
      `[data-module="${ImageStream.moduleName}"]`
    )

    const newContent = '<div class="image-grid"><img src="/img/1.jpg"></div>'
    eventListeners['images']({ data: newContent })

    expect(container.innerHTML).toBe(newContent)
  })

  it('logs a warning on connection error', () => {
    document.body.innerHTML = `
      <div data-module="${ImageStream.moduleName}" data-stream-url="/api/images/stream">
        <p>No images yet</p>
      </div>
    `

    createAll(ImageStream)

    eventListeners['error']()

    expect(console.warn).toHaveBeenCalledWith(
      'ImageStream: SSE connection error, reconnecting...'
    )
  })

  it('closes the EventSource when disconnect is called', () => {
    document.body.innerHTML = `
      <div data-module="${ImageStream.moduleName}" data-stream-url="/api/images/stream">
        <p>No images yet</p>
      </div>
    `

    const [component] = createAll(ImageStream)

    component.disconnect()

    expect(closeMock).toHaveBeenCalled()
    expect(component.eventSource).toBeNull()
  })

  it('does not throw when disconnect is called without an active connection', () => {
    document.body.innerHTML = `
      <div data-module="${ImageStream.moduleName}" data-stream-url="/api/images/stream">
        <p>No images yet</p>
      </div>
    `

    const [component] = createAll(ImageStream)
    component.eventSource = null

    expect(() => component.disconnect()).not.toThrow()
  })
})
