import datetime

from django import forms
from django.db.models import TextChoices
from django.forms.widgets import Textarea

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.nhsuk_forms.fields import (
    CharField,
    ChoiceField,
    IntegerField,
)
from manage_breast_screening.nhsuk_forms.fields.choice_fields import (
    MultipleChoiceField,
)
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields
from manage_breast_screening.participants.models.implanted_medical_device_history_item import (
    ImplantedMedicalDeviceHistoryItem,
)


class RemovalStatusChoices(TextChoices):
    HAS_BEEN_REMOVED = "HAS_BEEN_REMOVED", "Implanted device has been removed"


class ImplantedMedicalDeviceHistoryForm(FormWithConditionalFields):
    def __init__(self, *args, participant, **kwargs):
        super().__init__(*args, **kwargs)

        # if entered, years should be between 80 years ago and this year
        max_year = datetime.date.today().year
        min_year = max_year - 80
        year_outside_range_error_message = (
            f"Year should be between {min_year} and {max_year}."
        )
        year_invalid_format_error_message = "Enter year as a number."

        self.fields["device"] = ChoiceField(
            choices=ImplantedMedicalDeviceHistoryItem.Device,
            label=f"What device does {participant.first_name} have?",
            error_messages={"required": "Select the device type"},
        )
        self.fields["other_medical_device_details"] = CharField(
            required=False,
            label="Provide details",
            error_messages={"required": "Provide details of the device"},
            classes="nhsuk-u-width-two-thirds",
        )
        self.fields["procedure_year"] = IntegerField(
            hint="Leave blank if unknown",
            required=False,
            label="Year of procedure (optional)",
            label_classes="nhsuk-label--m",
            classes="nhsuk-input--width-4",
            min_value=min_year,
            max_value=max_year,
            error_messages={
                "min_value": year_outside_range_error_message,
                "max_value": year_outside_range_error_message,
                "invalid": year_invalid_format_error_message,
            },
        )
        self.fields["removal_status"] = MultipleChoiceField(
            required=False,
            choices=RemovalStatusChoices,
            widget=forms.CheckboxSelectMultiple,
            label="Removed implants",
            classes="app-checkboxes",
        )
        self.fields["removal_year"] = IntegerField(
            required=False,
            label="Year removed",
            classes="nhsuk-input--width-4",
            min_value=min_year,
            max_value=max_year,
            error_messages={
                "required": "Enter the year the device was removed",
                "min_value": year_outside_range_error_message,
                "max_value": year_outside_range_error_message,
                "invalid": year_invalid_format_error_message,
            },
        )
        self.fields["additional_details"] = CharField(
            hint="Include any other relevant information about the device or procedure",
            required=False,
            label="Additional details (optional)",
            label_classes="nhsuk-label--m",
            widget=Textarea(attrs={"rows": 4}),
            max_words=500,
            error_messages={
                "max_words": "Additional details must be 500 words or less"
            },
        )

        self.given_field_value(
            "device", ImplantedMedicalDeviceHistoryItem.Device.OTHER_MEDICAL_DEVICE
        ).require_field("other_medical_device_details")
        self.given_field_value(
            "removal_status", RemovalStatusChoices.HAS_BEEN_REMOVED
        ).require_field("removal_year")

    def model_values(self):
        return dict(
            device=self.cleaned_data.get("device", ""),
            other_medical_device_details=self.cleaned_data.get(
                "other_medical_device_details", ""
            ),
            removal_year=self.cleaned_data.get("removal_year", ""),
            procedure_year=self.cleaned_data.get("procedure_year", ""),
            additional_details=self.cleaned_data.get("additional_details", ""),
        )

    def create(self, appointment, request):
        auditor = Auditor.from_request(request)
        field_values = self.model_values()

        implanted_medical_device_history = (
            appointment.implanted_medical_device_history_items.create(
                appointment=appointment,
                **field_values,
            )
        )

        auditor.audit_create(implanted_medical_device_history)

        return implanted_medical_device_history

    def clean(self):
        cleaned_data = super().clean()
        procedure_year = cleaned_data.get("procedure_year")
        removal_year = cleaned_data.get("removal_year")
        if procedure_year and removal_year and procedure_year > removal_year:
            self.add_error(
                "removal_year",
                forms.ValidationError(
                    message="Year removed cannot be before year of procedure",
                    code="required",
                ),
            )
