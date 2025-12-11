from django.db.models import TextChoices
from django.forms import Textarea

from manage_breast_screening.nhsuk_forms.fields.char_field import CharField
from manage_breast_screening.nhsuk_forms.fields.choice_fields import (
    ChoiceField,
    MultipleChoiceField,
)
from manage_breast_screening.nhsuk_forms.fields.integer_field import YearField
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields
from manage_breast_screening.participants.models.medical_history.breast_cancer_history_item import (
    BreastCancerHistoryItem,
)


class BreastCancerHistoryItemForm(FormWithConditionalFields):
    class DiagnosisLocationChoices(TextChoices):
        RIGHT_BREAST = "RIGHT_BREAST", "Right breast"
        LEFT_BREAST = "LEFT_BREAST", "Left breast"
        DONT_KNOW = "DONT_KNOW", "Don't know"

        @staticmethod
        def form_value_to_model_field(form_value):
            match form_value:
                case [
                    BreastCancerHistoryItemForm.DiagnosisLocationChoices.RIGHT_BREAST,
                    BreastCancerHistoryItemForm.DiagnosisLocationChoices.LEFT_BREAST,
                ]:
                    return BreastCancerHistoryItem.DiagnosisLocationChoices.BOTH_BREASTS
                case [other]:
                    return BreastCancerHistoryItem.DiagnosisLocationChoices(other)

        @classmethod
        def model_field_to_form_value(cls, model_field):
            match model_field:
                case BreastCancerHistoryItem.DiagnosisLocationChoices.BOTH_BREASTS:
                    return [cls.RIGHT_BREAST, cls.LEFT_BREAST]
                case other:
                    return cls(other)

    diagnosis_location = MultipleChoiceField(
        label="In which breasts was cancer diagnosed?",
        choices=DiagnosisLocationChoices,
        error_messages={"required": "Select which breasts cancer was diagnosed in"},
        exclusive_choices={DiagnosisLocationChoices.DONT_KNOW},
    )
    diagnosis_year = YearField(
        hint="Leave blank if unknown",
        required=False,
        label="Year of diagnosis (optional)",
        label_classes="nhsuk-label--m",
        classes="nhsuk-input--width-4",
    )

    right_breast_procedure = ChoiceField(
        label="Right breast (or axilla)",
        visually_hidden_label_prefix="What procedure have they had in their ",
        visually_hidden_label_suffix="?",
        label_classes="nhsuk-fieldset__legend--s",
        choices=BreastCancerHistoryItem.Procedure,
        error_messages={
            "required": "Select which procedure they have had in the right breast"
        },
    )
    left_breast_procedure = ChoiceField(
        label="Left breast (or axilla)",
        visually_hidden_label_prefix="What procedure have they had in their ",
        visually_hidden_label_suffix="?",
        label_classes="nhsuk-fieldset__legend--s",
        choices=BreastCancerHistoryItem.Procedure,
        error_messages={
            "required": "Select which procedure they have had in the left breast"
        },
    )

    right_breast_other_surgery = MultipleChoiceField(
        label="Right breast (or axilla)",
        visually_hidden_label_prefix="What other surgery have they had in their ",
        visually_hidden_label_suffix="?",
        label_classes="nhsuk-fieldset__legend--s",
        choices=BreastCancerHistoryItem.Surgery,
        exclusive_choices={BreastCancerHistoryItem.Surgery.NO_SURGERY},
        error_messages={
            "required": "Select any other surgery they have had in the right breast"
        },
    )
    left_breast_other_surgery = MultipleChoiceField(
        label="Left breast (or axilla)",
        visually_hidden_label_prefix="What other surgery have they had in their ",
        visually_hidden_label_suffix="?",
        label_classes="nhsuk-fieldset__legend--s",
        choices=BreastCancerHistoryItem.Surgery,
        exclusive_choices={BreastCancerHistoryItem.Surgery.NO_SURGERY},
        error_messages={
            "required": "Select any other surgery they have had in the left breast"
        },
    )

    right_breast_treatment = MultipleChoiceField(
        label="Right breast (or axilla)",
        visually_hidden_label_prefix="What treatment have they had in their ",
        visually_hidden_label_suffix="?",
        label_classes="nhsuk-fieldset__legend--s",
        choices=BreastCancerHistoryItem.Treatment,
        exclusive_choices={BreastCancerHistoryItem.Treatment.NO_RADIOTHERAPY},
        error_messages={
            "required": "Select what treatment they have had in the right breast"
        },
    )
    left_breast_treatment = MultipleChoiceField(
        label="Left breast (or axilla)",
        visually_hidden_label_prefix="What treatment have they had in their ",
        visually_hidden_label_suffix="?",
        label_classes="nhsuk-fieldset__legend--s",
        choices=BreastCancerHistoryItem.Treatment,
        exclusive_choices={BreastCancerHistoryItem.Treatment.NO_RADIOTHERAPY},
        error_messages={
            "required": "Select what treatment they have had in the left breast"
        },
    )

    systemic_treatments = MultipleChoiceField(
        visually_hidden_label_prefix="What treatment have they had that are ",
        visually_hidden_label_suffix="?",
        label="Systemic treatments",
        label_classes="nhsuk-fieldset__legend--s",
        choices=BreastCancerHistoryItem.SystemicTreatment,
        exclusive_choices={
            BreastCancerHistoryItem.SystemicTreatment.NO_SYSTEMIC_TREATMENTS
        },
        error_messages={"required": "Select what systemic treatments they have had"},
    )
    systemic_treatments_other_treatment_details = CharField(
        label="Provide details",
        required=False,
        error_messages={"required": "Provide details of the other systemic treatment"},
    )

    intervention_location = ChoiceField(
        label="Where did surgery and treatment take place?",
        choices=BreastCancerHistoryItem.InterventionLocation,
        error_messages={"required": "Select where surgery and treatment took place"},
    )

    def __init__(self, instance=None, **kwargs):
        self.instance = instance
        self.appointment = instance.appointment if instance else None

        if instance:
            kwargs["initial"] = {
                "diagnosis_location": self.DiagnosisLocationChoices.model_field_to_form_value(
                    instance.diagnosis_location
                ),
                "diagnosis_year": instance.diagnosis_year,
                "right_breast_procedure": instance.right_breast_procedure,
                "left_breast_procedure": instance.left_breast_procedure,
                "right_breast_other_surgery": instance.right_breast_other_surgery,
                "left_breast_other_surgery": instance.left_breast_other_surgery,
                "right_breast_treatment": instance.right_breast_treatment,
                "left_breast_treatment": instance.left_breast_treatment,
                "systemic_treatments": instance.systemic_treatments,
                "systemic_treatments_other_treatment_details": instance.systemic_treatments_other_treatment_details,
                "intervention_location": instance.intervention_location,
                f"intervention_location_details_{instance.intervention_location.lower()}": instance.intervention_location_details,
                "additional_details": instance.additional_details,
            }

        super().__init__(**kwargs)

        self.given_field_value(
            "systemic_treatments", BreastCancerHistoryItem.SystemicTreatment.OTHER
        ).require_field("systemic_treatments_other_treatment_details")

        for location_value in BreastCancerHistoryItem.InterventionLocation:
            self.fields[f"intervention_location_details_{location_value.lower()}"] = (
                CharField(
                    label="Provide details",
                    required=False,
                    error_messages={
                        "required": "Provide details about where the surgery and treatment took place"
                    },
                )
            )

        self.fields["additional_details"] = CharField(
            label="Additional details (optional)",
            label_classes="nhsuk-label--m",
            hint="Include any other relevant information about the treatment",
            required=False,
            widget=Textarea({"rows": 3}),
        )

        self.given_field("intervention_location").require_field_with_prefix(
            "intervention_location_details"
        )

    def model_values(self):
        diagnosis_location = self.DiagnosisLocationChoices.form_value_to_model_field(
            self.cleaned_data.get("diagnosis_location", [])
        )
        intervention_location = self.cleaned_data["intervention_location"]

        return dict(
            diagnosis_location=diagnosis_location,
            diagnosis_year=self.cleaned_data.get("diagnosis_year"),
            right_breast_procedure=self.cleaned_data.get("right_breast_procedure"),
            left_breast_procedure=self.cleaned_data.get("left_breast_procedure"),
            right_breast_other_surgery=self.cleaned_data.get(
                "right_breast_other_surgery"
            ),
            left_breast_other_surgery=self.cleaned_data.get(
                "left_breast_other_surgery"
            ),
            right_breast_treatment=self.cleaned_data.get("right_breast_treatment"),
            left_breast_treatment=self.cleaned_data.get("left_breast_treatment"),
            systemic_treatments=self.cleaned_data.get("systemic_treatments"),
            systemic_treatments_other_treatment_details=self.cleaned_data.get(
                "systemic_treatments_other_treatment_details"
            ),
            intervention_location=intervention_location,
            intervention_location_details=self.cleaned_data.get(
                f"intervention_location_details_{intervention_location.lower()}"
            ),
            additional_details=self.cleaned_data.get("additional_details"),
        )

    def create(self, appointment):
        field_values = self.model_values()

        instance = appointment.breast_cancer_history_items.create(
            **field_values,
        )

        return instance

    def update(self):
        if self.instance is None:
            raise ValueError("Form has no instance")

        field_values = self.model_values()

        for k, v in field_values.items():
            setattr(self.instance, k, v)

        self.instance.save()

        return self.instance
