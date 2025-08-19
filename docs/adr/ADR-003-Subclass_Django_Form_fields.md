# ADR 003: Subclass django form fields

## Status

Accepted

## Context

Django has a built-in forms framework which makes it possible to declare the form structure in a `Form` subclass, and use that to render the HTML form.

The `Form` class also handles all the backend validation and cleaning of data prior to doing something with it — it's a very useful building block that we want to continue using.

Forms, Fields, and Widgets all have internal templates that allow you to interpolate them in a template, using constructs like `{{ form }}` or `{{ form.field.as_field_group() }}`. Out of the box, these render HTML that doesn't work with our design system, so we were instead [rendering form fields manually](https://docs.djangoproject.com/en/5.2/topics/forms/#rendering-fields-manually).

This was very error prone and verbose, because we had to map between Django's form API and the API of our component macros, and we had to repeat this work for every form we added.

## Decision

We decided to introduce a set of `Field` subclasses that customise the internal templates, so that they are rendered using the design system components.

| Field class                          | Widget class               | Rendered component |
| ------------------------------------ | -------------------------- | ------------------ |
| core.form_fields.CharField           | TextInput, EmailInput, etc | input              |
| core.form_fields.CharField           | TextArea                   | textarea           |
| core.form_fields.ChoiceField         | RadioSelect                | radios             |
| core.form_fields.ChoiceField         | Select                     | select             |
| core.form_fields.MultipleChoiceField | CheckboxSelectMultiple     | checkboxes         |
| core.form_fields.SplitDateField      | SplitDateWidget            | date-input         |

In a template, they are rendered with `{{ form.field.as_field_group() }}` this encpauslates all the complexity of mapping parameters between Django's form API and the [Jinja2 component macros](./ADR-002-Use_Jinja2.md).

## Consequences

the custom form field subclasses:

- make it possible to add new forms without writing a lot of HTML or Jinja in the template
- should be intuitive to developers already familiar with Django
- may need extending to support additional params for the underlying component
