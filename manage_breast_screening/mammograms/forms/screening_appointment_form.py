from django import forms

from manage_breast_screening.nhsuk_forms.fields import ChoiceField


class ScreeningAppointmentForm(forms.Form):
    decision = ChoiceField(
        label="Can the appointment go ahead?",
        label_classes="nhsuk-fieldset__legend--m",
        hint="Before you proceed, check the participant’s identity and confirm that their last mammogram was more than 6 months ago.",
        choices=(
            ("continue", "Yes, go to medical information"),
            ("dropout", "No, screening cannot proceed"),
        ),
        required=True,
        widget=forms.RadioSelect(),
    )

    def save(self):
        pass
