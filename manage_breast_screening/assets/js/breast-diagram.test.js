import { createAll } from 'nhsuk-frontend'

import { BreastDiagram } from './breast-diagram.js'
import { ImageMap } from './image-map.js'

jest.mock('./image-key', () => {
  const { Component } = jest.requireActual('nhsuk-frontend')

  return {
    ImageKey: class MockImageKey extends Component {
      addEventListener() {}
      render() {}
      static moduleName = 'app-image-key'
    }
  }
})

jest.mock('./image-map', () => {
  const { Component } = jest.requireActual('nhsuk-frontend')

  return {
    ImageMap: class MockImageMap extends Component {
      addEventListener() {}
      unsetState() {}
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
  x: 133,
  y: 82,
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
  id: 'pending',
  region_id: 'right_upper_outer',
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
      <input name="features" type="hidden" value="[]">
      <div data-module="app-breast-diagram">
        <template class="app-js-template-image-marker">
          <a class="app-image-marker" href="#">?</a>
        </template>
        <div data-module="app-image-map"></div>
        <div data-module="app-image-key"></div>
      </div>
    </form>`

  const diagramWithAFeatureMarked = `
    <form>
      <input name="features" type="hidden" value='[{"id": "pending", "region_id": "right_upper_outer", "x": 133, "y": 82}]'>
      <div data-module="app-breast-diagram">
        <template class="app-js-template-image-marker">
          <a class="app-image-marker" href="#">?</a>
        </template>
        <div data-module="app-image-map"></div>
        <div data-module="app-image-key"></div>
      </div>
    </form>`

  it('parses an empty list of values when the feature JSON is empty', () => {
    document.body.innerHTML = diagramWithNoFeatures

    const [component] = createAll(BreastDiagram)

    expect(component.values).toHaveLength(0)
  })

  it('parses a feature when the feature JSON is non-empty', () => {
    document.body.innerHTML = diagramWithAFeatureMarked

    const [component] = createAll(BreastDiagram)

    expect(component.values).toEqual([dummyFeature])
  })

  it('adds a feature', () => {
    document.body.innerHTML = diagramWithNoFeatures

    const [component] = createAll(BreastDiagram)
    component.add(dummyFeature)

    expect(component.values).toEqual([dummyFeature])
  })

  it('removes a feature', () => {
    document.body.innerHTML = diagramWithAFeatureMarked

    const [component] = createAll(BreastDiagram)
    component.remove(dummyFeature)

    expect(component.values).toEqual([])
  })

  it('writes JSON to the input', () => {
    document.body.innerHTML = diagramWithAFeatureMarked

    const [component] = createAll(BreastDiagram)
    component.write()

    expect(component.$input.value).toBe(
      '[{"id":"pending","region_id":"right_upper_outer","x":133,"y":82}]'
    )
  })
})

/**
 * @import { BreastFeature } from './breast-diagram.js'
 */
