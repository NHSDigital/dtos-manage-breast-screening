import { waitFor } from '@testing-library/dom'
import { outdent } from 'outdent'

import { CheckIn } from './check-in.js'

describe('Automatic initialisation', () => {
  beforeEach(() => {
    jest.spyOn(CheckIn, 'checkSupport')

    document.body.innerHTML = outdent`
      <div data-module="${CheckIn.moduleName}" data-appointment-id="123">
        <form method="post" action="/example" novalidate></form>
      </div>
    `
  })

  it('should init components on DOMContentLoaded', async () => {
    await import('./index.js')

    // Should not initialise on import
    expect(CheckIn.checkSupport).not.toHaveBeenCalled()

    // Should initialise on DOMContentLoaded
    window.document.dispatchEvent(new Event('DOMContentLoaded'))
    await waitFor(() => expect(CheckIn.checkSupport).toHaveBeenCalled())
  })
})
