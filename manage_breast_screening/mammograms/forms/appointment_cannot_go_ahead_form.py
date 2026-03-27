from django import forms

from manage_breast_screening.mammograms.services.appointment_services import (
    AppointmentStatusUpdater,
)
from manage_breast_screening.nhsuk_forms.fields import (
    CharField,
    ChoiceField,
    MultipleChoiceField,
)


class AppointmentCannotGoAheadForm(forms.Form):
    STOPPED_REASON_CHOICES = (
        ("failed_identity_check", "Failed identity check"),
        ("pain_during_screening", "Pain during screening"),
        ("symptomatic_appointment", "Has a symptomatic appointment"),
        ("participant_withdrew_consent", "Consent withdrawn"),
        ("physical_health_issue", "Physical health issue"),
        ("mental_health_issue", "Mental health issue"),
        ("language_difficulties", "Language difficulties"),
        ("no_mammographer", "No qualified mammographer available"),
        ("technical_issues", "Technical issues at clinic"),
        ("other", "Other reason"),
    )

    def __init__(self, *args, **kwargs):
        if "instance" not in kwargs:
            raise ValueError("AppointmentCannotGoAheadForm requires an instance")
        self.instance = kwargs.pop("instance")
        super().__init__(*args, **kwargs)

        # Dynamically add detail fields for each choice
        for choice_value, _ in self.STOPPED_REASON_CHOICES:
            details_field_name = f"{choice_value}_details"
            if choice_value == "other":
                self.fields[details_field_name] = CharField(
                    required=False,
                    label="Provide details",
                    widget=forms.Textarea(attrs={"rows": 5}),
                )
            else:
                self.fields[details_field_name] = CharField(
                    required=False, label="Provide details"
                )

        # Ensure that the field order matches the order we want to render in
        details_fields = [
            f"{field_name}_details" for field_name, _ in self.STOPPED_REASON_CHOICES
        ]
        self.order_fields(["stopped_reasons"] + details_fields + ["decision"])

    stopped_reasons = MultipleChoiceField(
        label="Why has this appointment been stopped?",
        choices=STOPPED_REASON_CHOICES,
        required=True,
        error_messages={
            "required": "A reason for why this appointment cannot continue must be provided"
        },
    )

    decision = ChoiceField(
        label="Does the appointment need to be rescheduled?",
        choices=(
            ("True", "Yes, add participant to reinvite list"),
            ("False", "No"),
        ),
        required=True,
        widget=forms.RadioSelect(),
        error_messages={
            "required": "Select whether the participant needs to be invited for another appointment"
        },
    )

    def clean(self):
        cleaned_data = super().clean()

        if (
            "stopped_reasons" in cleaned_data
            and "other" in cleaned_data["stopped_reasons"]
        ):
            if not cleaned_data.get("other_details"):
                self.add_error(
                    "other_details", "Explain why this appointment cannot proceed"
                )

        return cleaned_data

    def save(self, current_user):
        AppointmentStatusUpdater(
            self.instance, current_user=current_user
        ).mark_attended_not_screened()

        reasons_json = {}
        selected_stopped_reasons = self.cleaned_data["stopped_reasons"]
        reasons_json["stopped_reasons"] = selected_stopped_reasons
        for field_name, value in self.cleaned_data.items():
            if (
                field_name.endswith("_details")
                and field_name.replace("_details", "") in selected_stopped_reasons
                and value
            ):
                reasons_json[field_name] = value
        self.instance.stopped_reasons = reasons_json
        self.instance.reinvite = self.cleaned_data["decision"]
        self.instance.save()

        return self.instance
