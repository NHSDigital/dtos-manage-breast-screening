from django.db.models import TextChoices
from django.forms.widgets import Textarea

from manage_breast_screening.dicom.study_service import StudyService
from manage_breast_screening.mammograms.services.appointment_services import (
    RecallService,
)
from manage_breast_screening.manual_images.models import (
    IncompleteImagesReason,
    StudyCompleteness,
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
from manage_breast_screening.participants.models.appointment import (
    AppointmentWorkflowStepCompletion,
)


class GatewayImageDetailsForm(FormWithConditionalFields):
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

    def __init__(self, *args, instance=None, **kwargs):
        if instance:
            match instance.completeness:
                case StudyCompleteness.INCOMPLETE:
                    should_recall = self.RecallChoices.TO_BE_RECALLED
                case StudyCompleteness.PARTIAL:
                    should_recall = self.RecallChoices.PARTIAL_MAMMOGRAPHY
                case _:
                    should_recall = None

            images = instance.images().all()
            grouped_images = StudyService.images_by_laterality_and_view(images)

            kwargs["initial"] = {
                "imperfect_but_best_possible": instance.imperfect_but_best_possible,
                "not_all_mammograms_taken": bool(instance.reasons_incomplete),
                "reasons_incomplete": instance.reasons_incomplete,
                "reasons_incomplete_details": instance.reasons_incomplete_details,
                "should_recall": should_recall,
                "additional_details": instance.additional_details,
                "lmlo_count": len(grouped_images["LMLO"]),
                "lcc_count": len(grouped_images["LCC"]),
                "rmlo_count": len(grouped_images["RMLO"]),
                "rcc_count": len(grouped_images["RCC"]),
            }

        super().__init__(*args, **kwargs)

        self.given_field_value("not_all_mammograms_taken", True).require_field(
            "reasons_incomplete"
        )
        self.given_field_value("not_all_mammograms_taken", True).require_field(
            "should_recall"
        )

    def clean(self):
        cleaned_data = super().clean()
        not_all_mammograms_taken = self.cleaned_data.get("not_all_mammograms_taken")

        if (
            self.cleaned_data.get("rmlo_count") == 0
            and self.cleaned_data.get("rcc_count") == 0
            and self.cleaned_data.get("right_eklund_count") == 0
            and self.cleaned_data.get("lmlo_count") == 0
            and self.cleaned_data.get("lcc_count") == 0
            and self.cleaned_data.get("left_eklund_count") == 0
        ):
            self.add_error(None, "Enter at least one image count")
        elif (
            any(
                self.cleaned_data.get(f"{view}_count") == 0
                for view in ("rmlo", "rcc", "lmlo", "lcc")
            )
            and not not_all_mammograms_taken
        ):
            self.add_error(
                "not_all_mammograms_taken",
                'Select "Not all mammograms taken" if a CC or MLO view is missing',
            )

        return cleaned_data

    def completeness(self):
        match self.cleaned_data.get("should_recall"):
            case self.RecallChoices.TO_BE_RECALLED:
                return StudyCompleteness.INCOMPLETE
            case self.RecallChoices.PARTIAL_MAMMOGRAPHY:
                return StudyCompleteness.PARTIAL
            case _:
                return StudyCompleteness.COMPLETE

    def save(self, study_service: StudyService, recall_service: RecallService):
        study = study_service.save(
            additional_details=self.cleaned_data.get("additional_details", ""),
            imperfect_but_best_possible=self.cleaned_data.get(
                "imperfect_but_best_possible", False
            ),
            reasons_incomplete=self.cleaned_data.get("reasons_incomplete", []),
            reasons_incomplete_details=self.cleaned_data.get(
                "reasons_incomplete_details", ""
            ),
            completeness=self.completeness(),
        )

        if self.cleaned_data["should_recall"] == self.RecallChoices.TO_BE_RECALLED:
            recall_service.reinvite()

        return study

    def mark_workflow_step_complete(self):
        self.appointment.completed_workflow_steps.get_or_create(
            step_name=AppointmentWorkflowStepCompletion.StepNames.TAKE_IMAGES,
            defaults={"created_by": self.request.user},
        )
