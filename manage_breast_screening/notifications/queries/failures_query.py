from datetime import datetime
from zoneinfo import ZoneInfo

from django.db.models import F, QuerySet

from manage_breast_screening.notifications.models import (
    MessageStatus,
    MessageStatusChoices,
)


class FailuresQuery:
    COLUMNS = [
        "NHS number",
        "Appointment date",
        "Clinic code",
        "Episode type",
        "Failure date",
        "Failure reason",
    ]

    @staticmethod
    def query(date: datetime = datetime.today()) -> QuerySet:
        tzinfo = ZoneInfo("Europe/London")
        starts_at = date.replace(hour=0, minute=0, second=0, tzinfo=tzinfo)
        ends_at = date.replace(hour=23, minute=59, second=59, tzinfo=tzinfo)

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

    @classmethod
    def sql(cls, date: datetime = datetime.today()) -> str:
        return str(cls.query(date).query)

    @classmethod
    def columns(cls) -> list:
        return cls.COLUMNS
