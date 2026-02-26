import { ElementError } from 'nhsuk-frontend'

const TIMEOUT = 5000

/**
 * Enable a form to be submitted in the background via `fetch()`.
 * If this fails for any reason, it will fall back to normal form submission
 * (this assumes the form action is idempotent!)
 *
 * @param {HTMLFormElement} $form - HTML form element
 * @param {object} [options] - Handler options
 * @param {(this: HTMLFormElement) => void} [options.onBeforeSubmit] - Callback before submission
 * @param {(this: HTMLFormElement, response: Response) => void} [options.onSuccess] - Callback on successful response
 * @param {(this: HTMLFormElement, error: Error) => void} [options.onError] - Callback on error
 */
export default ($form, options = {}) => {
  if (!($form instanceof HTMLFormElement)) {
    throw new ElementError({
      element: $form,
      identifier: 'setSubmit: Form element (`$form`)',
      expectedType: 'HTMLFormElement'
    })
  }

  const method = $form.method
  const action = $form.action

  if (!method || !action) {
    throw new ElementError({
      identifier: 'setSubmit: Form method or action'
    })
  }

  function doSubmit() {
    if (options.onBeforeSubmit) {
      options.onBeforeSubmit.call($form)
    }

    /** @type {RequestInit} */
    const fetchOptions = {
      method: method,
      body: new FormData($form),
      headers: { Accept: 'text/plain, application/json' }
    }

    // Check for timeout support
    if ('AbortSignal' in window && 'timeout' in AbortSignal) {
      fetchOptions.signal = AbortSignal.timeout(TIMEOUT)
    }

    return fetch(action, fetchOptions)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Response status: ${response.status}`)
        }

        return response
      })
      .then((response) => {
        try {
          options.onSuccess?.apply($form, [response])
        } catch (error) {
          console.warn(
            'setSubmit: the form was submitted successfully, but the onSuccess handler threw an exception.'
          )

          throw error
        }

        return response
      })
      .catch((error) => {
        console.error(error)

        if (options.onError && error instanceof Error) {
          options.onError.apply($form, [error])
        }

        throw error
      })
  }

  /**
   * @this {HTMLFormElement}
   * @param {SubmitEvent} event
   */
  function handleSubmit(event) {
    event.preventDefault()

    // Manually submit form on error
    doSubmit().catch(() => {
      this.removeEventListener('submit', handleSubmit)
      this.submit()
    })
  }

  $form.addEventListener('submit', handleSubmit)
}
