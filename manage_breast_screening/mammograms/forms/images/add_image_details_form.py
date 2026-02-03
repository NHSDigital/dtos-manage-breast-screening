from django.forms.widgets import Textarea

from manage_breast_screening.manual_images.services import StudyService
from manage_breast_screening.nhsuk_forms.fields import CharField, IntegerField
from manage_breast_screening.nhsuk_forms.fields.integer_field import StepperInput
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields
from manage_breast_screening.participants.models.appointment import (
    AppointmentWorkflowStepCompletion,
)


class AddImageDetailsForm(FormWithConditionalFields):
    rmlo_count = IntegerField(
        label="RMLO",
        classes="nhsuk-input--width-4",
        required=True,
        min_value=0,
        max_value=20,
        initial=1,
        error_messages={
            "min_value": "Number of RMLO images must be at least 0.",
            "max_value": "Number of RMLO images must be at most 20.",
            "invalid": "Enter a valid number of RMLO images.",
            "required": "Enter the number of RMLO images.",
        },
        widget=StepperInput,
    )
    rcc_count = IntegerField(
        label="RCC",
        classes="nhsuk-input--width-4",
        required=True,
        min_value=0,
        max_value=20,
        initial=1,
        error_messages={
            "min_value": "Number of RCC images must be at least 0.",
            "max_value": "Number of RCC images must be at most 20.",
            "invalid": "Enter a valid number of RCC images.",
            "required": "Enter the number of RCC images.",
        },
        widget=StepperInput,
    )
    right_eklund_count = IntegerField(
        label="Right Eklund",
        hint="Used with breast implants",
        classes="nhsuk-input--width-4",
        required=True,
        min_value=0,
        max_value=20,
        initial=0,
        error_messages={
            "min_value": "Number of Right Eklund images must be at least 0.",
            "max_value": "Number of Right Eklund images must be at most 20.",
            "invalid": "Enter a valid number of Right Eklund images.",
            "required": "Enter the number of Right Eklund images.",
        },
        widget=StepperInput,
    )
    lmlo_count = IntegerField(
        label="LMLO",
        classes="nhsuk-input--width-4",
        required=True,
        min_value=0,
        max_value=20,
        initial=1,
        error_messages={
            "min_value": "Number of LMLO images must be at least 0.",
            "max_value": "Number of LMLO images must be at most 20.",
            "invalid": "Enter a valid number of LMLO images.",
            "required": "Enter the number of LMLO images.",
        },
        widget=StepperInput,
    )
    lcc_count = IntegerField(
        label="LCC",
        classes="nhsuk-input--width-4",
        required=True,
        min_value=0,
        max_value=20,
        initial=1,
        error_messages={
            "min_value": "Number of LCC images must be at least 0.",
            "max_value": "Number of LCC images must be at most 20.",
            "invalid": "Enter a valid number of LCC images.",
            "required": "Enter the number of LCC images.",
        },
        widget=StepperInput,
    )
    left_eklund_count = IntegerField(
        label="Left Eklund",
        hint="Used with breast implants",
        classes="nhsuk-input--width-4",
        required=True,
        min_value=0,
        max_value=20,
        initial=0,
        error_messages={
            "min_value": "Number of Left Eklund images must be at least 0.",
            "max_value": "Number of Left Eklund images must be at most 20.",
            "invalid": "Enter a valid number of Left Eklund images.",
            "required": "Enter the number of Left Eklund images.",
        },
        widget=StepperInput,
    )

    additional_details = CharField(
        hint="Provide information for image readers when reviewing",
        required=False,
        label="Notes for reader (optional)",
        label_classes="nhsuk-label--s",
        widget=Textarea(attrs={"rows": 2}),
        max_words=500,
        error_messages={"max_words": "Notes for reader must be 500 words or less"},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        if (
            self.cleaned_data.get("rmlo_count") == 0
            and self.cleaned_data.get("rcc_count") == 0
            and self.cleaned_data.get("right_eklund_count") == 0
            and self.cleaned_data.get("lmlo_count") == 0
            and self.cleaned_data.get("lcc_count") == 0
            and self.cleaned_data.get("left_eklund_count") == 0
        ):
            self.add_error(None, "Enter at least one image count")

        return cleaned_data

    def save(self, study_service: StudyService):
        return study_service.create(
            additional_details=self.cleaned_data.get("additional_details", ""),
            series_data=[
                self.build_series_dict("MLO", "R", "rmlo_count"),
                self.build_series_dict("CC", "R", "rcc_count"),
                self.build_series_dict("EKLUND", "R", "right_eklund_count"),
                self.build_series_dict("MLO", "L", "lmlo_count"),
                self.build_series_dict("CC", "L", "lcc_count"),
                self.build_series_dict("EKLUND", "L", "left_eklund_count"),
            ],
        )

    def build_series_dict(self, view_position, laterality, count_field_name):
        return {
            "view_position": view_position,
            "laterality": laterality,
            "count": self.cleaned_data.get(count_field_name),
        }

    def mark_workflow_step_complete(self):
        self.appointment.completed_workflow_steps.get_or_create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES,
            defaults={"created_by": self.request.user},
        )
