import { userEvent } from '@testing-library/user-event'

import { ImageMap } from './image-map.js'

describe('Image map', () => {
  const user = userEvent.setup()
  const emptySvg = '<div data-module="app-image-map"><svg></svg></div>'
  const multiPathSvg = `<div data-module="app-image-map">
    <svg viewBox="0 0 800 400">
      <path aria-label="a" d="M452.25,344.67c-19.02-15.94-34.28-38.03-47.06-66.66h-5.19v121.99h160.32v-23.33c-2.01.06-4.06.09-6.13.09-43.13,0-76.02-10.35-101.94-32.09Z" fill="none"/>
      <path aria-label="b" d="M420.59,234.02h-20.59v43.99h5.19c12.78,28.63,28.04,50.72,47.06,66.66l21.62-28.95c-28.17-21.35-44.51-52.66-53.28-81.7Z" fill="none"/>
    </svg>
  </div>
  `

  it("rejects SVGs if the selectors don't match anything", () => {
    document.body.innerHTML = emptySvg
    const $root = document.querySelector(
      `[data-module='${ImageMap.moduleName}']`
    )

    expect(
      () =>
        new ImageMap($root, {
          selectors: ['path']
        })
    ).toThrow(
      `${ImageMap.moduleName}: Image paths and polygons (\`path\`) not found`
    )
  })

  it('parses the paths from the image', () => {
    document.body.innerHTML = multiPathSvg
    const $root = document.querySelector('[data-module="app-image-map"]')
    const map = new ImageMap($root, { selectors: ['path', 'polygon'] })

    expect(map.$paths).toHaveLength(2)
  })

  it('notifies on highlight', async () => {
    document.body.innerHTML = multiPathSvg
    const $root = document.querySelector('[data-module="app-image-map"]')
    const map = new ImageMap($root, { selectors: ['path', 'polygon'] })

    const callback = jest.fn()
    map.onUpdate = callback

    await user.hover(map.$paths[0])

    expect(callback).toHaveBeenCalled()
    expect(callback.mock.calls).toHaveLength(1)
    expect(callback.mock.calls[0][0]).toBe('highlight')
  })

  it('notifies on click', async () => {
    document.body.innerHTML = multiPathSvg
    const $root = document.querySelector('[data-module="app-image-map"]')
    const map = new ImageMap($root, { selectors: ['path', 'polygon'] })

    const callback = jest.fn()
    map.onUpdate = callback

    await user.click(map.$paths[0])

    expect(callback).toHaveBeenCalled()
    expect(callback.mock.calls).toHaveLength(2)
    expect(callback.mock.calls[1][0]).toBe('active')
  })
})
