import { getByRole } from '@testing-library/dom'
import { userEvent } from '@testing-library/user-event'
import { createAll } from 'nhsuk-frontend'

import { MarkReviewed } from './mark-reviewed.js'

describe('Mark reviewed', () => {
  const user = userEvent.setup()

  /** @type {HTMLFormElement} */
  let form

  /** @type {HTMLButtonElement} */
  let button

  /** @type {HTMLDivElement} */
  let markReviewedContainer

  /** @type {NodeListOf<Element>} */
  let showOnReviewElements

  /** @type {NodeListOf<Element>} */
  let hideOnReviewElements

  beforeEach(() => {
    document.body.innerHTML = `
      <div id="example-content" class="app-card-with-status">
        <div class="nhsuk-card">
          <div class="nhsuk-card__content">
            <h2 class="nhsuk-card__heading">Example content</h2>
            <div class="app-card-with-status__tag" aria-live="polite">
              <span data-hide-on-review><strong class="nhsuk-tag nhsuk-tag--green app-section-review-tag">To review</strong></span>
              <span data-show-on-review hidden><strong class="nhsuk-tag nhsuk-tag--green app-section-review-tag">Reviewed</strong></span>
            </div>

            <p>Example content</p>

            <hr class="nhsuk-section-break nhsuk-section-break--visible nhsuk-u-margin-bottom-4">

            <div data-hide-on-review data-module="${MarkReviewed.moduleName}" data-status-card-id="example-content">
              <form method="post" action="/example">
                <button type="submit" class="nhsuk-button nhsuk-button--secondary nhsuk-u-margin-bottom-0">Mark as reviewed</button>
              </form>
            </div>

            <span data-show-on-review hidden><a href="#next-content" class="nhsuk-button nhsuk-button--secondary">Next section</a></span>
          </div>
        </div>
      </div>
      <div id="next-content" class="app-card-with-status">
        <p>Bla bla bla</p>
      </div>
    `

    markReviewedContainer = document.querySelector(
      'div[data-module="app-mark-reviewed"]'
    )

    showOnReviewElements = document.querySelectorAll('[data-show-on-review]')
    hideOnReviewElements = document.querySelectorAll('[data-hide-on-review]')

    form = markReviewedContainer.querySelector('form')
    button = getByRole(form, 'button', { name: 'Mark as reviewed' })

    jest.spyOn(console, 'error').mockImplementation(() => {})
    jest.spyOn(console, 'log').mockImplementation(() => {})
    jest.spyOn(console, 'warn').mockImplementation(() => {})
  })

  it('hides the form if marking as reviewed was successful', async () => {
    jest.mocked(fetch).mockResolvedValue(
      /** @type {Response} */ ({
        ok: true,
        status: 200
      })
    )

    createAll(MarkReviewed)

    await user.click(button)

    expect(markReviewedContainer).toHaveAttribute('hidden')
    expect(console.error).not.toHaveBeenCalled()
  })

  it('shows elements marked with data-show-on-review on success', async () => {
    jest.mocked(fetch).mockResolvedValue(
      /** @type {Response} */ ({
        ok: true,
        status: 200
      })
    )

    createAll(MarkReviewed)

    showOnReviewElements.forEach((element) => {
      expect(element).toHaveAttribute('hidden')
    })

    await user.click(button)

    showOnReviewElements.forEach((element) => {
      expect(element).not.toHaveAttribute('hidden')
    })
  })

  it('hides elements marked with data-hide-on-review on success', async () => {
    jest.mocked(fetch).mockResolvedValue(
      /** @type {Response} */ ({
        ok: true,
        status: 200
      })
    )

    createAll(MarkReviewed)

    hideOnReviewElements.forEach((element) => {
      expect(element).not.toHaveAttribute('hidden')
    })

    await user.click(button)

    hideOnReviewElements.forEach((element) => {
      expect(element).toHaveAttribute('hidden')
    })
  })

  it('does not change the DOM if the request fails', async () => {
    jest.mocked(fetch).mockResolvedValue(
      /** @type {Response} */ ({
        ok: false,
        status: 500
      })
    )

    createAll(MarkReviewed)

    await user.click(button)

    expect(markReviewedContainer).not.toHaveAttribute('hidden')

    showOnReviewElements.forEach((element) => {
      expect(element).toHaveAttribute('hidden')
    })

    hideOnReviewElements.forEach((element) => {
      expect(element).not.toHaveAttribute('hidden')
    })

    expect(console.error).toHaveBeenCalledWith(
      new Error('Response status: 500')
    )
  })

  it('throws an error if the status container cannot be found', async () => {
    // Create table but without matching status container
    document.body.innerHTML = `
        <div data-module="${MarkReviewed.moduleName}" data-status-card-id="999">
          <form method="post" action="/example" novalidate>
            <button>Mark as reviewed</button>
          </form>
        </div>
    `

    createAll(MarkReviewed)

    expect(console.log).toHaveBeenCalledWith(
      expect.objectContaining({
        message: expect.stringContaining(
          `${MarkReviewed.moduleName}: #999 is not of type HTMLElement`
        )
      })
    )
  })
})
