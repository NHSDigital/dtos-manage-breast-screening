from datetime import datetime

from django.db.models import F, QuerySet

from manage_breast_screening.notifications.models import (
    MessageStatus,
    MessageStatusChoices,
)


class Failures:
    def query(self, date: datetime = datetime.today()) -> QuerySet:
        starts_at = date.replace(hour=0, minute=0, second=0)
        ends_at = date.replace(hour=23, minute=59, second=59)

        return (
            MessageStatus.objects.filter(
                message__appointment__starts_at__gte=starts_at,
                message__appointment__starts_at__lte=ends_at,
                status=MessageStatusChoices.FAILED.value,
            )
            .values(
                "message__appointment__nhs_number",
                "message__appointment__starts_at",
                "message__appointment__clinic__code",
                "message__appointment__episode_type",
                "status_updated_at",
                "description",
            )
            .annotate(
                nhs_number=F("message__appointment__nhs_number"),
                appointment_date=F("message__appointment__starts_at"),
                clinic_code=F("message__appointment__clinic__code"),
                episode_type=F("message__appointment__episode_type"),
                failure_date=F("status_updated_at"),
                failure_reason=F("description"),
            )
        )
