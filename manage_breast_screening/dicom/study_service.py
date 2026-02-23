from django.db import transaction

from manage_breast_screening.core.services.auditor import Auditor

from .models import Study, Image


class StudyService:
    def __init__(self, appointment, current_user):
        self.appointment = appointment
        self.current_user = current_user
        self.auditor = Auditor(self.current_user)

    @transaction.atomic
    def save(
        self,
        **study_kwargs,
    ) -> Study | None:
        """
        Save additional details to the Study associated with the appointment's GatewayAction.
        Returns the updated Study, or None if no Study is found.
        """
        study = Study.for_appointment(self.appointment)

        if not study:
            return None

        study.additional_details = study_kwargs.get("additional_details", "")
        study.imperfect_but_best_possible = study_kwargs.get(
            "imperfect_but_best_possible", False
        )
        study.reasons_incomplete = study_kwargs.get("reasons_incomplete", [])
        study.reasons_incomplete_details = study_kwargs.get(
            "reasons_incomplete_details", ""
        )
        study.completeness = study_kwargs.get("completeness", "")

        study.save(
            update_fields=[
                "additional_details",
                "imperfect_but_best_possible",
                "reasons_incomplete",
                "reasons_incomplete_details",
                "completeness",
            ]
        )
        self.auditor.audit_update(study)

        return study

    @staticmethod
    def images_by_laterality_and_view(
        images: list["Image"],
    ) -> dict[str, list["Image"]]:
        grouped_images = {"LCC": [], "LMLO": [], "RCC": [], "RMLO": []}
        for image in images:
            laterality_and_view = image.laterality_and_view()
            if laterality_and_view in grouped_images:
                grouped_images[laterality_and_view].append(image)
        return grouped_images

    @staticmethod
    def image_counts_by_laterality_and_view(
        images: list["Image"],
    ) -> dict[str, int]:
        counts = {"LCC": 0, "LMLO": 0, "RCC": 0, "RMLO": 0}
        for image in images:
            laterality_and_view = image.laterality_and_view()
            if laterality_and_view in counts:
                counts[laterality_and_view] += 1
        return counts
