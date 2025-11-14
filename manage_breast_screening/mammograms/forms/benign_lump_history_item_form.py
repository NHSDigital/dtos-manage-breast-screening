from django.forms import Textarea

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.nhsuk_forms.fields.char_field import CharField
from manage_breast_screening.nhsuk_forms.fields.choice_fields import (
    ChoiceField,
    MultipleChoiceField,
)
from manage_breast_screening.nhsuk_forms.fields.integer_field import IntegerField
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields
from manage_breast_screening.participants.models.benign_lump_history_item import (
    BenignLumpHistoryItem,
)


class BenignLumpHistoryItemForm(FormWithConditionalFields):
    LOCATION_DETAIL_FIELDS = {
        BenignLumpHistoryItem.ProcedureLocation.NHS_HOSPITAL: "nhs_hospital_details",
        BenignLumpHistoryItem.ProcedureLocation.PRIVATE_CLINIC_UK: "private_clinic_uk_details",
        BenignLumpHistoryItem.ProcedureLocation.OUTSIDE_UK: "outside_uk_details",
        BenignLumpHistoryItem.ProcedureLocation.MULTIPLE_LOCATIONS: "multiple_locations_details",
        BenignLumpHistoryItem.ProcedureLocation.EXACT_LOCATION_UNKNOWN: "exact_location_unknown_details",
    }

    left_breast_procedures = MultipleChoiceField(
        label="Left breast",
        label_classes="nhsuk-fieldset__legend--s",
        choices=BenignLumpHistoryItem.Procedure,
    )
    right_breast_procedures = MultipleChoiceField(
        label="Right breast",
        label_classes="nhsuk-fieldset__legend--s",
        choices=BenignLumpHistoryItem.Procedure,
    )

    procedure_year = IntegerField(
        label="Year of procedure (optional)",
        label_classes="nhsuk-label--m",
        classes="nhsuk-input--width-4",
        hint="Leave blank if unknown",
        required=False,
    )

    procedure_location = ChoiceField(
        label="Where were the tests and treatment done?",
        choices=BenignLumpHistoryItem.ProcedureLocation,
    )
    nhs_hospital_details = CharField(label="Provide details", required=False)
    private_clinic_uk_details = CharField(label="Provide details", required=False)
    outside_uk_details = CharField(label="Provide details", required=False)
    multiple_locations_details = CharField(label="Provide details", required=False)
    exact_location_unknown_details = CharField(label="Provide details", required=False)

    additional_details = CharField(
        label="Additional details (optional)",
        label_classes="nhsuk-label--m",
        required=False,
        widget=Textarea(attrs={"rows": 3}),
        hint="Include any other relevant information about the procedure (optional)",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for location, detail_field in self.LOCATION_DETAIL_FIELDS.items():
            self.given_field_value("procedure_location", location).require_field(
                detail_field
            )

    def create(self, request):
        auditor = Auditor.from_request(request)

        benign_lump_history_item = BenignLumpHistoryItem.objects.create(
            appointment=self.appointment,
            left_breast_procedures=self.cleaned_data.get("left_breast_procedures", []),
            right_breast_procedures=self.cleaned_data.get(
                "right_breast_procedures", []
            ),
            procedure_year=self.cleaned_data.get("procedure_year"),
            procedure_location=self.cleaned_data["procedure_location"],
            procedure_location_details=self._get_selected_location_details(),
            additional_details=self.cleaned_data.get("additional_details", ""),
        )

        auditor.audit_create(benign_lump_history_item)

        return benign_lump_history_item

    @property
    def location_detail_fields(self):
        return tuple(self.LOCATION_DETAIL_FIELDS.items())

    def _get_selected_location_details(self):
        location = self.cleaned_data.get("procedure_location")
        try:
            detail_field = self.LOCATION_DETAIL_FIELDS[location]
        except KeyError as exc:
            msg = f"Unsupported procedure location '{location}'"
            raise ValueError(msg) from exc
        return self.cleaned_data.get(detail_field, "")
