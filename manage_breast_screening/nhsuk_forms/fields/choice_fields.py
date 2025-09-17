from django import forms
from django.forms import widgets


class RadioSelectWithoutFieldset(widgets.RadioSelect):
    use_fieldset = False


class CheckboxSelectMultipleWithoutFieldset(widgets.CheckboxSelectMultiple):
    use_fieldset = False


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

    To render a select instead, pass Select for the `widget` argument.
    To render radios without the fieldset, pass RadioSelectWithoutFieldset
    for the `widget` argument.
    """

    widget = widgets.RadioSelect
    bound_field_class = BoundChoiceField

    def __init__(
        self,
        *args,
        hint=None,
        label_classes="nhsuk-fieldset__legend--m",
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
        if (
            isinstance(widget, type) and issubclass(widget, widgets.RadioSelect)
        ) or isinstance(widget, widgets.RadioSelect):
            return "forms/radios.jinja"
        elif (
            isinstance(widget, type) and issubclass(widget, widgets.Select)
        ) or isinstance(widget, widgets.Select):
            return "forms/select.jinja"


class MultipleChoiceField(forms.MultipleChoiceField):
    """
    A MultipleChoiceField that renders using the NHS.UK design system checkboxes
    component.

    To render checkboxes without the fieldset, pass CheckboxSelectMultipleWithoutFieldset
    for the `widget` argument.
    """

    widget = widgets.CheckboxSelectMultiple
    bound_field_class = BoundChoiceField

    def __init__(
        self,
        *args,
        hint=None,
        label_classes="nhsuk-fieldset__legend--m",
        classes=None,
        **kwargs,
    ):
        kwargs["template_name"] = "forms/checkboxes.jinja"

        self.hint = hint
        self.classes = classes
        self.label_classes = label_classes

        super().__init__(*args, **kwargs)
