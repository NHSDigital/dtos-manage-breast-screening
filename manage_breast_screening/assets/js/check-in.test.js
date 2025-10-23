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
  let checkInContainer

  /** @type {HTMLDivElement} */
  let statusContainer

  /** @type {HTMLSpanElement} */
  let currentStatus

  /** @type {HTMLSpanElement} */
  let checkedInStatus

  beforeEach(() => {
    document.body.innerHTML = `
      <table>
        <tbody>
          <tr>
            <td>
              <div data-event-status-container="123">
                <span data-hide-on-check-in>Confirmed</span>
                <span data-show-on-check-in hidden>Checked in</span>
              </div>
            </td>
            <td>
              <div data-module="${CheckIn.moduleName}" data-appointment-id="123">
                <form method="post" action="/example" novalidate>
                  <button>Check in</button>
                </form>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    `

    checkInContainer = document.querySelector('[data-module="app-check-in"]')
    statusContainer = document.querySelector(
      '[data-event-status-container="123"]'
    )
    form = checkInContainer.querySelector('form')
    button = getByRole(form, 'button', { name: 'Check in' })
    currentStatus = statusContainer.querySelector('[data-hide-on-check-in]')
    checkedInStatus = statusContainer.querySelector('[data-show-on-check-in]')

    jest.spyOn(console, 'error').mockImplementation(() => {})
    jest.spyOn(console, 'warn').mockImplementation(() => {})
  })

  it('updates the status and hides the form on successful check-in', async () => {
    jest.mocked(fetch).mockResolvedValue(
      /** @type {Response} */ ({
        ok: true,
        status: 200
      })
    )

    createAll(CheckIn)

    await user.click(button)

    expect(checkInContainer).toHaveAttribute('hidden')
    expect(currentStatus).toHaveAttribute('hidden')
    expect(checkedInStatus).not.toHaveAttribute('hidden')
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

    expect(checkInContainer).not.toHaveAttribute('hidden')
    expect(currentStatus).not.toHaveAttribute('hidden')
    expect(checkedInStatus).toHaveAttribute('hidden')

    expect(console.error).toHaveBeenCalledWith(
      new Error('Response status: 500')
    )
  })

  it('throws an error if the status container cannot be found', async () => {
    // Create table but without matching status container
    document.body.innerHTML = `
      <table>
        <tbody>
          <tr>
            <td>
              <div data-module="${CheckIn.moduleName}" data-appointment-id="999">
                <form method="post" action="/example" novalidate>
                  <button>Check in</button>
                </form>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    `

    jest.mocked(fetch).mockResolvedValue(
      /** @type {Response} */ ({
        ok: true,
        status: 200
      })
    )

    createAll(CheckIn)

    const newButton = getByRole(document.body, 'button', { name: 'Check in' })
    await user.click(newButton)

    expect(console.warn).toHaveBeenCalledWith(
      'setSubmit: the form was submitted successfully, but the onSuccess handler threw an exception.'
    )
    expect(console.error).toHaveBeenCalledWith(
      expect.objectContaining({
        message: expect.stringContaining(
          'Status container element (`$statusContainer`)'
        )
      })
    )
  })
})
