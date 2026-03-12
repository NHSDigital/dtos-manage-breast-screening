from django import forms


class ParticipantCsvUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="CSV File",
        widget=forms.FileInput(attrs={"accept": ".csv"}),
        error_messages={
            "required": "Select a CSV file to upload",
        },
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data["csv_file"]
        if not csv_file.name.lower().endswith(".csv"):
            raise forms.ValidationError("File must be a CSV.")
        return csv_file
