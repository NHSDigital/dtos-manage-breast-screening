from django import forms
from django.forms import Form
from django.forms.widgets import Textarea

from manage_breast_screening.nhsuk_forms.fields import (
    BooleanField,
    CharField,
    YearField,
)
from manage_breast_screening.nhsuk_forms.fields.choice_fields import MultipleChoiceField
from manage_breast_screening.participants.models.medical_history.breast_augmentation_history_item import (
    BreastAugmentationHistoryItem,
)


class BreastAugmentationHistoryItemForm(Form):
    right_breast_procedures = MultipleChoiceField(
        label="Right breast",
        label_classes="nhsuk-fieldset__legend--s",
        visually_hidden_label_prefix="What procedure have they had in their ",
        visually_hidden_label_suffix="?",
        choices=BreastAugmentationHistoryItem.Procedure,
        error_messages={
            "required": "Select procedures for the right breast",
        },
        exclusive_choices={"NO_PROCEDURES"},
    )
    left_breast_procedures = MultipleChoiceField(
        label="Left breast",
        label_classes="nhsuk-fieldset__legend--s",
        visually_hidden_label_prefix="What procedure have they had in their ",
        visually_hidden_label_suffix="?",
        choices=BreastAugmentationHistoryItem.Procedure,
        error_messages={
            "required": "Select procedures for the left breast",
        },
        exclusive_choices={"NO_PROCEDURES"},
    )
    procedure_year = YearField(
        hint="Leave blank if unknown",
        required=False,
        label="Year of procedure (optional)",
        label_classes="nhsuk-label--m",
        classes="nhsuk-input--width-4",
    )
    implants_have_been_removed = BooleanField(
        required=False,
        label="Implants have been removed",
        classes="app-checkboxes",
    )
    removal_year = YearField(
        required=False,
        label="Year removed (if available)",
        classes="nhsuk-input--width-4",
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

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance

        if instance:
            kwargs["initial"] = {
                "right_breast_procedures": instance.right_breast_procedures,
                "left_breast_procedures": instance.left_breast_procedures,
                "procedure_year": instance.procedure_year,
                "implants_have_been_removed": instance.implants_have_been_removed,
                "removal_year": instance.removal_year,
                "additional_details": instance.additional_details,
            }

        super().__init__(*args, **kwargs)

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

    def create(self, appointment):
        field_values = self.model_values()
        breast_augmentation_history = (
            appointment.breast_augmentation_history_items.create(
                appointment=appointment,
                **field_values,
            )
        )

        return breast_augmentation_history

    def update(self):
        if self.instance is None:
            raise ValueError("Form has no instance")

        # fmt: off
        self.instance.right_breast_procedures = self.cleaned_data["right_breast_procedures"]
        self.instance.left_breast_procedures = self.cleaned_data["left_breast_procedures"]
        self.instance.procedure_year = self.cleaned_data["procedure_year"]
        self.instance.implants_have_been_removed = self.cleaned_data["implants_have_been_removed"]
        self.instance.removal_year = self.cleaned_data["removal_year"]
        self.instance.additional_details = self.cleaned_data["additional_details"]
        # fmt: on

        self.instance.save()

        return self.instance
