from django import forms
from django.forms import Textarea

from manage_breast_screening.nhsuk_forms import validators


class CharField(forms.CharField):
    """
    CharField subclass that renders using an input or textarea component in the
    NHS design system, depending on the widget argument.

    If max_words or max_length are passed in, a character count component will
    be used.
    """

    def __init__(
        self,
        *args,
        max_length=None,
        max_words=250,
        threshold=25,
        hint=None,
        label_classes=None,
        classes=None,
        visually_hidden_label_prefix=None,
        visually_hidden_label_suffix=None,
        inputmode=None,
        **kwargs,
    ):
        self.hint = hint
        self.classes = classes
        self.label_classes = label_classes
        self.visually_hidden_label_prefix = visually_hidden_label_prefix
        self.visually_hidden_label_suffix = visually_hidden_label_suffix
        self.max_length = max_length
        self.max_words = max_words
        self.threshold = threshold
        self.inputmode = inputmode

        if max_length and max_words:
            raise ValueError("Cannot set both max_length and max_words")

        kwargs["template_name"] = self.template_name(widget=kwargs.get("widget"))

        super().__init__(*args, max_length=max_length, **kwargs)

        if max_words:
            self.validators.append(validators.MaxWordValidator(int(max_words)))

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)

        # Don't use maxlength even if there is a max length validator.
        # This attribute prevents the user from seeing errors, so we don't use it
        attrs.pop("maxlength", None)

        return attrs

    def template_name(self, widget):
        is_textarea = widget is Textarea or isinstance(widget, Textarea)

        if is_textarea and (self.max_length is not None or self.max_words is not None):
            return "forms/character-count.jinja"
        elif is_textarea:
            return "forms/textarea.jinja"
        else:
            return "forms/input.jinja"
