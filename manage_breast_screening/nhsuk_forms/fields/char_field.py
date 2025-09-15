from django import forms
from django.forms import Textarea


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
