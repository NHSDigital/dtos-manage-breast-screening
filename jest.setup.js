import '@testing-library/jest-dom'
import { outdent } from 'outdent'

/**
 * Mock fetch() function for jsdom
 */
Object.defineProperty(window, 'fetch', {
  configurable: true,
  writable: true,
  value: jest.fn().mockResolvedValue(undefined)
})

/**
 * Mock out SVG functionality that isn't implemented by JSDOM.
 * These mocks are not remotely realistic, so don't depend on them
 * for testing complex SVG interactions.
 */
Object.defineProperty(globalThis.SVGElement.prototype, 'getScreenCTM', {
  configurable: true,
  writable: true,
  value: jest.fn().mockImplementation(() => ({
    a: 1,
    b: 0,
    c: 0,
    d: 1,
    e: 0,
    f: 0,
    inverse: jest.fn().mockReturnThis(),
    multiply: jest.fn().mockReturnThis(),
    translate: jest.fn().mockReturnThis(),
    scale: jest.fn().mockReturnThis(),
    rotate: jest.fn().mockReturnThis()
  }))
})

Object.defineProperty(globalThis.SVGElement.prototype, 'createSVGPoint', {
  configurable: true,
  writable: true,
  value: jest.fn().mockImplementation(() => ({
    x: 0,
    y: 0,
    matrixTransform: jest.fn().mockReturnThis
  }))
})

Object.defineProperty(globalThis.SVGElement.prototype, 'isPointInFill', {
  configurable: true,
  writable: true,
  value: jest.fn().mockImplementation(() => true)
})

beforeEach(() => {
  const stylesheet = document.createElement('style')

  stylesheet.innerHTML = outdent`
    :root {
      --nhsuk-breakpoint-mobile: 20rem;
      --nhsuk-breakpoint-tablet: 40.0625rem;
      --nhsuk-breakpoint-desktop: 48.0625rem;
      --nhsuk-breakpoint-large-desktop: 61.875rem;
    }
  `

  // Add styles for NHS.UK frontend checks
  document.head.appendChild(stylesheet)

  // Flag NHS.UK frontend as supported
  document.body.classList.add('nhsuk-frontend-supported')
})
