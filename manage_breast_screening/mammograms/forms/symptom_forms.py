from datetime import date

from django.db.models import TextChoices
from django.forms import Form, ValidationError
from django.forms.widgets import Textarea

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.nhsuk_forms.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    SplitDateField,
)
from manage_breast_screening.nhsuk_forms.fields.choice_fields import (
    RadioSelectWithoutFieldset,
)
from manage_breast_screening.nhsuk_forms.utils import YesNo, yes_no, yes_no_field
from manage_breast_screening.participants.models.symptom import (
    RelativeDateChoices,
    SymptomAreas,
    SymptomType,
)


class RightLeftOtherChoices(TextChoices):
    RIGHT_BREAST = SymptomAreas.RIGHT_BREAST.value, SymptomAreas.RIGHT_BREAST.label
    LEFT_BREAST = SymptomAreas.LEFT_BREAST.value, SymptomAreas.LEFT_BREAST.label
    OTHER = SymptomAreas.OTHER.value, SymptomAreas.OTHER.label


class LumpForm(Form):
    area = ChoiceField(
        choices=RightLeftOtherChoices,
        label="Where is the lump located?",
        error_messages={"required": "Select the location of the lump"},
    )
    area_description = CharField(
        required=False,
        label="Describe the specific area",
        hint="For example, the left armpit",
        error_messages={
            "required": "Describe the specific area where the lump is located"
        },
        classes="nhsuk-u-width-two-thirds",
    )
    when_started = ChoiceField(
        choices=RelativeDateChoices,
        label="How long has this symptom existed?",
        widget=RadioSelectWithoutFieldset,
        error_messages={"required": "Select how long the symptom has existed"},
    )
    specific_date = SplitDateField(
        hint="For example, 3 2025",
        label="Date symptom started",
        label_classes="nhsuk-u-visually-hidden",
        required=False,
        include_day=False,
        error_messages={"required": "Enter the date the symptom started"},
    )
    intermittent = BooleanField(required=False, label="The symptom is intermittent")
    recently_resolved = BooleanField(
        required=False, label="The symptom has recently resolved"
    )
    when_resolved = CharField(
        required=False,
        label="Describe when",
        hint="For example, 3 days ago",
        classes="nhsuk-u-width-two-thirds",
    )
    investigated = yes_no_field(
        label="Has this been investigated?",
        error_messages={
            "required": "Select whether the lump has been investigated or not"
        },
    )
    investigation_details = CharField(
        required=False,
        label="Provide details",
        hint="Include where, when and the outcome",
        error_messages={"required": "Enter details of any investigations"},
        classes="nhsuk-u-width-two-thirds",
    )
    additional_information = CharField(
        required=False,
        label="Additional info (optional)",
        label_classes="nhsuk-label--m",
        widget=Textarea(attrs={"rows": 4}),
    )

    def __init__(self, instance=None, **kwargs):
        self.instance = instance

        if instance:
            kwargs["initial"] = {
                "area": instance.area,
                "area_description": instance.area_description,
                "when_started": instance.when_started,
                "specific_date": (instance.month_started, instance.year_started),
                "intermittent": instance.intermittent,
                "recently_resolved": instance.recently_resolved,
                "when_resolved": instance.when_resolved,
                "investigated": yes_no(instance.investigated),
                "investigation_details": instance.investigation_details,
                "additional_information": instance.additional_information,
            }

        super().__init__(**kwargs)

    def clean(self):
        rules = [
            ("area", RightLeftOtherChoices.OTHER, "area_description"),
            (
                "when_started",
                RelativeDateChoices.SINCE_A_SPECIFIC_DATE,
                "specific_date",
            ),
            ("investigated", YesNo.YES, "investigation_details"),
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

    def update(self, request):
        auditor = Auditor.from_request(request)
        field_values = self._model_values()
        symptom = self.instance

        if symptom is None:
            raise ValueError("attempting to update but instance is None")

        for fieldname, value in field_values.items():
            setattr(symptom, fieldname, value)

        symptom.save(update_fields=field_values.keys())

        auditor.audit_update(symptom)

        return symptom

    def create(self, appointment, request):
        auditor = Auditor.from_request(request)
        field_values = self._model_values()

        symptom = appointment.symptom_set.create(
            appointment=appointment,
            symptom_type_id=SymptomType.LUMP,
            reported_at=date.today(),
            **field_values,
        )

        auditor.audit_create(symptom)

        return symptom

    def _model_values(self):
        """
        Further clean the form data to match the model, including
        splitting year/month tuples into multiple fields, and blanking
        conditionally revealed fields that are no longer visible.
        """
        area = self.cleaned_data["area"]
        area_description = (
            self.cleaned_data.get("area_description", "")
            if area == SymptomAreas.OTHER
            else ""
        )

        when_started = self.cleaned_data.get("when_started")
        specific_date = (
            self.cleaned_data.get("specific_date")
            if when_started == RelativeDateChoices.SINCE_A_SPECIFIC_DATE
            else None
        )

        investigated = self.cleaned_data.get("investigated") == YesNo.YES
        investigation_details = (
            self.cleaned_data.get("investigation_details", "") if investigated else ""
        )

        intermittent = self.cleaned_data.get("intermittent", False)

        recently_resolved = self.cleaned_data.get("recently_resolved", False)
        when_resolved = (
            self.cleaned_data.get("when_resolved") if recently_resolved else ""
        )

        additional_information = self.cleaned_data.get("additional_information", "")

        return dict(
            area=area,
            area_description=area_description,
            investigated=investigated,
            investigation_details=investigation_details,
            when_started=when_started,
            year_started=specific_date.year if specific_date else None,
            month_started=specific_date.month if specific_date else None,
            intermittent=intermittent,
            recently_resolved=recently_resolved,
            when_resolved=when_resolved,
            additional_information=additional_information,
        )
