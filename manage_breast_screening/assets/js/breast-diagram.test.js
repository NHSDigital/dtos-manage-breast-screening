import { BreastDiagram } from './breast-diagram.js'
import { ImageMap } from './image-map.js'

jest.mock('./image-map', () => {
  const { Component } = jest.requireActual('nhsuk-frontend')

  return {
    ImageMap: class MockImageMap extends Component {
      addEventListener() {}
      config = { readOnly: false }
      static moduleName = 'app-image-map'
    }
  }
})

/**
 * Mock SVG point
 *
 * @type {DOMPoint}
 */
const dummyPoint = {
  x: 0,
  y: 0,
  w: null,
  z: null,
  matrixTransform: jest.fn(),
  toJSON: jest.fn()
}

/**
 * Mock breast feature
 *
 * @type {BreastFeature}
 */
const dummyFeature = {
  id: 'abc',
  name: 'Pending',
  x: dummyPoint.x,
  y: dummyPoint.y
}

beforeEach(() => {
  ImageMap.prototype.createPoint = jest.fn().mockReturnValue(dummyPoint)
  ImageMap.prototype.getPathById = jest.fn().mockReturnValue(null)
  ImageMap.prototype.setState = jest.fn()
})

describe('Breast diagram', () => {
  const diagramWithNoFeatures = `
    <form>
      <div data-module="app-breast-diagram">
        <input name="features" type="hidden" value="[]">
        <div data-module="app-image-map"></div>
      </div>
    </form>`

  const diagramWithAFeatureMarked = `
    <form>
      <div data-module="app-breast-diagram">
        <input name="features" type="hidden" value='[{"x": 0, "y": 0, "name": "Pending", "id": "abc"}]'>
        <div data-module="app-image-map"></div>
      </div>
    </form>`

  it('parses an empty list of values when the feature JSON is empty', () => {
    document.body.innerHTML = diagramWithNoFeatures
    const $root = document.querySelector(
      `[data-module='${BreastDiagram.moduleName}']`
    )

    const diagram = new BreastDiagram($root)
    expect(diagram.values).toHaveLength(0)
  })

  it('parses a feature when the feature JSON is non-empty', () => {
    document.body.innerHTML = diagramWithAFeatureMarked
    const $root = document.querySelector(
      `[data-module='${BreastDiagram.moduleName}']`
    )

    const diagram = new BreastDiagram($root)

    expect(diagram.values).toEqual([dummyFeature])
  })

  it('adds a feature', () => {
    document.body.innerHTML = diagramWithNoFeatures
    const $root = document.querySelector(
      `[data-module='${BreastDiagram.moduleName}']`
    )

    const diagram = new BreastDiagram($root)

    diagram.add(dummyFeature)

    expect(diagram.values).toEqual([dummyFeature])
  })

  it('removes a feature', () => {
    document.body.innerHTML = diagramWithAFeatureMarked
    const $root = document.querySelector(
      `[data-module='${BreastDiagram.moduleName}']`
    )

    const diagram = new BreastDiagram($root)

    diagram.remove(dummyFeature)

    expect(diagram.values).toEqual([])
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

/**
 * @import { BreastFeature } from './breast-diagram.js'
 */
