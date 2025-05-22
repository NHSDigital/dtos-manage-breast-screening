import { getByRole } from '@testing-library/dom'
import { userEvent } from '@testing-library/user-event'

import setSubmit from './set-submit.js'

describe('setSubmit', () => {
  const user = userEvent.setup()

  /** @type {HTMLButtonElement} */
  let button

  /** @type {HTMLFormElement} */
  let form

  /** @type {boolean} */
  let beforeSubmit

  /** @type {Response} */
  let successResponse

  /** @type {Error} */
  let error

  beforeEach(() => {
    document.body.innerHTML = `
      <form method="post" action="/example" novalidate>
        <button>Submit</button>
      </form>
    `

    form = document.querySelector('form')
    button = getByRole(form, 'button', { name: 'Submit' })

    /** Add mock event handlers */
    beforeSubmit = false
    successResponse = undefined
    error = undefined
    setSubmit(form, {
      onBeforeSubmit() {
        beforeSubmit = true
      },
      onSuccess(response) {
        successResponse = response
      },
      onError(e) {
        error = e
      }
    })
  })

  it('calls onBeforeSubmit and onSuccess when the request succeeds', async () => {
    jest.mocked(fetch).mockResolvedValue(
      /** @type {Response} */ ({
        ok: true,
        status: 200
      })
    )

    await user.click(button)

    expect(beforeSubmit).toBe(true)
    expect(successResponse).toHaveProperty('status', 200)
    expect(error).toBeUndefined()
  })

  it('calls onBeforeSubmit and onError when the request fails', async () => {
    jest.mocked(fetch).mockResolvedValue(
      /** @type {Response} */ ({
        ok: false,
        status: 500
      })
    )

    await user.click(button)

    expect(beforeSubmit).toBe(true)
    expect(successResponse).toBeUndefined()
    expect(error).toEqual(Error('Response status: 500'))
  })

  it('calls onBeforeSubmit and onError when an error is thrown', async () => {
    const thrownError = new Error('Something went wrong')

    jest.mocked(fetch).mockRejectedValue(thrownError)

    await user.click(button)

    expect(beforeSubmit).toBe(true)
    expect(successResponse).toBeUndefined()
    expect(error).toEqual(thrownError)
  })
})
