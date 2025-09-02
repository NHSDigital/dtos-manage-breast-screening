import { createAll, initAll } from 'nhsuk-frontend'

import { CheckIn } from './check-in.js'

document.addEventListener('DOMContentLoaded', () => {
  // Initialise NHS.UK frontend components
  initAll()

  // Initialise application components
  createAll(CheckIn)
})
