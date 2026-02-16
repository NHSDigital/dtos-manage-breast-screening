import { BreastDiagram } from './breast-diagram.js'
import { ImageMap } from './image-map.js'

jest.mock('./image-map')

// Mock out ImageMap so it always returns this dummy region
const dummyRegion = {
  id: '123',
  label: 'abc',
  point: {
    x: 0,
    y: 0,
    w: null,
    z: null,
    matrixTransform: jest.fn(),
    toJSON: jest.fn()
  },
  $path: null
}

beforeEach(() => {
  ImageMap.prototype.createRegion = jest.fn().mockReturnValue(dummyRegion)
})

describe('Breast diagram', () => {
  const diagramWithNoFeatures = `
    <form data-module="app-breast-diagram">
      <div data-module="app-image-map"></div>
      <input name="features" type="hidden" value="[]">
    </form>`

  const diagramWithAFeatureMarked = `
    <form data-module="app-breast-diagram">
      <div data-module="app-image-map"></div>
      <input name="features" type="hidden" value='[{"x": 0, "y": 0, "name": "Pending", "id": "abc"}]'>
    </form>`

  it('parses an empty list of features when the feature JSON is empty', () => {
    document.body.innerHTML = diagramWithNoFeatures
    const $root = document.querySelector(
      `[data-module='${BreastDiagram.moduleName}']`
    )

    const diagram = new BreastDiagram($root)
    expect(diagram.features).toHaveLength(0)
  })

  it('parses a feature when the feature JSON is non-empty', () => {
    document.body.innerHTML = diagramWithAFeatureMarked
    const $root = document.querySelector(
      `[data-module='${BreastDiagram.moduleName}']`
    )

    const diagram = new BreastDiagram($root)

    expect(diagram.features).toEqual([
      {
        name: 'Pending',
        region: dummyRegion
      }
    ])
  })

  it('adds a feature when clicked', () => {
    document.body.innerHTML = diagramWithNoFeatures
    const $root = document.querySelector(
      `[data-module='${BreastDiagram.moduleName}']`
    )

    const diagram = new BreastDiagram($root)

    diagram.onUpdate('active', dummyRegion)

    expect(diagram.features).toEqual([
      {
        name: 'Pending',
        region: dummyRegion
      }
    ])
  })

  it('writes JSON to the input', () => {
    document.body.innerHTML = diagramWithAFeatureMarked
    const $root = document.querySelector(
      `[data-module='${BreastDiagram.moduleName}']`
    )

    /** @type {HTMLInputElement} */
    const $input = $root.querySelector('input[name="features"]')

    const diagram = new BreastDiagram($root)
    diagram.write()

    expect($input.value).toBe('[{"x":0,"y":0,"name":"Pending","id":"abc"}]')
  })
})
