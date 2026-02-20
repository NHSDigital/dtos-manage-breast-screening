from django import forms
from django.forms import Textarea

from manage_breast_screening.nhsuk_forms.fields import (
    CharField,
    MultipleChoiceField,
)
from manage_breast_screening.participants.models import SupportReasons


class ProvideSpecialAppointmentDetailsForm(forms.Form):
    SupportReasons = SupportReasons

    SupportReasonHints = {
        SupportReasons.PHYSICAL_RESTRICTION: "For example, mobility or dexterity",
        SupportReasons.SOCIAL_EMOTIONAL_MENTAL_HEALTH: "For example, neurodiversity or agoraphobia",
    }

    def __init__(self, *args, participant, **kwargs):
        self.saved_data = kwargs.pop("saved_data", {}) or {}

        super().__init__(*args, **kwargs)

        # Populate the initial data based on the JSON field
        self._init_from_json(participant.extra_needs)

        # Allow all reasons to be unselected if editing, rather than creating
        # a special appointment.
        self.fields["support_reasons"] = MultipleChoiceField(
            label=f"Why does {participant.full_name} need additional support?",
            hint="Select all that apply. When describing support required, include any special requests made by the participant or their carer.",
            choices=self.SupportReasons,  # type: ignore
            required=("support_reasons" not in self.initial),
            error_messages={"required": "Select a reason"},
        )

        # Each support reason has an associated field for details.
        for option in self.SupportReasons:
            field_name = option.value.lower() + "_details"
            self.fields[field_name] = CharField(
                required=False,
                initial="",
                label="Describe support required",
                widget=Textarea,
                hint=self.SupportReasonHints.get(option),
            )

    def clean(self):
        for reason in self.cleaned_data.get("support_reasons", []):
            details_field = reason.lower() + "_details"
            if not self.cleaned_data.get(details_field, "").strip():
                self.add_error(
                    details_field,
                    forms.ValidationError(
                        message="Describe the support required", code="required"
                    ),
                )

    def to_json(self):
        """
        Generate JSON that can be stored on the participant record
        """
        result = {}

        for reason in self.cleaned_data.get("support_reasons", []):
            result[reason] = {
                "details": self.cleaned_data.get(reason.lower() + "_details", "")
            }
        return result

    def _init_from_json(self, json):
        """
        Set initial values from JSON stored on the participant record
        """
        if not json:
            return

        initial = {"support_reasons": []}
        for reason in self.SupportReasons:
            if reason in json:
                need = json[reason]
                initial["support_reasons"].append(reason.value)
                initial[reason.value.lower() + "_details"] = need["details"]

        self.initial = initial
