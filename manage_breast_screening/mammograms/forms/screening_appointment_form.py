from django import forms


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
