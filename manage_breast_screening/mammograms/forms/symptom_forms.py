from datetime import date

from django.db.models import TextChoices
from django.forms import (  # FIXME: create our own version of BooleanField
    BooleanField,
    Form,
    ValidationError,
)
from django.forms.widgets import Textarea

from manage_breast_screening.core.form_fields import (
    CharField,
    ChoiceField,
    SplitDateField,
)
from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.forms.choices import YesNo
from manage_breast_screening.forms.fields import yes_no_field
from manage_breast_screening.participants.models import (
    SymptomAreas,
    SymptomType,
    WhenStartedChoices,
)


class RightLeftOtherChoices(TextChoices):
    RIGHT_BREAST = SymptomAreas.RIGHT_BREAST
    LEFT_BREAST = SymptomAreas.LEFT_BREAST
    OTHER = SymptomAreas.OTHER


class LumpForm(Form):
    where_located = ChoiceField(
        choices=RightLeftOtherChoices,
        label="Where is the lump located?",
        label_classes="nhsuk-fieldset__legend--m",
    )
    other_area_description = CharField(
        required=False,
        label="Describe the specific area",
        label_classes="nhsuk-fieldset__legend--m",
        hint="For example, the left armpit",
    )
    how_long = ChoiceField(
        choices=WhenStartedChoices,
        label="How long has this symptom existed?",
        label_classes="nhsuk-fieldset__legend--m",
    )
    specific_date = SplitDateField(
        hint="For example, 3 2025",
        label="Date symptom started",
        label_classes="nhsuk-u-visually-hidden",
        required=False,
        include_day=False,
    )
    intermittent = BooleanField(required=False, label="The symptom is intermittent")
    recently_resolved = BooleanField(
        required=False, label="The symptom has recently resolved"
    )
    when_resolved = CharField(
        required=False, label="Describe when", hint="For example, 3 days ago"
    )
    investigated = yes_no_field(
        label="Has this been investigated?",
        label_classes="nhsuk-fieldset__legend--m",
    )
    investigated_details = CharField(
        required=False,
        label="Provide details",
        hint="Include where, when and the outcome",
    )
    additional_info = CharField(
        required=False,
        label="Additional info (optional)",
        label_classes="nhsuk-label--m",
        widget=Textarea(attrs={"rows": 4}),
    )

    def __init__(self, instance=None, **kwargs):
        self.instance = instance
        super().__init__(**kwargs)

    def clean(self):
        rules = [
            ("where_located", RightLeftOtherChoices.OTHER, "other_area_description"),
            ("how_long", WhenStartedChoices.SINCE_A_SPECIFIC_DATE, "specific_date"),
            ("investigated", YesNo.YES, "investigated_details"),
        ]

        for selected_field, selected_value, required_field in rules:
            if self.cleaned_data.get(selected_field) == selected_value:
                cleaned_value = self.cleaned_data.get(required_field)
                if isinstance(cleaned_value, str):
                    cleaned_value = cleaned_value.strip()

                if not cleaned_value:
                    self.add_error(
                        required_field,
                        ValidationError(
                            message=self.fields[required_field].error_messages[
                                "required"
                            ],
                            code="required",
                        ),
                    )

    def save(self, appointment, request):
        specific_date = self.cleaned_data.get("specific_date")
        auditor = Auditor.from_request(request)

        symptom = appointment.symptom_set.create(
            appointment=appointment,
            symptom_type_id=SymptomType.LUMP,
            reported_at=date.today(),
            area=self.cleaned_data["where_located"],
            area_description=self.cleaned_data.get("other_area_description"),
            investigated=self.cleaned_data.get("investigated") == YesNo.YES,
            when_started=self.cleaned_data.get("how_long"),
            year_started=specific_date.year if specific_date else None,
            month_started=specific_date.month if specific_date else None,
            intermittent=self.cleaned_data.get("intermittent", False),
            recently_resolved=self.cleaned_data.get("recently_resolved", False),
            when_resolved=self.cleaned_data.get("when_resolved"),
            additional_information=self.cleaned_data.get("additional_info"),
        )

        auditor.audit_create(symptom)

        return symptom
