from django import forms
from django.forms import Textarea

from manage_breast_screening.nhsuk_forms.fields import CharField


class AppointmentNoteForm(forms.Form):
    content = CharField(
        label="Note",
        hint="Include information that is relevant to this appointment.",
        required=True,
        error_messages={
            "required": "Enter a note",
        },
        label_classes="nhsuk-label--m",
        widget=Textarea(attrs={"rows": 5}),
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop("instance", None)
        if self.instance:
            initial = kwargs.setdefault("initial", {})
            initial.setdefault("content", self.instance.content)
        super().__init__(*args, **kwargs)

    def save(self):
        self.instance.content = self.cleaned_data["content"]
        self.instance.save()
        return self.instance
