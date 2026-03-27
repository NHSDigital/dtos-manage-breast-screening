import { userEvent } from '@testing-library/user-event'
import { createAll } from 'nhsuk-frontend'

import { ImageMap } from './image-map.js'

describe('Image map', () => {
  const user = userEvent.setup()

  const emptySvg = `<div data-module="app-image-map">
    <svg class="app-image-map__svg"></svg>
  </div>`

  const multiPathSvg = `<div data-module="app-image-map">
    <svg class="app-image-map__svg" viewBox="0 0 800 400">
      <path class="fake_id_1" d="M452.25,344.67c-19.02-15.94-34.28-38.03-47.06-66.66h-5.19v121.99h160.32v-23.33c-2.01.06-4.06.09-6.13.09-43.13,0-76.02-10.35-101.94-32.09Z" fill="none">
        <title>a</title>
      </path>
      <path class="fake_id_2" d="M420.59,234.02h-20.59v43.99h5.19c12.78,28.63,28.04,50.72,47.06,66.66l21.62-28.95c-28.17-21.35-44.51-52.66-53.28-81.7Z" fill="none">
        <title>b</title>
      </path>
    </svg>
  </div>
  `

  it("rejects SVGs if the selectors don't match anything", () => {
    document.body.innerHTML = emptySvg

    expect(() =>
      createAll(
        ImageMap,
        {
          imageClass: 'app-image-map__svg',
          selectors: ['path']
        },
        {
          onError(error) {
            throw error
          }
        }
      )
    ).toThrow(
      `${ImageMap.moduleName}: Image paths and polygons (\`path\`) not found`
    )
  })

  it('parses the paths from the image', () => {
    document.body.innerHTML = multiPathSvg

    const [component] = createAll(ImageMap, {
      imageClass: 'app-image-map__svg',
      selectors: ['path', 'polygon']
    })

    expect(component.$paths).toHaveLength(2)
  })

  it('notifies on hover', async () => {
    document.body.innerHTML = multiPathSvg

    const [component] = createAll(ImageMap, {
      imageClass: 'app-image-map__svg',
      selectors: ['path', 'polygon']
    })

    const callback = jest.fn()
    component.addEventListener('hover', callback)

    await user.hover(component.$paths[0])
    expect(callback).toHaveBeenCalled()
  })

  it('notifies on create', async () => {
    document.body.innerHTML = multiPathSvg

    const [component] = createAll(ImageMap, {
      imageClass: 'app-image-map__svg',
      selectors: ['path', 'polygon']
    })

    const callback = jest.fn()
    component.addEventListener('create', callback)

    await user.click(component.$paths[0])
    expect(callback).toHaveBeenCalled()
  })
})
