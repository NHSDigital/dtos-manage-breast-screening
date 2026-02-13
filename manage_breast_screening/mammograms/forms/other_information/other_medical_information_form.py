from django.forms import Textarea

from manage_breast_screening.nhsuk_forms.fields import CharField
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields
from manage_breast_screening.participants.models.other_information.other_medical_information import (
    OtherMedicalInformation,
)


class OtherMedicalInformationForm(FormWithConditionalFields):
    details = CharField(
        hint="Provide details of any relevant health conditions or medications that are not covered by symptoms or medical history questions.",
        required=True,
        label="Other medical information",
        label_classes="nhsuk-label--l",
        page_heading=True,
        widget=Textarea(attrs={"rows": 10}),
        max_words=500,
        error_messages={
            "required": "Provide details of any relevant health conditions or medications that are not covered by symptoms or medical history questions",
            "max_words": "Other medical information must be 500 words or less",
        },
    )

    def __init__(self, *args, participant, **kwargs):
        self.instance = kwargs.pop("instance", None)

        if self.instance:
            kwargs["initial"] = self.initial_values(self.instance)

        super().__init__(*args, **kwargs)

    def initial_values(self, instance):
        return {
            "details": instance.details,
        }

    def create(self, appointment):
        return OtherMedicalInformation.objects.create(
            appointment=appointment,
            details=self.cleaned_data["details"],
        )

    def update(self):
        self.instance.details = self.cleaned_data["details"]
        self.instance.save()

        return self.instance
