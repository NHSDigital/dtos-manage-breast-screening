from django import forms
from django.db.models import TextChoices
from django.forms import Textarea

from manage_breast_screening.core.form_fields import CharField, ChoiceField
from manage_breast_screening.participants.models import SupportReasons


class ProvideSpecialAppointmentDetailsForm(forms.Form):
    SupportReasons = SupportReasons

    class TemporaryChoices(TextChoices):
        YES = ("YES", "Yes")
        NO = ("NO", "No")

    SupportReasonHints = {
        SupportReasons.PHYSICAL_RESTRICTION: "For example, mobility or dexterity",
        SupportReasons.SOCIAL_EMOTIONAL_MENTAL_HEALTH: "For example, neurodiversity or agoraphobia",
    }

    def __init__(self, *args, **kwargs):
        self.saved_data = kwargs.pop("saved_data", {}) or {}

        super().__init__(*args, **kwargs)

        # Populate the initial data based on the JSON field
        self._init_from_json(self.saved_data)

        # Allow all reasons to be unselected if editing, rather than creating
        # a special appointment.
        self.fields["support_reasons"] = forms.MultipleChoiceField(
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

        self.fields["any_temporary"] = ChoiceField(
            label="Are any of these reasons temporary?",
            hint="This includes issues that are likely to be resolved by their next mammogram, for example a broken foot or a short-term eye problem.",
            choices=self.TemporaryChoices,  # type: ignore
            required=True,
            error_messages={
                "required": "Select whether any of the reasons are temporary"
            },
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
        any_temporary = (
            self.cleaned_data.get("any_temporary") == self.TemporaryChoices.YES
        )

        for reason in self.cleaned_data.get("support_reasons", []):
            need = {"details": self.cleaned_data.get(reason.lower() + "_details", "")}
            if not any_temporary:
                need["temporary"] = False
            else:
                # Preserve answers from the second form if we are editing the first form
                existing_value = self.saved_data.get(reason, {}).get("temporary")
                if existing_value is not None:
                    need["temporary"] = existing_value

            result[reason] = need
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

        if any(need.get("temporary") for need in json.values()):
            initial["any_temporary"] = self.TemporaryChoices.YES  # type: ignore
        else:
            initial["any_temporary"] = self.TemporaryChoices.NO  # type: ignore

        self.initial = initial


class MarkReasonsTemporaryForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.saved_data = kwargs.pop("saved_data", {}) or {}
        super().__init__(*args, **kwargs)

        choices = [
            (reason.value, reason.label)
            for reason in ProvideSpecialAppointmentDetailsForm.SupportReasons
            if reason.value in self.saved_data
        ]

        self.fields["which_are_temporary"] = forms.MultipleChoiceField(
            choices=choices,  # type: ignore
            required=True,
            error_messages={"required": "Select which reasons are temporary"},
        )

        # Populate the initial data based on the JSON field
        self._init_from_json(self.saved_data)

    def to_json(self):
        """
        Generate JSON that can be stored on the participant record
        """
        result = self.saved_data
        for reason, details in self.saved_data.items():
            temporary = reason in self.cleaned_data.get("which_are_temporary", [])
            details["temporary"] = temporary

        return result

    def _init_from_json(self, json):
        """
        Set initial values from JSON stored on the participant record
        """
        if not json:
            return

        self.initial = {
            "which_are_temporary": [
                reason
                for reason, details in self.saved_data.items()
                if details and details.get("temporary", False)
            ]
        }
