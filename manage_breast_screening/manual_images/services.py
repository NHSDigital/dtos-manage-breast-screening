from django.db import transaction

from manage_breast_screening.core.services.auditor import Auditor

from .models import Series, Study


class StudyService:
    def __init__(self, appointment, current_user):
        self.appointment = appointment
        self.current_user = current_user
        self.auditor = Auditor(self.current_user)

    @transaction.atomic
    def create_with_default_series(self):
        self.remove_existing_study_and_series()

        study = Study.objects.create(appointment=self.appointment)
        self.auditor.audit_create(study)

        series_set = [
            Series(study=study, view_position="CC", laterality="L", count=1),
            Series(study=study, view_position="CC", laterality="R", count=1),
            Series(study=study, view_position="MLO", laterality="L", count=1),
            Series(study=study, view_position="MLO", laterality="R", count=1),
        ]
        study.series_set.bulk_create(series_set)
        self.auditor.audit_bulk_create(series_set)

        return study

    @transaction.atomic
    def create(
        self,
        series_data: list[dict],
        **study_kwargs,
    ):
        self.remove_existing_study_and_series()

        study = Study.objects.create(
            appointment=self.appointment,
            **study_kwargs,
        )
        self.auditor.audit_create(study)

        series_set = [
            Series(study=study, **data) for data in series_data if data["count"] != 0
        ]
        study.series_set.bulk_create(series_set)
        self.auditor.audit_bulk_create(series_set)

        return study

    @transaction.atomic
    def remove_existing_study_and_series(self):
        if hasattr(self.appointment, "study"):
            study = self.appointment.study
            series = study.series_set.all()

            self.auditor.audit_bulk_delete(series)
            series.delete()
            self.auditor.audit_delete(study)
            study.delete()
