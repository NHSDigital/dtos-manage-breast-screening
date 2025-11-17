import datetime

from django import forms
from django.forms import Form
from django.forms.widgets import Textarea

from manage_breast_screening.core.services.auditor import Auditor
from manage_breast_screening.nhsuk_forms.fields import (
    BooleanField,
    CharField,
    IntegerField,
)
from manage_breast_screening.nhsuk_forms.fields.choice_fields import (
    MultipleChoiceField,
)
from manage_breast_screening.participants.models.breast_augmentation_history_item import (
    BreastAugmentationHistoryItem,
)


class BreastAugmentationHistoryForm(Form):
    right_breast_procedures = MultipleChoiceField(
        label="Right breast",
        label_classes="nhsuk-fieldset__legend--s",
        choices=BreastAugmentationHistoryItem.Procedure,
        error_messages={
            "required": "Select procedures for the right breast",
        },
        exclusive_choices={"NO_PROCEDURES"},
    )
    left_breast_procedures = MultipleChoiceField(
        label="Left breast",
        label_classes="nhsuk-fieldset__legend--s",
        choices=BreastAugmentationHistoryItem.Procedure,
        error_messages={
            "required": "Select procedures for the left breast",
        },
        exclusive_choices={"NO_PROCEDURES"},
    )
    implants_have_been_removed = BooleanField(
        required=False,
        label="Implants have been removed",
        classes="app-checkboxes",
    )
    additional_details = CharField(
        hint="Include any other relevant information about the procedure",
        required=False,
        label="Additional details (optional)",
        label_classes="nhsuk-label--m",
        widget=Textarea(attrs={"rows": 4}),
        max_words=500,
        error_messages={"max_words": "Additional details must be 500 words or less"},
    )

    def __init__(self, *args, participant, **kwargs):
        super().__init__(*args, **kwargs)

        # if entered, years should be between 80 years ago and this year
        max_year = datetime.date.today().year
        min_year = max_year - 80
        year_outside_range_error_message = (
            f"Year should be between {min_year} and {max_year}."
        )
        year_invalid_format_error_message = "Enter year as a number."

        self.fields["procedure_year"] = IntegerField(
            hint="Leave blank if unknown",
            required=False,
            label="Year of procedure (optional)",
            label_classes="nhsuk-label--m",
            classes="nhsuk-input--width-4",
            min_value=min_year,
            max_value=max_year,
            error_messages={
                "min_value": year_outside_range_error_message,
                "max_value": year_outside_range_error_message,
                "invalid": year_invalid_format_error_message,
            },
        )
        self.fields["removal_year"] = IntegerField(
            required=False,
            label="Year removed (if available)",
            classes="nhsuk-input--width-4",
            min_value=min_year,
            max_value=max_year,
            error_messages={
                "min_value": year_outside_range_error_message,
                "max_value": year_outside_range_error_message,
                "invalid": year_invalid_format_error_message,
            },
        )

    def model_values(self):
        return dict(
            left_breast_procedures=self.cleaned_data.get("left_breast_procedures", []),
            right_breast_procedures=self.cleaned_data.get(
                "right_breast_procedures", []
            ),
            implants_have_been_removed=self.cleaned_data.get(
                "implants_have_been_removed"
            ),
            removal_year=self.cleaned_data.get("removal_year"),
            procedure_year=self.cleaned_data.get("procedure_year", ""),
            additional_details=self.cleaned_data.get("additional_details", ""),
        )

    def create(self, appointment, request):
        auditor = Auditor.from_request(request)
        field_values = self.model_values()
        breast_augmentation_history = (
            appointment.breast_augmentation_history_items.create(
                appointment=appointment,
                **field_values,
            )
        )
        auditor.audit_create(breast_augmentation_history)

        return breast_augmentation_history

    def full_clean(self):
        # if a removal_year is provided then remove it if implants_have_been_removed is False
        if self.data.get("removal_year") and not self.data.get(
            "implants_have_been_removed"
        ):
            # makes QueryDict mutable
            self.data = self.data.copy()
            self.data["removal_year"] = None
            if hasattr(self.data, "_mutable"):
                self.data._mutable = False

        super().full_clean()

    def clean(self):
        cleaned_data = super().clean()
        procedure_year = cleaned_data.get("procedure_year")
        removal_year = cleaned_data.get("removal_year")

        if procedure_year and removal_year and procedure_year > removal_year:
            self.add_error(
                "removal_year",
                forms.ValidationError(
                    message="Year removed cannot be before year of procedure",
                    code="required",
                ),
            )

        return cleaned_data
