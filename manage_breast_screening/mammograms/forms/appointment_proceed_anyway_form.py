from django.forms import Form
from django.forms.widgets import Textarea

from manage_breast_screening.nhsuk_forms.fields import CharField


class AppointmentProceedAnywayForm(Form):
    reason_for_continuing = CharField(
        required=True,
        label="Provide a reason for continuing",
        label_classes="nhsuk-label--m",
        widget=Textarea(attrs={"rows": 3}),
        max_words=500,
        error_messages={
            "max_words": "Reason for continuing must be 500 words or less",
            "required": "Provide a reason for continuing",
        },
    )

    def __init__(self, *args, participant, **kwargs):
        self.instance = kwargs.pop("instance", None)

        kwargs["initial"] = {
            "reason_for_continuing": self.instance.reason_for_continuing
        }

        super().__init__(*args, **kwargs)

    def update(self):
        self.instance.reason_for_continuing = self.cleaned_data["reason_for_continuing"]
        self.instance.save()

        return self.instance
