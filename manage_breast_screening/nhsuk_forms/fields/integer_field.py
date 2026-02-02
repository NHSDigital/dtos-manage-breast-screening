from datetime import date

from django import forms


class StepperInput(forms.TextInput):
    pass


class IntegerField(forms.IntegerField):
    widget = forms.TextInput

    def __init__(
        self,
        *args,
        hint=None,
        label_classes=None,
        visually_hidden_label_prefix=None,
        visually_hidden_label_suffix=None,
        classes=None,
        inputmode="numeric",
        **kwargs,
    ):
        kwargs["template_name"] = IntegerField._template_name(
            kwargs.get("widget", self.widget)
        )

        self.hint = hint
        self.classes = classes
        self.label_classes = label_classes
        self.visually_hidden_label_prefix = visually_hidden_label_prefix
        self.visually_hidden_label_suffix = visually_hidden_label_suffix
        self.inputmode = inputmode

        super().__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)

        # Don't use min/max/step attributes. These are controlled
        # by the stepper-input component, so that we can opt-out of
        # user-unfriendly scroll behaviour.
        attrs.pop("min", None)
        attrs.pop("max", None)
        attrs.pop("step", None)

        return attrs

    @staticmethod
    def _template_name(widget):
        if (
            isinstance(widget, type) and issubclass(widget, StepperInput)
        ) or isinstance(widget, StepperInput):
            return "forms/stepper-input.jinja"
        else:
            return "forms/input.jinja"


class YearField(IntegerField):
    def __init__(
        self,
        *args,
        hint=None,
        label_classes=None,
        classes=None,
        min_value_callable=None,
        max_value_callable=None,
        **kwargs,
    ):
        self.min_value_callable = min_value_callable
        self.max_value_callable = max_value_callable

        super().__init__(
            *args, hint=hint, label_classes=label_classes, classes=classes, **kwargs
        )

    def _default_min_year(self):
        return date.today().year - 80

    def _default_max_year(self):
        return date.today().year

    def validate(self, value):
        super().validate(value)

        if value in self.empty_values:
            return

        min_value_callable = self.min_value_callable or self._default_min_year
        max_value_callable = self.max_value_callable or self._default_max_year

        min_value = min_value_callable()
        max_value = max_value_callable()

        if value < min_value:
            raise forms.ValidationError(
                self.error_messages.get(
                    "min_value", "Year must be %(min_value)s or later"
                ),
                code="min_value",
                params={"min_value": min_value},
            )

        if value > max_value:
            raise forms.ValidationError(
                self.error_messages.get(
                    "max_value", "Year must be %(max_value)s or earlier"
                ),
                code="max_value",
                params={"max_value": max_value},
            )
