from django.forms import Form
from django.forms.widgets import Textarea

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.nhsuk_forms.fields import (
    CharField,
    ChoiceField,
)
from manage_breast_screening.participants.models.cyst_history_item import (
    CystHistoryItem,
)


class CystHistoryForm(Form):
    def __init__(self, *args, participant, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["treatment"] = ChoiceField(
            choices=CystHistoryItem.Treatment,
            label=f"What breast cyst treatment has {participant.first_name} had?",
            error_messages={"required": "Select the treatment type"},
        )
        self.fields["additional_details"] = CharField(
            hint="Include any other relevant information about the procedure",
            required=False,
            label="Additional details (optional)",
            label_classes="nhsuk-label--m",
            widget=Textarea(attrs={"rows": 4}),
            max_words=500,
            error_messages={
                "max_words": "Additional details must be 500 words or less"
            },
        )

    def model_values(self):
        return dict(
            treatment=self.cleaned_data.get("treatment", ""),
            additional_details=self.cleaned_data.get("additional_details", ""),
        )

    def create(self, appointment, request):
        auditor = Auditor.from_request(request)
        field_values = self.model_values()

        cyst_history = appointment.cyst_history_items.create(
            appointment=appointment,
            **field_values,
        )

        auditor.audit_create(cyst_history)

        return cyst_history
