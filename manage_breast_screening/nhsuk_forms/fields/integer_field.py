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
