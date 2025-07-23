import datetime
from typing import Mapping

from django import forms
from django.core import validators
from django.forms import ValidationError, widgets
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from manage_breast_screening.core.utils.date_formatting import format_date


class SplitDateWidget(widgets.MultiWidget):
    """
    A widget that splits a date into 3 number inputs.
    Adapted from https://github.com/ministryofjustice/django-govuk-forms/blob/master/govuk_forms/widgets.py
    """

    def __init__(self, attrs=None):
        date_widgets = (
            widgets.NumberInput(attrs=attrs),
            widgets.NumberInput(attrs=attrs),
            widgets.NumberInput(attrs=attrs),
        )
        super().__init__(date_widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.day, value.month, value.year]
        return [None, None, None]

    def subwidgets(self, name, value, attrs=None):
        """
        Expose data for each subwidget, so that we can render them separately in the template.

        For some reason, as of Django 5.2, `MultiWidget` does not actually override the default
        implementation provided by `Widget`, which means you can't call `form.date.0` `form.date.1`
        to access the individual parts.
        (see https://stackoverflow.com/questions/24866936/render-only-one-part-of-a-multiwidget-in-django)
        """
        context = self.get_context(name, value, attrs)
        for subwidget in context["widget"]["subwidgets"]:
            yield subwidget


class SplitHiddenDateWidget(SplitDateWidget):
    """
    A widget that splits a date into 3 number inputs (hidden variant)
    Adapted from https://github.com/ministryofjustice/django-govuk-forms/blob/master/govuk_forms/widgets.py
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for widget in self.widgets:
            widget.input_type = "hidden"


class SplitDateField(forms.MultiValueField):
    """
    A form field that can be rendered as 3 inputs using the dateInput component in the design system.
    Adapted from https://github.com/ministryofjustice/django-govuk-forms/blob/master/govuk_forms/fields.py
    """

    widget = SplitDateWidget
    hidden_widget = SplitHiddenDateWidget
    default_error_messages = {"invalid": _("Enter a valid date.")}

    def __init__(self, *args, **kwargs):
        max_value = kwargs.pop("max_value", datetime.date.today())
        min_value = kwargs.pop("min_value", datetime.date(1900, 1, 1))
        self.hint = kwargs.pop("hint", None)

        day_bounds_error = gettext("Day should be between 1 and 31.")
        month_bounds_error = gettext("Month should be between 1 and 12.")
        year_bounds_error = gettext(
            "Year should be between %(min_year)s and %(max_year)s."
        ) % {"min_year": min_value.year, "max_year": max_value.year}

        day_kwargs = {
            "min_value": 1,
            "max_value": 31,
            "error_messages": {
                "min_value": day_bounds_error,
                "max_value": day_bounds_error,
                "invalid": gettext("Enter day as a number."),
            },
        }
        month_kwargs = {
            "min_value": 1,
            "max_value": 12,
            "error_messages": {
                "min_value": month_bounds_error,
                "max_value": month_bounds_error,
                "invalid": gettext("Enter month as a number."),
            },
        }
        year_kwargs = {
            "min_value": min_value.year,
            "max_value": max_value.year,
            "error_messages": {
                "min_value": year_bounds_error,
                "max_value": year_bounds_error,
                "invalid": gettext("Enter year as a number."),
            },
        }

        self.fields = [
            forms.IntegerField(**day_kwargs),
            forms.IntegerField(**month_kwargs),
            forms.IntegerField(**year_kwargs),
        ]

        kwargs["template_name"] = "forms/split_date_field.jinja"

        super().__init__(self.fields, *args, **kwargs)

        self.validators.append(
            validators.MinValueValidator(
                min_value, f"Enter a date after {format_date(min_value)}"
            )
        )
        self.validators.append(
            validators.MaxValueValidator(
                max_value, f"Enter a date before {format_date(max_value)}"
            )
        )

    def compress(self, data_list):
        if data_list:
            try:
                if any(item in self.empty_values for item in data_list):
                    raise ValueError
                return datetime.date(data_list[2], data_list[1], data_list[0])
            except ValueError:
                raise ValidationError(self.error_messages["invalid"], code="invalid")
        return None

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if not isinstance(widget, SplitDateWidget):
            return attrs
        for subfield, subwidget in zip(self.fields, widget.widgets):
            if subfield.min_value is not None:
                subwidget.attrs["min"] = subfield.min_value
            if subfield.max_value is not None:
                subwidget.attrs["max"] = subfield.max_value
        return attrs


class ChoiceFieldRadios(forms.ChoiceField):
    """
    A ChoiceField that renders as a NHS.UK frontend radios component
    """

    def __init__(self, *args, **kwargs):
        kwargs["template_name"] = "forms/choice_field_radios.jinja"
        self.hint = kwargs.pop("hint", None)
        super().__init__(*args, **kwargs)


class DictMultiWidget(widgets.MultiWidget):
    """
    Multiwidget that decompresses from a dict
    """

    def decompress(self, value):
        result = []
        for widget_name in self.widgets_names:
            if value:
                result.append(value.get(widget_name[1:]))
            else:
                result.append(None)
        return result


class ConditionalField(forms.MultiValueField):
    """
    A field that groups a ChoiceField with a set of conditionally required fields.

    The conditional field names are prefixed by the lowercased value of the ChoiceField.

    Example usage:

    >>> myfield = ConditionalField(
    ...     choice_field=ChoiceField(choices=[('choice1', 'One', 'choice2', 'Two')]),
    ...     revealed_fields={ 'choice2': {'details': CharField()} }
    ... )
    ...
    ... myfield.clean(['choice1', 'abc'])
    {"choice": "choice2", "choice2_details": "abc"}
    """

    widget = DictMultiWidget
    hidden_widget = DictMultiWidget

    def __init__(
        self,
        choice_field: forms.ChoiceField,
        revealed_fields: Mapping[str, Mapping[str, forms.Field]],
        **kwargs,
    ):
        kwargs["template_name"] = "forms/conditional.jinja"
        self.hint = kwargs.pop("hint", None)
        self.choice_field = choice_field
        fields: list[forms.Field] = [choice_field]
        self.revealed_field_names = []
        self.revealed_field_required = {}

        widgets = {"choice": choice_field.widget}

        for value, fields_for_value in revealed_fields.items():
            for name, field in fields_for_value.items():
                fields.append(field)
                derived_name = f"{value.lower()}_{name}"
                self.revealed_field_names.append(derived_name)
                widgets[derived_name] = field.widget

                # Switch off required check for conditionally-revealed fields,
                # as it does not make sense to validate this unless the relevant
                # option has been selected. The default behaviour of MultiValueField
                # is to respect the required flag and raise ValidationError if the
                # field is empty.
                # Instead, we will store this flag and apply the check conditionally.
                self.revealed_field_required[derived_name] = field.required
                field.required = False

        super().__init__(
            fields,
            require_all_fields=False,
            widget=DictMultiWidget(widgets=widgets),
            **kwargs,
        )

    def compress(self, data_list):
        """
        Aggregate the data from the choice field and the conditionally-revealed fields
        into a dictionary.
        """
        result = {}
        choice_value, *other_data = data_list
        result["choice"] = choice_value
        prefix = f"{choice_value.lower()}_"

        for field_name, value in zip(
            self.revealed_field_names, other_data, strict=True
        ):
            result[field_name] = value
            if (
                field_name.startswith(prefix)
                and self.revealed_field_required[field_name]
                and value in self.empty_values
            ):
                # TODO: use a more specific error message
                raise ValidationError(self.error_messages["required"], code="required")

        return result
