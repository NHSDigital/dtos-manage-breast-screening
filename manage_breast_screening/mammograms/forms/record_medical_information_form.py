from django import forms

from manage_breast_screening.core.form_fields import ChoiceField


class RecordMedicalInformationForm(forms.Form):
    decision = ChoiceField(
        label="Can imaging go ahead?",
        choices=(
            ("continue", "Yes, mark incomplete sections as ‘none’ or ‘no’"),
            ("dropout", "No, screening cannot proceed"),
        ),
        required=True,
        widget=forms.RadioSelect(),
    )

    def save(self):
        pass
