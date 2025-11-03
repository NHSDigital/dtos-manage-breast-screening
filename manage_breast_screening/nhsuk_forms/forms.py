"""
Helpers to handle conditionally required fields
"""

from dataclasses import dataclass
from typing import Any

from django.forms import Form, ValidationError
from django.forms.widgets import MultiWidget


@dataclass
class ConditionalRequirement:
    predicate_field: str
    predicate_field_value: Any
    conditionally_required_field: str


class FieldPredicate:
    def __init__(self, validator, field_name, field_choices):
        self.validator = validator
        self.field_name = field_name
        self.field_choices = field_choices

    def require_field_with_prefix(self, prefix):
        for value, _ in self.field_choices:
            self.validator.require_field_with_value(
                predicate_field=self.field_name,
                predicate_field_value=value,
                conditionally_required_field=f"{prefix}_{value.lower()}",
            )


class FieldValuePredicate:
    def __init__(self, validator, field, field_value):
        self.validator = validator
        self.field = field
        self.field_value = field_value

    def require_field(self, conditionally_required_field):
        self.validator.require_field_with_value(
            predicate_field=self.field,
            predicate_field_value=self.field_value,
            conditionally_required_field=conditionally_required_field,
        )


class ConditionalFieldValidator:
    """
    Helper class to perform the conditional validation for the FormWithConditionalFields
    """

    def __init__(self, form):
        self.conditional_requirements = []
        self.form = form

    def require_field_with_value(
        self, conditionally_required_field, predicate_field, predicate_field_value
    ):
        """
        Mark a field as conditionally required if and only if another field (the predicate field)
        is set to a specific value.
        If the predicate field is set to the predicate value, this field will require a value.
        If the predicate field is set to a different value, this field's value will be ignored.
        """
        if conditionally_required_field not in self.form.fields:
            raise ValueError(f"{conditionally_required_field} is not a valid field")
        if predicate_field not in self.form.fields:
            raise ValueError(f"{predicate_field} is not a valid field")

        self.conditional_requirements.append(
            ConditionalRequirement(
                conditionally_required_field=conditionally_required_field,
                predicate_field=predicate_field,
                predicate_field_value=predicate_field_value,
            )
        )

        self.form.fields[conditionally_required_field].required = False

    def clean_conditional_fields(self):
        form = self.form
        for requirement in self.conditional_requirements:
            field = requirement.conditionally_required_field
            predicate_field_value = form.cleaned_data.get(requirement.predicate_field)

            if predicate_field_value == requirement.predicate_field_value:
                cleaned_value = form.cleaned_data.get(field)
                if isinstance(cleaned_value, str):
                    cleaned_value = cleaned_value.strip()

                if not cleaned_value:
                    form.add_error(
                        field,
                        ValidationError(
                            message=form.fields[field].error_messages["required"],
                            code="required",
                        ),
                    )


class FormWithConditionalFields(Form):
    """
    This form class makes it possible to declare conditional relationships between two fields.
    E.g. if the user selects a particular value of one field (the predicate field) then
    another field (the conditional field) should become required.

    Declare the fields normally, then in the `__init__`, after the superclass has been initialised,
    call `given_field_value().require_field()` or `given_field().require_field_with_prefix()`
    to declare the relationships.
    """

    def __init__(self, *args, **kwargs):
        self.conditional_field_validator = ConditionalFieldValidator(self)

        super().__init__(*args, **kwargs)

    def given_field_value(self, field, field_value):
        """
        Mini-DSL to declare conditional field relationships

        e.g. self.given_field_value('foo', 'choice1').require_field('other_details')
        """
        return FieldValuePredicate(
            self.conditional_field_validator, field=field, field_value=field_value
        )

    def given_field(self, predicate_field):
        """
        Mini-DSL to declare conditional field relationships

        e.g. self.given_field('foo').require_field_with_prefix('other')
        """
        return FieldPredicate(
            self.conditional_field_validator,
            field_name=predicate_field,
            field_choices=self.fields[predicate_field].choices,
        )

    def clean_conditional_fields(self):
        """
        Apply the validation and blank out any conditional fields that do not have their predicate met.
        This can happen when the user selects one option, fills out the conditional field, and then changes
        to a different option.
        """
        return self.conditional_field_validator.clean_conditional_fields()

    def full_clean(self):
        for requirement in self.conditional_field_validator.conditional_requirements:
            field = requirement.conditionally_required_field
            predicate_field_value = self.data.get(requirement.predicate_field)
            if predicate_field_value is None:
                cleaned_predicate_field_value = None
            else:
                cleaned_predicate_field_value = self.fields[
                    requirement.predicate_field
                ].clean(predicate_field_value)

            if cleaned_predicate_field_value != requirement.predicate_field_value:
                self.data = self.data.copy()

                if isinstance(self.fields[field].widget, MultiWidget):
                    for child in self.fields[field].widget.widgets_names:
                        self.data.pop(field + child, None)
                else:
                    self.data.pop(field, None)

                if hasattr(self.data, "_mutable"):
                    self.data._mutable = False

        super().full_clean()

    def clean(self):
        cleaned_data = super().clean()
        self.clean_conditional_fields()

        return cleaned_data
