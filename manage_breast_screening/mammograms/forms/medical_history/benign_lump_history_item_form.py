from django.forms import Textarea

from manage_breast_screening.nhsuk_forms.fields.char_field import CharField
from manage_breast_screening.nhsuk_forms.fields.choice_fields import (
    ChoiceField,
    MultipleChoiceField,
)
from manage_breast_screening.nhsuk_forms.fields.integer_field import YearField
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields
from manage_breast_screening.participants.models.medical_history.benign_lump_history_item import (
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
        visually_hidden_label_prefix="What procedure have they had in their ",
        visually_hidden_label_suffix="?",
        choices=BenignLumpHistoryItem.Procedure,
        exclusive_choices={"NO_PROCEDURES"},
        error_messages={
            "required": "Select which procedures they have had in the left breast",
        },
    )
    right_breast_procedures = MultipleChoiceField(
        label="Right breast",
        label_classes="nhsuk-fieldset__legend--s",
        visually_hidden_label_prefix="What procedure have they had in their ",
        visually_hidden_label_suffix="?",
        choices=BenignLumpHistoryItem.Procedure,
        exclusive_choices={"NO_PROCEDURES"},
        error_messages={
            "required": "Select which procedures they have had in the right breast",
        },
    )

    procedure_year = YearField(
        label="Year of procedure (optional)",
        label_classes="nhsuk-label--m",
        classes="nhsuk-input--width-4",
        hint="Leave blank if unknown",
        required=False,
    )

    procedure_location = ChoiceField(
        label="Where were the tests and treatment done?",
        choices=BenignLumpHistoryItem.ProcedureLocation,
        error_messages={
            "required": "Select where the tests and treatment were done",
        },
    )
    nhs_hospital_details = CharField(
        label="Provide details",
        required=False,
        error_messages={
            "required": "Provide details about where the surgery and treatment took place"
        },
    )
    private_clinic_uk_details = CharField(
        label="Provide details",
        required=False,
        error_messages={
            "required": "Provide details about where the surgery and treatment took place"
        },
    )
    outside_uk_details = CharField(
        label="Provide details",
        required=False,
        error_messages={
            "required": "Provide details about where the surgery and treatment took place"
        },
    )
    multiple_locations_details = CharField(
        label="Provide details",
        required=False,
        error_messages={
            "required": "Provide details about where the surgery and treatment took place"
        },
    )
    exact_location_unknown_details = CharField(
        label="Provide details",
        required=False,
        error_messages={
            "required": "Provide details about where the surgery and treatment took place"
        },
    )

    additional_details = CharField(
        label="Additional details (optional)",
        label_classes="nhsuk-label--m",
        required=False,
        widget=Textarea(attrs={"rows": 3}),
        hint="Include any other relevant information about the procedure (optional)",
    )

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance

        if self.instance:
            kwargs["initial"] = self.initial_values(self.instance)

        super().__init__(*args, **kwargs)

        for location, detail_field in self.LOCATION_DETAIL_FIELDS.items():
            self.given_field_value("procedure_location", location).require_field(
                detail_field
            )

    def initial_values(self, instance):
        initial = {
            "left_breast_procedures": instance.left_breast_procedures,
            "right_breast_procedures": instance.right_breast_procedures,
            "procedure_year": instance.procedure_year,
            "procedure_location": instance.procedure_location,
            "additional_details": instance.additional_details,
        }

        detail_field = self.LOCATION_DETAIL_FIELDS.get(instance.procedure_location)
        if detail_field:
            initial[detail_field] = instance.procedure_location_details

        return initial

    def create(self, appointment):
        benign_lump_history_item = BenignLumpHistoryItem.objects.create(
            appointment=appointment,
            left_breast_procedures=self.cleaned_data.get("left_breast_procedures", []),
            right_breast_procedures=self.cleaned_data.get(
                "right_breast_procedures", []
            ),
            procedure_year=self.cleaned_data.get("procedure_year"),
            procedure_location=self.cleaned_data["procedure_location"],
            procedure_location_details=self._get_selected_location_details(),
            additional_details=self.cleaned_data.get("additional_details", ""),
        )

        return benign_lump_history_item

    def update(self):
        if self.instance is None:
            raise ValueError("Form has no instance")

        self.instance.left_breast_procedures = self.cleaned_data.get(
            "left_breast_procedures", []
        )
        self.instance.right_breast_procedures = self.cleaned_data.get(
            "right_breast_procedures", []
        )
        self.instance.procedure_year = self.cleaned_data.get("procedure_year")
        self.instance.procedure_location = self.cleaned_data["procedure_location"]
        self.instance.procedure_location_details = self._get_selected_location_details()
        self.instance.additional_details = self.cleaned_data.get(
            "additional_details", ""
        )

        self.instance.save()

        return self.instance

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
