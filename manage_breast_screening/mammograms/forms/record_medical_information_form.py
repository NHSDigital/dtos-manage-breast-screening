from django import forms


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
