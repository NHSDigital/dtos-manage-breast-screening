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
        if "participant" not in kwargs:
            raise ValueError("SpecialAppointmentForm requires a participant instance")
        self.participant = kwargs.pop("participant")
        super().__init__(*args, **kwargs)

        # Dynamically add the fields: each suppert reason has an associated field
        # for details.
        self.fields["support_reason"] = forms.MultipleChoiceField(
            choices=self.SupportReasons  # type: ignore
        )

        for option in self.SupportReasons:
            field_name = option.value[0].lower() + "_details"
            self.fields[field_name] = forms.CharField(required=False)

        self.fields["any_temporary"] = forms.ChoiceField(choices=self.TemporaryChoices)  # type: ignore

        self.set_initial_from_participant()

    def set_initial_from_participant(self):
        pass

    def save(self):
        """
        Save unconfirmed data to the participant record
        """
        pass
