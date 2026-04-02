from django.db.models import TextChoices
from django.forms.widgets import Textarea

from manage_breast_screening.manual_images.models import (
    IncompleteImagesReason,
)
from manage_breast_screening.nhsuk_forms.fields import (
    BooleanField,
    CharField,
    IntegerField,
)
from manage_breast_screening.nhsuk_forms.fields.choice_fields import (
    ChoiceField,
    MultipleChoiceField,
)
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields


class GatewayImagesFormFieldsMixin(FormWithConditionalFields):
    class RecallChoices(TextChoices):
        TO_BE_RECALLED = "TO_BE_RECALLED", "Yes, record as 'to be recalled'"
        PARTIAL_MAMMOGRAPHY = (
            "PARTIAL_MAMMOGRAPHY",
            "No, record as 'partial mammography'",
        )

    rmlo_count = IntegerField(
        required=True,
        min_value=0,
        max_value=20,
        initial=1,
        error_messages={
            "min_value": "Number of RMLO images must be at least 0",
            "max_value": "Number of RMLO images must be at most 20",
            "invalid": "Enter a valid number of RMLO images",
            "required": "Enter the number of RMLO images",
        },
    )
    rcc_count = IntegerField(
        required=True,
        min_value=0,
        max_value=20,
        initial=1,
        error_messages={
            "min_value": "Number of RCC images must be at least 0",
            "max_value": "Number of RCC images must be at most 20",
            "invalid": "Enter a valid number of RCC images",
            "required": "Enter the number of RCC images",
        },
    )
    rccid_count = IntegerField(
        required=False,
        min_value=0,
        max_value=20,
        initial=0,
        error_messages={
            "min_value": "Number of right craniocaudal Eklund images must be at least 0",
            "max_value": "Number of right craniocaudal Eklund images must be at most 20",
            "invalid": "Enter a valid number of right craniocaudal Eklund images",
            "required": "Enter the number of right craniocaudal Eklund images",
        },
    )
    rmloid_count = IntegerField(
        required=False,
        min_value=0,
        max_value=20,
        initial=0,
        error_messages={
            "min_value": "Number of right mediolateral Eklund images must be at least 0",
            "max_value": "Number of right mediolateral Eklund images must be at most 20",
            "invalid": "Enter a valid number of right mediolateral Eklund images",
            "required": "Enter the number of right mediolateral Eklund images",
        },
    )
    lmlo_count = IntegerField(
        required=True,
        min_value=0,
        max_value=20,
        initial=1,
        error_messages={
            "min_value": "Number of LMLO images must be at least 0",
            "max_value": "Number of LMLO images must be at most 20",
            "invalid": "Enter a valid number of LMLO images",
            "required": "Enter the number of LMLO images",
        },
    )
    lcc_count = IntegerField(
        required=True,
        min_value=0,
        max_value=20,
        initial=1,
        error_messages={
            "min_value": "Number of LCC images must be at least 0",
            "max_value": "Number of LCC images must be at most 20",
            "invalid": "Enter a valid number of LCC images",
            "required": "Enter the number of LCC images",
        },
    )
    lccid_count = IntegerField(
        required=False,
        min_value=0,
        max_value=20,
        initial=0,
        error_messages={
            "min_value": "Number of left craniocaudal Eklund images must be at least 0",
            "max_value": "Number of left craniocaudal Eklund images must be at most 20",
            "invalid": "Enter a valid number of left craniocaudal Eklund images",
            "required": "Enter  of left craniocaudal Eklund images",
        },
    )
    lmloid_count = IntegerField(
        required=False,
        min_value=0,
        max_value=20,
        initial=0,
        error_messages={
            "min_value": "Number of left mediolateral Eklund images must be at least 0",
            "max_value": "Number of left mediolateral Eklund images must be at most 20",
            "invalid": "Enter a valid number of left mediolateral Eklund images",
            "required": "Enter the number of left mediolateral Eklund images",
        },
    )

    imperfect_but_best_possible = BooleanField(
        label="Imperfect, but best possible images",
        hint="Image readers will be advised not to request a technical recall",
        required=False,
    )

    not_all_mammograms_taken = BooleanField(
        label="Not all mammograms taken", required=False
    )

    reasons_incomplete = MultipleChoiceField(
        label="Why could you not take all the images?",
        choices=IncompleteImagesReason,
        required=False,
        label_classes="nhsuk-label--s",
        error_messages={
            "required": "Select a reason why you could not take all the images"
        },
        choice_hints={
            IncompleteImagesReason.UNABLE_TO_SCAN_TISSUE: "For example, large breasts or implanted device"
        },
    )

    reasons_incomplete_details = CharField(
        label="Provide details (optional)",
        required=False,
        label_classes="nhsuk-label--s",
        widget=Textarea(attrs={"rows": 2}),
        max_words=500,
        threshold=0,
        error_messages={"max_words": "Details must be 500 words or less"},
    )

    should_recall = ChoiceField(
        label="Should the participant be recalled to take more images?",
        label_classes="nhsuk-label--s",
        required=False,
        choices=RecallChoices,
        error_messages={
            "required": "Select whether the participant should be recalled to take more images"
        },
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
