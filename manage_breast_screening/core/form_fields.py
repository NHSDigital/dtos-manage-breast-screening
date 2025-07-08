import datetime

from django import forms
from django.forms import ValidationError, widgets
from django.utils.timezone import now
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _


class YearField(forms.IntegerField):
    """
    In integer field that accepts years between 1900 and now
    Allows 2-digit year entry which is converted depending on the `era_boundary`
    Adapted from https://github.com/ministryofjustice/django-govuk-forms/blob/master/govuk_forms/fields.py
    """

    def __init__(self, era_boundary=None, **kwargs):
        self.current_year = now().year
        self.century = 100 * (self.current_year // 100)
        if era_boundary is None:
            # 2-digit dates are a minimum of 10 years ago by default
            era_boundary = self.current_year - self.century - 10
        self.era_boundary = era_boundary
        bounds_error = gettext("Year should be between 1900 and %(current_year)s.") % {
            "current_year": self.current_year
        }
        options = {
            "min_value": 1900,
            "max_value": self.current_year,
            "error_messages": {
                "min_value": bounds_error,
                "max_value": bounds_error,
                "invalid": gettext("Enter year as a number."),
            },
        }
        options.update(kwargs)
        super().__init__(**options)

    def clean(self, value):
        value = self.to_python(value)
        if isinstance(value, int) and value < 100:
            if value > self.era_boundary:
                value += self.century - 100
            else:
                value += self.century
        return super().clean(value)


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
        day_bounds_error = gettext("Day should be between 1 and 31.")
        month_bounds_error = gettext("Month should be between 1 and 12.")

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
        year_kwargs = {}

        max_year = kwargs.pop("max_year", None)
        if max_year:
            year_kwargs["max_value"] = max_year

        self.fields = [
            forms.IntegerField(**day_kwargs),
            forms.IntegerField(**month_kwargs),
            YearField(**year_kwargs),
        ]

        super().__init__(self.fields, *args, **kwargs)

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
