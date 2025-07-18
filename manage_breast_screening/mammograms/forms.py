from django import forms

from ..participants.models import AppointmentStatus


class ScreeningAppointmentForm(forms.Form):
    decision = forms.ChoiceField(
        choices=(
            ("continue", "Yes, go to medical information"),
            ("dropout", "No, screening cannot proceed"),
        ),
        required=True,
        widget=forms.RadioSelect(),
    )

    def save(self):
        pass


class AskForMedicalInformationForm(forms.Form):
    decision = forms.ChoiceField(
        choices=(
            ("yes", "Yes"),
            ("no", "No - proceed to imaging"),
        ),
        required=True,
        widget=forms.RadioSelect(),
    )

    def save(self):
        pass


class RecordMedicalInformationForm(forms.Form):
    decision = forms.ChoiceField(
        choices=(
            ("continue", "Yes, mark incomplete sections as ‘none’ or ‘no’"),
            ("dropout", "No, screening cannot proceed"),
        ),
        required=True,
        widget=forms.RadioSelect(),
    )

    def save(self):
        pass


class AppointmentCannotGoAheadForm(forms.Form):
    STOPPED_REASON_CHOICES = (
        ("participant_did_not_attend", "Participant did not attend"),
        ("failed_identity_check", "Failed identity check"),
        ("language_difficulties", "Language difficulties"),
        ("physical_health_issue", "Physical health issue"),
        ("mental_health_issue", "Mental health issue"),
        ("last_mammogram_within_6_months", "Last mammogram within 6 months"),
        ("breast_implant_risks", "Breast implant risks"),
        ("pain_during_screening", "Pain during screening"),
        ("technical_issues", "Technical issues"),
        ("participant_withdrew_consent", "Participant withdrew consent"),
        ("other", "Other"),
    )

    def __init__(self, *args, **kwargs):
        if "instance" not in kwargs:
            raise ValueError("AppointmentCannotGoAheadForm requires an instance")
        self.instance = kwargs.pop("instance")
        super().__init__(*args, **kwargs)

        # Dynamically add detail fields for each choice
        for field_name, _ in self.STOPPED_REASON_CHOICES:
            self.fields[f"{field_name}_details"] = forms.CharField(required=False)

        # Ensure that the field order matches the order we want to render in
        details_fields = [
            f"{field_name}_details" for field_name, _ in self.STOPPED_REASON_CHOICES
        ]
        self.order_fields(["stopped_reasons"] + details_fields + ["decision"])

    stopped_reasons = forms.MultipleChoiceField(
        choices=STOPPED_REASON_CHOICES,
        required=True,
        error_messages={
            "required": "A reason for why this appointment cannot continue must be provided"
        },
    )

    decision = forms.ChoiceField(
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

    def save(self):
        reasons_json = {}
        reasons_json["stopped_reasons"] = self.cleaned_data["stopped_reasons"]
        for field_name, value in self.cleaned_data.items():
            if field_name.endswith("_details") and value:
                reasons_json[field_name] = value
        self.instance.stopped_reasons = reasons_json
        self.instance.reinvite = self.cleaned_data["decision"]
        self.instance.save()
        self.instance.statuses.create(state=AppointmentStatus.ATTENDED_NOT_SCREENED)

        return self.instance
