# Testing approach

We aim to follow the [testing principles outlined in the quality framework](https://github.com/NHSDigital/software-engineering-quality-framework/blob/main/practices/testing.md).

Our automated test suite is a quality gate that every build must pass in order to be merged and deployed. The whole test suite can be run locally with `make test`.

We generally follow the [test pyramid](https://martinfowler.com/articles/practical-test-pyramid.html) approach, with a large number of unit tests and a smaller number of UI tests.

## Python unit tests

For our python unit tests we use pytest and [pytest_django](https://pytest-django.readthedocs.io/en/latest/) rather than unittest style classes.

### Factories

We use [factory-boy](https://factoryboy.readthedocs.io/en/stable/) for test data management. Factory classes live in `tests/factories.py` within each django app.

When declaring a factory, provide the minimal set of attributes in order to be able to construct a valid object. Do not rely on randomness or the current time, otherwise the tests will be non-deterministic.

Consider creating [traits](https://factoryboy.readthedocs.io/en/stable/reference.html#traits) for common instantiations of the factory class.

You can wrap factory calls in a pytest fixture to avoid duplication in tests.

#### Example: traits for reported mammograms

```python
    class Params:
        outside_uk = Trait(
            location_type=models.ParticipantReportedMammogram.LocationType.OUTSIDE_UK,
            location_details="france",
        )
        elsewhere_uk = Trait(
            location_type=models.ParticipantReportedMammogram.LocationType.ELSEWHERE_UK,
            location_details="private provider",
        )
```

### `pytest.mark.django_db`

Some tests require django database access, indiciated by the `pytest.mark.django_db` mark. Bear in mind that these
tests will be much slower to run.

You can avoid the need for the django_db mark by:

- mocking out the dependencies of the unit under test using [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- using factory-boy's [build or stub strategies](https://factoryboy.readthedocs.io/en/stable/reference.html#factory.BUILD_STRATEGY) instead of the default 'create' strategy. These allow you to create objects without saving them to the db.
- restructuring the code under test (e.g. avoiding passing models directly to templates, or factoring out a service object to encapsulate some ORM queries)

| Component                  | Should it require the django_db mark? |
| -------------------------- | ------------------------------------- |
| Models                     | Yes                                   |
| Services                   | Yes                                   |
| Views, including API views | Maybe                                 |
| Templates                  | No                                    |
| Presenters                 | No                                    |
| Utilities                  | No                                    |

#### Example: testing a presenter using mocks

```python
def test_additional_details(self):
    appointment = MagicMock(spec=Appointment)
    appointment.study = MagicMock(spec=Study)
    appointment.study.additional_details = (
        "Some additional details about the images taken."
    )

    assert (
        ImagesTakenPresenter(appointment).additional_details
        == "Some additional details about the images taken."
    )
```

#### Example: using the factory-boy build strategy

```python
def test_success_message_content(self):
    obj = UserFactory.build()

    assert AddView().get_success_message_content(obj) == "Added test"
```

## JavaScript unit tests

Our JavaScript tests are run with [jest](https://jestjs.io/) and [testing-library](https://testing-library.com/). The tests are run against [jsdom](https://github.com/jsdom/jsdom), which is a simulated version of a browser environment, meaning that some browser functionality may need to be mocked or polyfilled.

Use the `userEvent` object to simulate user actions, like clicking on a button, so that the tests mirror what a user would do.

> [The more your tests resemble the way your software is used, the more confidence they can give you.](https://twitter.com/kentcdodds/status/977018512689455106)

### Example: using userEvent

```js
/* eslint-disable */

import { userEvent } from '@testing-library/user-event'

const user = userEvent.setup()
// ...

it('displays start-appointment', async () => {
    // ...

    expect($startAppointmentContainer).toHaveAttribute('hidden')
    await user.click(button)
    expect(startAppointmentContainer).not.toHaveAttribute('hidden')
})

/* eslint-enable */
```

## Playwright UI tests

Playwright tests live in the top level tests/system directory.

These are written in pytest, but we divide each test into a series of given/when/then steps, which are just function calls.

Follow the [playwright best practices](https://playwright.dev/docs/best-practices):

- don't test behaviour that is invisible to the user
- avoid CSS or XPath locators, which can be fragile, but make good use of `getByRole`, which depends on the accessible role instead
- use `getByLabel` when filling out forms, as this will ensure the inputs are correctly labelled
- use [playwright's assertions](https://playwright.dev/python/docs/test-assertions) that auto wait for the locator

Be extra careful when calling `.all()` on a locator as this returns immediately instead of auto-waiting, which can cause flaky tests.

### Example: given/when/then structure

```python
def test_log_in_with_single_provider_assigned(self):
    self.given_a_user_with_single_provider()
    self.given_i_am_on_the_home_page()
    self.when_i_log_in_via_cis2()
    self.then_i_am_redirected_to_home()
    self.then_header_shows_log_out()
```

### Example: using getByRole

```python
def then_header_shows_log_in(self):
    header = self.page.get_by_role("navigation")

    expect(header.get_by_text("Log in")).to_be_visible()
```

## Review apps for exploratory testing and review

When a PR is in review, you can apply the 'Deploy' tag to deploy to a review environment. This can be used for exploratory testing and product review.

## Accessibility testing

We use Axe to scan for some automated issues within our Playwright tests. When adding a new page, we should have at least one test that visits the page and runs the scanner.

Automated testing can only catch a subset of accessibility issues, so we need to supplement this with manual testing. Follow the [accessibility testing guidance in the service manual](https://service-manual.nhs.uk/accessibility/testing). The service should meet WCAG 2.2.

## Cross browser testing

When testing manually, don't forget to test in different browsers and with assistive tech. Developers can request a licence to Browserstack to help with this. We should aim to support [the same set of browsers as the design system](https://github.com/nhsuk/nhsuk-frontend/blob/main/packages/nhsuk-frontend/.browserslistrc).

## Deployment testing and monitoring in production

We do a staged deployment: first we deploy to our preprod environment, then we run [a smoke test](/scripts/bash/container_app_smoke_test.sh), and then we only deploy to prod
if it's successful.

We are using Azure application insights to collect metrics, logs, and traces, and production alerts go to #screening-manage-devs in slack.
