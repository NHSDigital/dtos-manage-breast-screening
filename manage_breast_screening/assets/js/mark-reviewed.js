import { Component, ElementError } from 'nhsuk-frontend'

import setSubmit from './set-submit.js'

/**
 * Enhance the mark as reviewed button to submit via fetch and update the review
 * status without a full page reload.
 */
export class MarkReviewed extends Component {
  /**
   * @param {Element | null} $root - HTML element to use for component
   */
  constructor($root) {
    super($root)

    const $form = this.$root.querySelector('form')
    if (!$form) {
      throw new ElementError({
        element: $root,
        component: MarkReviewed,
        identifier: 'Form element (`$form`)'
      })
    }

    const cardId = this.$root.getAttribute('data-status-card-id')
    if (!cardId) {
      throw new ElementError({
        element: $root,
        component: MarkReviewed,
        identifier: 'data-status-card-id attribute'
      })
    }

    this.$form = $form
    this.$card = document.getElementById(cardId)

    if (this.$card === null) {
      throw new ElementError({
        element: $root,
        component: MarkReviewed,
        identifier: `#${cardId}`
      })
    }

    const updateDom = this.updateDom.bind(this)

    setSubmit(this.$form, {
      onBeforeSubmit() {
        console.log('Marking as reviewed...')
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
  }

  /**
   * Name for the component used when initialising using data-module attributes
   */
  static moduleName = 'app-mark-reviewed'
}
