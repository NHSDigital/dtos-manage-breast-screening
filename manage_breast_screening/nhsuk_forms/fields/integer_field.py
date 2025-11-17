from datetime import date

from django import forms


class IntegerField(forms.IntegerField):
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
        kwargs["template_name"] = "forms/input.jinja"

        self.hint = hint
        self.classes = classes
        self.label_classes = label_classes
        self.visually_hidden_label_prefix = visually_hidden_label_prefix
        self.visually_hidden_label_suffix = visually_hidden_label_suffix
        self.inputmode = inputmode

        super().__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)

        # Don't use min/max/step attributes.
        attrs.pop("min", None)
        attrs.pop("max", None)
        attrs.pop("step", None)

        return attrs


class YearField(IntegerField):
    def __init__(
        self,
        *args,
        hint=None,
        label_classes=None,
        classes=None,
        min_value=None,
        max_value=None,
        **kwargs,
    ):
        if min_value is None:
            min_value = date.today().year - 80
        if max_value is None:
            max_value = date.today().year

        year_bounds_error = f"Year must be between {min_value} and {max_value}"

        if "error_messages" not in kwargs:
            kwargs["error_messages"] = {}

        kwargs["error_messages"].setdefault("min_value", year_bounds_error)
        kwargs["error_messages"].setdefault("max_value", year_bounds_error)
        kwargs["min_value"] = min_value
        kwargs["max_value"] = max_value

        super().__init__(
            *args, hint=hint, label_classes=label_classes, classes=classes, **kwargs
        )
