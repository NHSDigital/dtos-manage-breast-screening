from django import forms
from django.forms import widgets

from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields
from manage_breast_screening.nhsuk_forms.validators import ExcludesOtherOptionsValidator


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
        self._exclusive_options = set()

    def add_conditional_html(self, value, html):
        if isinstance(self.field.widget, widgets.Select):
            raise ValueError("select comonent does not support conditional fields")

        self._conditional_html[value] = html

    def conditional_html(self, value):
        explicitly_set_html = self._conditional_html.get(value)
        if explicitly_set_html:
            return explicitly_set_html

        if isinstance(self.form, FormWithConditionalFields):
            return self.form.conditionally_shown_html(self.name, value)

        return None

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
        visually_hidden_label_prefix=None,
        visually_hidden_label_suffix=None,
        classes=None,
        choice_hints=None,
        **kwargs,
    ):
        kwargs["template_name"] = ChoiceField._template_name(
            kwargs.get("widget", self.widget)
        )

        self.hint = hint
        self.classes = classes
        self.label_classes = label_classes
        self.visually_hidden_label_prefix = visually_hidden_label_prefix
        self.visually_hidden_label_suffix = visually_hidden_label_suffix
        self.choice_hints = choice_hints or {}

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
        visually_hidden_label_prefix=None,
        visually_hidden_label_suffix=None,
        exclusive_choices=(),
        classes=None,
        choice_hints=None,
        **kwargs,
    ):
        kwargs["template_name"] = "forms/checkboxes.jinja"

        self.hint = hint
        self.classes = classes
        self.label_classes = label_classes
        self.visually_hidden_label_prefix = visually_hidden_label_prefix
        self.visually_hidden_label_suffix = visually_hidden_label_suffix
        self.exclusive_choices = exclusive_choices
        self.choice_hints = choice_hints or {}

        super().__init__(*args, **kwargs)

        choice_labels = {choice: label for choice, label in self.choices}

        for exclusive_choice in self.exclusive_choices:
            try:
                label = choice_labels[exclusive_choice]
            except KeyError:
                raise ValueError(f"{exclusive_choice} is not in choices")

            self.validators.append(
                ExcludesOtherOptionsValidator(exclusive_choice, label)
            )

    def is_exclusive(self, value):
        return value in self.exclusive_choices
