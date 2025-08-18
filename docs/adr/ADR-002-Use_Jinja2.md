# ADR 002: Consume the design system components via Jinja2

## Status

Accepted

## Context

Our backend is in Python/Django. When we [chose Django as our framework](../ADR-001-Use_Django_framework.md), we had a choice of using the default template engine, or [swapping it out for Jinja2 or another template engine](https://docs.djangoproject.com/en/5.2/topics/templates/#support-for-template-engines).

At the same time, we wanted a simple way of making use of NHS.UK frontend, so that we can consistently use design system components. NHS.UK frontend can be used in several ways:

1. Copying and pasting the HTML directly into the template
2. Via the Nunjucks templates bundled with nhsuk-frontend (which are mostly compatable with Jinja2)
3. Via [NHS.UK react components](https://github.com/NHSDigital/nhsuk-react-components) (which lag behind nhsuk-frontend)

We didn't pursue option 1 because it would have led to very verbose templates, with lots of room for inconsistency.

Option 2 seemed promising, based on the experience of other teams. For example [ONS maintain their own variant of the GOV.UK design system, and they ensure that their templates can be used in both Jinja2 and Nunjucks](https://service-manual.ons.gov.uk/design-system/guidance/templating-in-nunjucks). [govuk-frontend-jinja](https://github.com/LandRegistry/govuk-frontend-jinja) is a well established port of the GOV.UK design system to Jinja2, and we have heard that the changes required for new releases are typically quite minimal.

We did not want to introduce a JavaScript framework purely for template reuse, because it would bring additional complexity,
and we are unlikely to gain additional benefits, since we are not building a single-page app, and we do not expect to use
much Javascript or Typescript in the service. The [GOV.UK service manual page on progressive enhancement](https://www.gov.uk/service-manual/technology/using-progressive-enhancement) requires us to build our service in a way that still works even if the Javascript layer fails. With React, we would need to add additional tooling to support Server Side Rendering (SSR) of the components.

## Decision

We decided to use Jinja2 as our template framework, allowing us to make use of NHS.UK frontend components.
We created [a port of the nunjucks templates, specifically for Jinja2](https://github.com/NHSDigital/nhsuk-frontend-jinja), mirroring the approach taken by the govuk-frontend-jinja project.

We've configured Django to use Jinja instead of the Django template language, and exposed `static`, `url`, and `STATIC_URL` to all templates for computing URLs. We've also set Jinja2's undefined setting to `ChainableUndefined` as this is what's assumed by the NHS.UK frontend templates.

## Consequences

nhsuk-frontend-jinja has a macro for every design system component, and can be reused by other services. It follows the same structure as the Nunjucks templates. It will need updating with each release of nhsuk-frontend.

[The Jinja engine does not support all the functionality of the Django test client](https://code.djangoproject.com/ticket/24622),
so we will need to find other ways to test that the right context is being passed to the templates.
