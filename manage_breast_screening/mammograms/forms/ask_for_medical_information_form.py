from django import forms


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
