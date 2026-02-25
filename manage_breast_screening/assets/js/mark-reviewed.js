import { ConfigurableComponent, ElementError } from 'nhsuk-frontend'

import setSubmit from './set-submit.js'

/**
 * Enhance the mark as reviewed button to submit via fetch and update the review
 * status without a full page reload.
 *
 * @augments {ConfigurableComponent<MarkReviewedConfig>}
 */
export class MarkReviewed extends ConfigurableComponent {
  /** @type {HTMLElement | null} */
  $nextCard = null

  /**
   * @param {Element | null} $root - HTML element to use for component
   */
  constructor($root) {
    super($root)

    const { statusCardId, nextCardId } = this.config

    const $form = this.$root.querySelector('form')
    if (!$form) {
      throw new ElementError({
        element: $root,
        component: MarkReviewed,
        identifier: 'Form element (`$form`)'
      })
    }

    if (!statusCardId) {
      throw new ElementError({
        element: $root,
        component: MarkReviewed,
        identifier: 'data-status-card-id attribute'
      })
    }

    if (nextCardId) {
      const $nextCard = document.getElementById(nextCardId)

      if (!($nextCard instanceof HTMLElement)) {
        throw new ElementError({
          element: $root,
          component: MarkReviewed,
          identifier: `#${nextCardId}`
        })
      }

      this.$nextCard = $nextCard
    }

    const $card = document.getElementById(statusCardId)

    if (!($card instanceof HTMLElement)) {
      throw new ElementError({
        element: $root,
        component: MarkReviewed,
        identifier: `#${statusCardId}`
      })
    }

    this.$card = $card
    this.$form = $form

    const updateDom = this.updateDom.bind(this)

    setSubmit(this.$form, {
      onBeforeSubmit() {
        console.log('Marking as reviewed…')
      },
      onSuccess() {
        updateDom()
      },
      onError(error) {
        console.error(error)
      }
    })
  }

  updateDom() {
    this.$card.querySelectorAll('[data-hide-on-review]').forEach(($elem) => {
      $elem.setAttribute('hidden', '')
    })

    this.$card.querySelectorAll('[data-show-on-review]').forEach(($elem) => {
      $elem.removeAttribute('hidden')
    })

    // Hide the mark reviewed form
    this.$root.setAttribute('hidden', '')

    if (this.$nextCard) {
      this.$nextCard.scrollIntoView({ behavior: 'smooth' })
    }
  }

  /**
   * Name for the component used when initialising using data-module attributes
   */
  static moduleName = 'app-mark-reviewed'

  /**
   * Mark reviewed default config
   *
   * @see {@link MarkReviewedConfig}
   * @constant
   * @type {MarkReviewedConfig}
   */
  static defaults = Object.freeze({
    statusCardId: ''
  })

  /**
   * Mark reviewed config schema
   *
   * @constant
   * @satisfies {Schema<MarkReviewedConfig>}
   */
  static schema = Object.freeze({
    properties: {
      statusCardId: { type: 'string' },
      nextCardId: { type: 'string' }
    },
    anyOf: [
      {
        required: ['statusCardId'],
        errorMessage: '"statusCardId" must be provided'
      }
    ]
  })
}

/**
 * Mark reviewed config
 *
 * @see {@link MarkReviewed.defaults}
 * @typedef {object} MarkReviewedConfig
 * @property {string} statusCardId - Id of the card for the current section
 * @property {string} [nextCardId] - Id of the next section's card, if there is one
 */

/**
 * @import { Schema } from 'nhsuk-frontend/dist/nhsuk/common/configuration/index.mjs'
 */
