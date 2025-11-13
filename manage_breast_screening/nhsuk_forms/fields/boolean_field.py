from django import forms

from .choice_fields import BoundChoiceField


class BooleanField(forms.BooleanField):
    bound_field_class = BoundChoiceField

    def __init__(
        self,
        *args,
        hint=None,
        label_classes=None,
        visually_hidden_label_prefix=None,
        visually_hidden_label_suffix=None,
        classes=None,
        **kwargs,
    ):
        kwargs["template_name"] = "forms/single-checkbox.jinja"

        self.hint = hint
        self.classes = classes
        self.label_classes = label_classes
        self.visually_hidden_label_prefix = visually_hidden_label_prefix
        self.visually_hidden_label_suffix = visually_hidden_label_suffix

        super().__init__(*args, **kwargs)
