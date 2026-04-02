from manage_breast_screening.dicom.study_service import StudyService
from manage_breast_screening.mammograms.forms.images.gateway_images_form_fields_mixin import (
    GatewayImagesFormFieldsMixin,
)
from manage_breast_screening.mammograms.services.appointment_services import (
    RecallService,
)
from manage_breast_screening.manual_images.models import (
    StudyCompleteness,
)
from manage_breast_screening.nhsuk_forms.forms import FormWithConditionalFields
from manage_breast_screening.participants.models.appointment import (
    AppointmentWorkflowStepCompletion,
)


class GatewayImageDetailsForm(GatewayImagesFormFieldsMixin, FormWithConditionalFields):
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
                "lccid_count": len(grouped_images["LCCID"]),
                "lmloid_count": len(grouped_images["LMLOID"]),
                "rmlo_count": len(grouped_images["RMLO"]),
                "rcc_count": len(grouped_images["RCC"]),
                "rccid_count": len(grouped_images["RCCID"]),
                "rmloid_count": len(grouped_images["RMLOID"]),
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
