import { initAll } from 'nhsuk-frontend'

import { initCheckIn } from './check-in.js'

document.addEventListener('DOMContentLoaded', () => {
  initAll()
  initCheckIn()
})
