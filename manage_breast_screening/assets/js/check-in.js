import { Component, ElementError } from 'nhsuk-frontend'

import setSubmit from './set-submit.js'

/**
 * Enhance a check-in form to submit via fetch and update the appointment
 * status without a full page reload.
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

    const appointmentId = this.$root.getAttribute('data-appointment-id')
    if (!appointmentId) {
      throw new ElementError({
        element: $root,
        component: CheckIn,
        identifier: 'data-appointment-id attribute'
      })
    }

    this.$form = $form
    this.appointmentId = appointmentId

    const updateStatus = this.updateStatus.bind(this)

    setSubmit(this.$form, {
      onBeforeSubmit() {
        console.log('Checking in appointment...')
      },
      onSuccess() {
        updateStatus()
      },
      onError(error) {
        console.error(error)
      }
    })
  }

  updateStatus() {
    const $statusContainer = document.querySelector(
      `[data-appointment-status-container="${this.appointmentId}"]`
    )

    const $startAppointmentContainer = document.querySelector(
      `[data-appointment-id="${this.appointmentId}"][data-module="app-start-appointment"]`
    )

    if (!$statusContainer) {
      throw new ElementError({
        element: this.$root,
        component: CheckIn,
        identifier: 'Status container element (`$statusContainer`)'
      })
    }

    // Hide the current status
    const $hideOnCheckIn = $statusContainer.querySelector(
      '[data-hide-on-check-in]'
    )
    if ($hideOnCheckIn) {
      $hideOnCheckIn.setAttribute('hidden', '')
    }

    // Show the checked-in status
    const $showOnCheckIn = $statusContainer.querySelector(
      '[data-show-on-check-in]'
    )
    if ($showOnCheckIn) {
      $showOnCheckIn.removeAttribute('hidden')
    }

    // Hide the check-in form
    this.$root.setAttribute('hidden', '')
    if ($startAppointmentContainer) {
      $startAppointmentContainer.removeAttribute('hidden')
    }
  }

  /**
   * Name for the component used when initialising using data-module attributes
   */
  static moduleName = 'app-check-in'
}
