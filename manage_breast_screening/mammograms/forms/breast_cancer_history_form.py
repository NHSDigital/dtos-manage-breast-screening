from django.db.models import TextChoices
from django.forms import Textarea

from manage_breast_screening.nhsuk_forms.fields.char_field import CharField
from manage_breast_screening.nhsuk_forms.fields.choice_fields import (
    ChoiceField,
    MultipleChoiceField,
)
from manage_breast_screening.nhsuk_forms.fields.integer_field import IntegerField
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields
from manage_breast_screening.participants.models.breast_cancer_history_item import (
    BreastCancerHistoryItem,
)


class BreastCancerHistoryForm(FormWithConditionalFields):
    class DiagnosisLocationChoices(TextChoices):
        RIGHT_BREAST = "RIGHT_BREAST", "Right breast"
        LEFT_BREAST = "LEFT_BREAST", "Left breast"
        DONT_KNOW = "DONT_KNOW", "Don't know"

    diagnosis_location = MultipleChoiceField(
        label="In which breasts was cancer diagnosed?", choices=DiagnosisLocationChoices
    )
    # todo: constrain min/max
    diagnosis_year = IntegerField(
        label="Year of diagnosis (optional)",
        label_classes="nhsuk-label--m",
        classes="nhsuk-input--width-4",
        hint="Leave blank if unknown",
    )

    left_breast_procedure = ChoiceField(
        label="Left breast (or axilla)",
        visually_hidden_label_prefix="What procedure have they had in their ",
        visually_hidden_label_suffix="?",
        label_classes="nhsuk-fieldset__legend--s",
        choices=BreastCancerHistoryItem.Procedure,
    )
    right_breast_procedure = ChoiceField(
        label="Right breast (or axilla)",
        visually_hidden_label_prefix="What procedure have they had in their ",
        visually_hidden_label_suffix="?",
        label_classes="nhsuk-fieldset__legend--s",
        choices=BreastCancerHistoryItem.Procedure,
    )

    left_breast_other_surgery = MultipleChoiceField(
        label="Left breast (or axilla)",
        visually_hidden_label_prefix="What other surgery have they had in their ",
        visually_hidden_label_suffix="?",
        label_classes="nhsuk-fieldset__legend--s",
        choices=BreastCancerHistoryItem.Surgery,
    )
    right_breast_other_surgery = MultipleChoiceField(
        label="Right breast (or axilla)",
        visually_hidden_label_prefix="What other surgery have they had in their ",
        visually_hidden_label_suffix="?",
        label_classes="nhsuk-fieldset__legend--s",
        choices=BreastCancerHistoryItem.Surgery,
    )

    left_breast_treatment = MultipleChoiceField(
        label="Left breast (or axilla)",
        visually_hidden_label_prefix="What treatment have they had in their ",
        visually_hidden_label_suffix="?",
        choices=BreastCancerHistoryItem.Treatment,
    )
    right_breast_treatment = MultipleChoiceField(
        label="Right breast (or axilla)",
        visually_hidden_label_prefix="What treatment have they had in their ",
        visually_hidden_label_suffix="?",
        choices=BreastCancerHistoryItem.Treatment,
    )

    systemic_treatments = ChoiceField(
        visually_hidden_label_prefix="What treatment have they had that are ",
        visually_hidden_label_suffix="?",
        label="Systemic treatments",
        choices=BreastCancerHistoryItem.SystemicTreatment,
    )
    systemic_treatment_other_treatment_details = CharField(
        label="Provide details", required=False
    )

    intervention_location = ChoiceField(
        label="Where did surgery and treatment take place?",
        choices=BreastCancerHistoryItem.InterventionLocation,
    )
    intervention_location_details = CharField(label="Provide details", required=False)

    additional_details = CharField(
        label="Additional details (optional)", required=False, widget=Textarea
    )
