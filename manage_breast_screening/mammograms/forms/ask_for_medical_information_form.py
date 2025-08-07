from django import forms

from manage_breast_screening.core.form_fields import ChoiceField


class AskForMedicalInformationForm(forms.Form):
    decision = ChoiceField(
        label="Has the participant shared any relevant medical information?",
        choices=(
            ("yes", "Yes"),
            ("no", "No - proceed to imaging"),
        ),
        required=True,
        widget=forms.RadioSelect(),
    )

    def save(self):
        pass
