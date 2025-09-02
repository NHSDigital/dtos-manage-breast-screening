import { getByRole } from '@testing-library/dom'
import { userEvent } from '@testing-library/user-event'
import { createAll } from 'nhsuk-frontend'

import { CheckIn } from './check-in.js'

describe('Check in', () => {
  const user = userEvent.setup()

  /** @type {HTMLFormElement} */
  let form

  /** @type {HTMLButtonElement} */
  let button

  /** @type {HTMLDivElement} */
  let oldMessage

  /** @type {HTMLDivElement} */
  let message

  beforeEach(() => {
    document.body.innerHTML = `
      <div data-module="${CheckIn.moduleName}">
        <div data-hide-on-submit>Not submitted</div>
        <div data-show-on-submit hidden>Submitted</div>
        <form method="post" action="/example" novalidate>
          <button>Submit</button>
        </form>
      </div>
    `

    const $container = document.querySelector('[data-module="app-check-in"]')

    form = $container.querySelector('form')
    button = getByRole(form, 'button', { name: 'Submit' })
    oldMessage = $container.querySelector('[data-hide-on-submit]')
    message = $container.querySelector('[data-show-on-submit]')

    jest.spyOn(console, 'error').mockImplementation(() => {})
  })

  it('swaps the form for a success message', async () => {
    jest.mocked(fetch).mockResolvedValue(
      /** @type {Response} */ ({
        ok: true,
        status: 200
      })
    )

    createAll(CheckIn)

    await user.click(button)

    expect(form).toHaveAttribute('hidden')
    expect(oldMessage).toHaveAttribute('hidden')
    expect(message).not.toHaveAttribute('hidden')
    expect(console.error).not.toHaveBeenCalled()
  })

  it('does not change the DOM if the request fails', async () => {
    jest.mocked(fetch).mockResolvedValue(
      /** @type {Response} */ ({
        ok: false,
        status: 500
      })
    )

    createAll(CheckIn)

    await user.click(button)

    expect(message).toHaveAttribute('hidden')
    expect(oldMessage).not.toHaveAttribute('hidden')

    expect(console.error).toHaveBeenCalledWith(
      new Error('Response status: 500')
    )
  })
})
