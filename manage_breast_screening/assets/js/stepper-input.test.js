import { getByLabelText } from '@testing-library/dom'
import { userEvent } from '@testing-library/user-event'
import { createAll } from 'nhsuk-frontend'

import { StepperInput } from './stepper-input.js'

describe('stepper-input', () => {
  const user = userEvent.setup()
  let stepUpButton
  let stepDownButton
  let input

  beforeEach(async () => {
    document.body.innerHTML = `
      <div class="nhsuk-form-group app-stepper-input" data-module="app-stepper-input" data-max="20" data-min="0">
        <label class="nhsuk-label" for="number_of_giraffes">Number of giraffes</label>

        <div class="nhsuk-input-wrapper">
          <button hidden class="nhsuk-button nhsuk-button--secondary app-button--icon nhsuk-button--small app-stepper-input__step-down app-js-stepper-input-step-down" data-module="nhsuk-button" type="button" aria-controls="number_of_giraffes" aria-describedby="number_of_giraffes-label" data-nhsuk-button-init="">
            <svg class="app-icon app-icon--minus" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" focusable="false" role="img" aria-label="Decrease">
              <title>Decrease</title>
              <path d="M5.5 10.5a1.5 1.5 0 0 0 0 3h13a1.5 1.5 0 0 0 0-3h-13Z"></path>
            </svg>
          </button>

          <input class="nhsuk-input app-stepper-input__input nhsuk-input--width-3 app-js-stepper-input-input" id="number_of_giraffes" name="number_of_giraffes" type="number" spellcheck="false" value="2" autocapitalize="none" inputmode="numeric" max="20" step="1">

          <button hidden class="nhsuk-button nhsuk-button--secondary app-button--icon nhsuk-button--small app-stepper-input__step-up app-js-stepper-input-step-up" data-module="nhsuk-button" type="button" aria-controls="number_of_giraffes" aria-describedby="number_of_giraffes-label" data-nhsuk-button-init="">
            <svg class="app-icon app-icon--plus" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" focusable="false" role="img" aria-label="Increase">
              <title>Increase</title>
              <path d="M13.5 5.5a1.5 1.5 0 0 0-3 0v5h-5a1.5 1.5 0 0 0 0 3h5v5a1.5 1.5 0 0 0 3 0v-5h5a1.5 1.5 0 0 0 0-3h-5v-5Z"></path>
            </svg>
          </button>
        </div>
      </div>
    `

    stepUpButton = getByLabelText(document.body, 'Increase').parentElement
    stepDownButton = getByLabelText(document.body, 'Decrease').parentElement
    input = getByLabelText(document.body, 'Number of giraffes')
  })

  it('shows buttons when javascript is enabled', async () => {
    expect(stepUpButton).toHaveAttribute('hidden')
    expect(stepDownButton).toHaveAttribute('hidden')

    createAll(StepperInput)

    expect(stepUpButton).not.toHaveAttribute('hidden')
    expect(stepDownButton).not.toHaveAttribute('hidden')
  })

  it('steps up when the button is clicked', async () => {
    createAll(StepperInput)
    expect(input).toHaveValue(2)

    await user.click(stepUpButton)

    expect(input).toHaveValue(3)
  })

  it('steps down when the button is clicked', async () => {
    createAll(StepperInput)
    expect(input).toHaveValue(2)

    await user.click(stepDownButton)

    expect(input).toHaveValue(1)
  })

  it('announces the change after buttons are clicked', async () => {
    createAll(StepperInput)

    /** @type {HTMLElement} */
    const liveRegion = document.querySelector("[aria-live='polite']")

    await user.click(stepUpButton)
    expect(liveRegion.innerText).toBe('3')
    await user.click(stepDownButton)
    expect(liveRegion.innerText).toBe('2')
  })

  it('assumes the min value when stepping down if the input is empty', async () => {
    createAll(StepperInput)
    input.value = ''

    await user.click(stepDownButton)

    expect(input).toHaveValue(0)
  })

  it('starts from 1 when stepping up if the input is empty and min is 0', async () => {
    createAll(StepperInput)
    input.value = ''

    await user.click(stepUpButton)

    expect(input).toHaveValue(1)
  })
})
