from django import forms
from django.forms.widgets import Textarea

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.nhsuk_forms.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    YearField,
)
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields
from manage_breast_screening.participants.models.medical_history.implanted_medical_device_history_item import (
    ImplantedMedicalDeviceHistoryItem,
)


class ImplantedMedicalDeviceHistoryItemForm(FormWithConditionalFields):
    def __init__(self, *args, participant, instance=None, **kwargs):
        self.instance = instance

        if instance:
            kwargs["initial"] = {
                "device": instance.device,
                "other_medical_device_details": instance.other_medical_device_details,
                "device_has_been_removed": instance.device_has_been_removed,
                "removal_year": instance.removal_year,
                "procedure_year": instance.procedure_year,
                "additional_details": instance.additional_details,
            }

        super().__init__(*args, **kwargs)

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
        self.fields["procedure_year"] = YearField(
            hint="Leave blank if unknown",
            required=False,
            label="Year of procedure (optional)",
            label_classes="nhsuk-label--m",
            classes="nhsuk-input--width-4",
        )
        self.fields["device_has_been_removed"] = BooleanField(
            required=False,
            label="Implanted device has been removed",
            classes="app-checkboxes",
        )
        self.fields["removal_year"] = YearField(
            required=False,
            label="Year removed (if available)",
            classes="nhsuk-input--width-4",
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

    def model_values(self):
        return dict(
            device=self.cleaned_data.get("device", ""),
            other_medical_device_details=self.cleaned_data.get(
                "other_medical_device_details", ""
            ),
            device_has_been_removed=self.cleaned_data.get("device_has_been_removed"),
            removal_year=self.cleaned_data.get("removal_year", ""),
            procedure_year=self.cleaned_data.get("procedure_year", ""),
            additional_details=self.cleaned_data.get("additional_details", ""),
        )

    def full_clean(self):
        # if a removal_year is provided then remove it if device_has_been_removed is False
        if self.data.get("removal_year") and not self.data.get(
            "device_has_been_removed"
        ):
            # makes QueryDict mutable
            self.data = self.data.copy()
            self.data["removal_year"] = None
            if hasattr(self.data, "_mutable"):
                self.data._mutable = False

        super().full_clean()

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

    def update(self, request):
        if self.instance is None:
            raise ValueError("Form has no instance")

        self.instance.device = self.cleaned_data["device"]
        self.instance.other_medical_device_details = self.cleaned_data[
            "other_medical_device_details"
        ]
        self.instance.device_has_been_removed = self.cleaned_data[
            "device_has_been_removed"
        ]
        self.instance.removal_year = self.cleaned_data["removal_year"]
        self.instance.procedure_year = self.cleaned_data["procedure_year"]
        self.instance.additional_details = self.cleaned_data["additional_details"]
        self.instance.save()

        Auditor.from_request(request).audit_update(self.instance)

        return self.instance
