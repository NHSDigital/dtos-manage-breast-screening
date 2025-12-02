from django.forms.widgets import Textarea

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.nhsuk_forms.fields import CharField, ChoiceField
from manage_breast_screening.nhsuk_forms.fields.integer_field import YearField
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields
from manage_breast_screening.participants.models.other_procedure_history_item import (
    OtherProcedureHistoryItem,
)


class OtherProcedureHistoryForm(FormWithConditionalFields):
    PROCEDURE_DETAIL_FIELDS = {
        OtherProcedureHistoryItem.Procedure.BREAST_REDUCTION: "breast_reduction_details",
        OtherProcedureHistoryItem.Procedure.BREAST_SYMMETRISATION: "breast_symmetrisation_details",
        OtherProcedureHistoryItem.Procedure.NIPPLE_CORRECTION: "nipple_correction_details",
        OtherProcedureHistoryItem.Procedure.OTHER: "other_details",
    }

    def __init__(self, *args, participant, **kwargs):
        self.instance = kwargs.pop("instance", None)

        if self.instance:
            kwargs["initial"] = self.initial_values(self.instance)

        super().__init__(*args, **kwargs)

        self.fields["procedure"] = ChoiceField(
            choices=OtherProcedureHistoryItem.Procedure,
            label=f"What procedure has {participant.first_name} had?",
            error_messages={"required": "Select the procedure"},
        )

        for procedure, detail_field in self.PROCEDURE_DETAIL_FIELDS.items():
            self.fields[detail_field] = CharField(
                required=False,
                label="Provide details",
                error_messages={"required": "Provide details of the procedure"},
                classes="nhsuk-u-width-two-thirds",
            )
            self.given_field_value("procedure", procedure).require_field(detail_field)

        self.fields["procedure_year"] = YearField(
            label="Year of procedure (optional)",
            label_classes="nhsuk-label--m",
            classes="nhsuk-input--width-4",
            hint="Leave blank if unknown",
            required=False,
        )
        self.fields["additional_details"] = CharField(
            hint="Include any other relevant information about the device or procedure",
            required=False,
            label="Additional details (optional)",
            label_classes="nhsuk-label--m",
            widget=Textarea(attrs={"rows": 4}),
            max_words=500,
            error_messages={
                "max_words": "Additional details must be 500 words or less"
            },
        )

    def initial_values(self, instance):
        initial = {
            "procedure": instance.procedure,
            "procedure_year": instance.procedure_year,
            "additional_details": instance.additional_details,
        }

        detail_field = self.PROCEDURE_DETAIL_FIELDS.get(instance.procedure)
        if detail_field:
            initial[detail_field] = instance.procedure_details

        return initial

    def create(self, appointment, request):
        auditor = Auditor.from_request(request)

        other_procedure_history_item = OtherProcedureHistoryItem.objects.create(
            appointment=appointment,
            procedure=self.cleaned_data["procedure"],
            procedure_details=self._get_selected_procedure_details(),
            procedure_year=self.cleaned_data.get("procedure_year"),
            additional_details=self.cleaned_data.get("additional_details", ""),
        )

        auditor.audit_create(other_procedure_history_item)

        return other_procedure_history_item

    def update(self, request):
        self.instance.procedure = self.cleaned_data["procedure"]
        self.instance.procedure_details = self._get_selected_procedure_details()
        self.instance.procedure_year = self.cleaned_data["procedure_year"]
        self.instance.additional_details = self.cleaned_data["additional_details"]
        self.instance.save()

        Auditor.from_request(request).audit_update(self.instance)

        return self.instance

    @property
    def procedure_detail_fields(self):
        return tuple(self.PROCEDURE_DETAIL_FIELDS.items())

    def _get_selected_procedure_details(self):
        procedure = self.cleaned_data.get("procedure")
        try:
            detail_field = self.PROCEDURE_DETAIL_FIELDS[procedure]
        except KeyError as exc:
            msg = f"Unsupported procedure '{procedure}'"
            raise ValueError(msg) from exc
        return self.cleaned_data.get(detail_field, "")
