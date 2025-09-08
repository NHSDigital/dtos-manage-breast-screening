import datetime

from django import forms
from django.core import validators
from django.forms import Textarea, ValidationError, widgets
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from manage_breast_screening.core.utils.date_formatting import format_date


class BetterMultiWidget(widgets.MultiWidget):
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


class DayMonthYearWidget(BetterMultiWidget):
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


class MonthYearWidget(BetterMultiWidget):
    """
    A widget that splits a date into 2 number inputs.

    Adapted from https://github.com/ministryofjustice/django-govuk-forms/blob/master/govuk_forms/widgets.py
    """

    def __init__(self, attrs=None):
        date_widgets = (
            widgets.NumberInput(attrs=attrs),
            widgets.NumberInput(attrs=attrs),
        )
        super().__init__(date_widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.month, value.year]
        return [None, None]


class SplitDateField(forms.MultiValueField):
    """
    A form field that can be rendered as 2 or 3 inputs using the dateInput component in the design system.

    By default, the date is validated to be between 1st January 1900
    and today's date. This can be customised with the `min_value` and
    `max_value` arguments.

    If you pass `include_day=False`, then the day input will be dropped,
    and the date will be assumed to be the first of the month.

    Adapted from https://github.com/ministryofjustice/django-govuk-forms/blob/master/govuk_forms/fields.py
    """

    default_error_messages = {"invalid": _("Enter a valid date.")}

    def __init__(self, *args, **kwargs):
        max_value = kwargs.pop("max_value", datetime.date.today())
        min_value = kwargs.pop("min_value", datetime.date(1900, 1, 1))

        self.include_day = kwargs.pop("include_day", True)
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
            IntegerField(**month_kwargs),
            IntegerField(**year_kwargs),
        ]

        if self.include_day:
            self.fields.insert(0, IntegerField(**day_kwargs))

        if self.include_day:
            kwargs["widget"] = DayMonthYearWidget
            kwargs["template_name"] = "forms/day-month-year-date-input.jinja"
        else:
            kwargs["widget"] = MonthYearWidget
            kwargs["template_name"] = "forms/month-year-date-input.jinja"

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
                if self.include_day:
                    return datetime.date(data_list[2], data_list[1], data_list[0])
                else:
                    return datetime.date(data_list[1], data_list[0], 1)
            except ValueError:
                raise ValidationError(self.error_messages["invalid"], code="invalid")
        return None

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if not isinstance(widget, widgets.MultiWidget):
            return attrs
        for subfield, subwidget in zip(self.fields, widget.widgets):
            if subfield.min_value is not None:
                subwidget.attrs["min"] = subfield.min_value
            if subfield.max_value is not None:
                subwidget.attrs["max"] = subfield.max_value
        return attrs


class CharField(forms.CharField):
    def __init__(
        self,
        *args,
        hint=None,
        label_classes=None,
        classes=None,
        **kwargs,
    ):
        widget = kwargs.get("widget")
        if (isinstance(widget, type) and widget is Textarea) or isinstance(
            widget, Textarea
        ):
            kwargs["template_name"] = "forms/textarea.jinja"
        else:
            kwargs["template_name"] = "forms/input.jinja"

        self.hint = hint
        self.classes = classes
        self.label_classes = label_classes

        super().__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)

        # Don't use maxlength even if there is a max length validator.
        # This attribute prevents the user from seeing errors, so we don't use it
        attrs.pop("maxlength", None)

        return attrs


class IntegerField(forms.IntegerField):
    def __init__(
        self,
        *args,
        hint=None,
        label_classes=None,
        classes=None,
        **kwargs,
    ):
        kwargs["template_name"] = "forms/input.jinja"

        self.hint = hint
        self.classes = classes
        self.label_classes = label_classes

        super().__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)

        # Don't use min/max/step attributes.
        attrs.pop("min", None)
        attrs.pop("max", None)
        attrs.pop("step", None)

        return attrs


class BoundChoiceField(forms.BoundField):
    """
    Specialisation of BoundField that can deal with conditionally shown fields,
    and divider content between choices.
    This can be used to render a set of radios or checkboxes with text boxes to capture
    more details.
    """

    def __init__(self, form: forms.Form, field: "ChoiceField", name: str):
        super().__init__(form, field, name)

        self._conditional_html = {}
        self.dividers = {}

    def add_conditional_html(self, value, html):
        if isinstance(self.field.widget, widgets.Select):
            raise ValueError("select comonent does not support conditional fields")

        self._conditional_html[value] = html

    def conditional_html(self, value):
        return self._conditional_html.get(value)

    def add_divider_after(self, previous, divider):
        self.dividers[previous] = divider

    def get_divider_after(self, previous):
        return self.dividers.get(previous)


class ChoiceField(forms.ChoiceField):
    """
    A ChoiceField that renders using NHS.UK design system radios/select
    components.
    """

    widget = widgets.RadioSelect
    bound_field_class = BoundChoiceField

    def __init__(
        self,
        *args,
        hint=None,
        label_classes=None,
        classes=None,
        **kwargs,
    ):
        kwargs["template_name"] = ChoiceField._template_name(
            kwargs.get("widget", self.widget)
        )

        self.hint = hint
        self.classes = classes
        self.label_classes = label_classes

        super().__init__(*args, **kwargs)

    @staticmethod
    def _template_name(widget):
        if (isinstance(widget, type) and widget is widgets.RadioSelect) or isinstance(
            widget, widgets.RadioSelect
        ):
            return "forms/radios.jinja"
        elif (isinstance(widget, type) and widget is widgets.Select) or isinstance(
            widget, widgets.Select
        ):
            return "forms/select.jinja"


class MultipleChoiceField(forms.MultipleChoiceField):
    """
    A MultipleChoiceField that renders using the NHS.UK design system checkboxes
    component.
    """

    widget = widgets.CheckboxSelectMultiple
    bound_field_class = BoundChoiceField

    def __init__(
        self,
        *args,
        hint=None,
        label_classes=None,
        classes=None,
        **kwargs,
    ):
        kwargs["template_name"] = "forms/checkboxes.jinja"

        self.hint = hint
        self.classes = classes
        self.label_classes = label_classes

        super().__init__(*args, **kwargs)
