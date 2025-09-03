import { Component, ElementError } from 'nhsuk-frontend'

import setSubmit from './set-submit.js'

/**
 * Enhance an HTML form to intercept submit events and instead fetch the form action URL.
 * If successful, show child elements with data-show-on-submit, and hide those with data-hide-on-submit.
 * If unsuccessful, or the fetch times out, force a page refresh.
 */
export class CheckIn extends Component {
  /**
   * @param {Element | null} $root - HTML element to use for component
   */
  constructor($root) {
    super($root)

    const $form = this.$root.querySelector('form')
    if (!$form) {
      throw new ElementError({
        element: $root,
        component: CheckIn,
        identifier: 'Form element (`$form`)'
      })
    }

    this.$form = $form
    this.$showOnSubmit = this.$root.querySelectorAll('[data-show-on-submit]')
    this.$hideOnSubmit = this.$root.querySelectorAll('[data-hide-on-submit]')

    const showResult = this.showResult.bind(this)

    setSubmit(this.$form, {
      onBeforeSubmit() {
        console.log('Submitting form...')
      },
      onSuccess() {
        showResult()
      },
      onError(error) {
        console.error(error)
      }
    })
  }

  showResult() {
    this.$form.setAttribute('hidden', '')
    this.$hideOnSubmit.forEach(($elem) => $elem.setAttribute('hidden', ''))
    this.$showOnSubmit.forEach(($elem) => $elem.removeAttribute('hidden'))
  }

  /**
   * Name for the component used when initialising using data-module attributes
   */
  static moduleName = 'app-check-in'
}
