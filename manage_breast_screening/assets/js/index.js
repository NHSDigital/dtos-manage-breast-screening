import { createAll, initAll } from 'nhsuk-frontend'

import { CheckIn } from './check-in.js'
import { StepperInput } from './stepper-input.js'

document.addEventListener('DOMContentLoaded', () => {
  // Initialise NHS.UK frontend components
  initAll()

  // Initialise application components
  createAll(CheckIn)
  createAll(StepperInput)
})
