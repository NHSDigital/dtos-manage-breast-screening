from django import forms
from django.db.models import TextChoices


class ProvideSpecialAppointmentDetailsForm(forms.Form):
    class SupportReasons(TextChoices):
        BREAST_IMPLANTS = ("BREAST_IMPLANTS", "Breast implants")
        MEDICAL_DEVICES = ("MEDICAL_DEVICES", "Implanted medical devices")
        VISION = ("VISION", "Vision")
        HEARING = ("HEARING", "Hearing")
        PHYSICAL_RESTRICTION = ("PHYSICAL_RESTRICTION", "Physical restriction")
        SOCIAL_EMOTIONAL_MENTAL_HEALTH = (
            "SOCIAL_EMOTIONAL_MENTAL_HEALTH",
            "Social, emotional, and mental health",
        )
        LANGUAGE = ("LANGUAGE", "Language")
        GENDER_IDENTITY = ("GENDER_IDENTITY", "Gender identity")
        OTHER = ("OTHER", "Other")

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
            self.fields[field_name] = forms.CharField(required=False, initial="")

        self.fields["any_temporary"] = forms.ChoiceField(
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
