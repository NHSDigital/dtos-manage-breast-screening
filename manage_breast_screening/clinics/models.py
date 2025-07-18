import uuid
from datetime import date
from enum import StrEnum

from django.db import models

from ..core.models import BaseModel


class Provider(BaseModel):
    name = models.TextField()

    def __str__(self):
        return self.name


class Setting(BaseModel):
    name = models.TextField()
    provider = models.ForeignKey(Provider, on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class ClinicFilter(StrEnum):
    TODAY = "today"
    UPCOMING = "upcoming"
    COMPLETED = "completed"
    ALL = "all"


class ClinicQuerySet(models.QuerySet):
    def by_filter(self, filter: str):
        match filter:
            case ClinicFilter.TODAY:
                return self.today()
            case ClinicFilter.UPCOMING:
                return self.upcoming()
            case ClinicFilter.COMPLETED:
                return self.completed()
            case ClinicFilter.ALL:
                return self
            case _:
                raise ValueError(filter)

    def today(self):
        """
        Clinics that start today
        """
        return self.filter(starts_at__date=date.today())

    def upcoming(self):
        """
        Clinics that start tomorrow or later
        """
        return self.filter(starts_at__date__gt=date.today())

    def completed(self):
        """
        Clinics that started in the past
        (note: we may want to also consider the clinic state when splitting things out by date)
        """
        return self.filter(starts_at__date__lt=date.today())

    def with_statuses(self):
        return self.prefetch_related("statuses")


class Clinic(BaseModel):
    class RiskType:
        MIXED_RISK = "MIXED_RISK"
        ROUTINE_RISK = "ROUTINE_RISK"
        MOBILE = "MOBILE"

    class Type:
        ASSESSMENT = "ASSESSMENT"
        SCREENING = "SCREENING"

    class TimeOfDay:
        ALL_DAY = "all day"
        MORNING = "morning"
        AFTERNOON = "afternoon"

    RISK_TYPE_CHOICES = {
        RiskType.MIXED_RISK: "Mixed risk",
        RiskType.ROUTINE_RISK: "Routine risk",
        RiskType.MOBILE: "Mobile screening",
    }

    TYPE_CHOICES = {Type.ASSESSMENT: "Assessment", Type.SCREENING: "Screening"}

    setting = models.ForeignKey(Setting, on_delete=models.PROTECT)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    type = models.CharField(choices=TYPE_CHOICES, max_length=50)
    risk_type = models.CharField(choices=RISK_TYPE_CHOICES, max_length=50)

    objects = ClinicQuerySet.as_manager()

    @property
    def provider(self):
        return self.setting.provider

    @property
    def current_status(self):
        return self.statuses.order_by("-created_at").first()

    def session_type(self):
        start_hour = self.starts_at.hour
        duration = (self.ends_at - self.starts_at).seconds
        if duration > 6 * 60 * 60:
            return self.TimeOfDay.ALL_DAY

        if start_hour < 12:
            return self.TimeOfDay.MORNING

        return self.TimeOfDay.AFTERNOON

    def time_range(self):
        return {"start_time": self.starts_at, "end_time": self.ends_at}

    @classmethod
    def filter_counts(cls):
        return {
            ClinicFilter.ALL: cls.objects.count(),
            ClinicFilter.TODAY: cls.objects.today().count(),
            ClinicFilter.UPCOMING: cls.objects.upcoming().count(),
            ClinicFilter.COMPLETED: cls.objects.completed().count(),
        }


class ClinicSlot(BaseModel):
    clinic = models.ForeignKey(
        Clinic, on_delete=models.PROTECT, related_name="clinic_slots"
    )
    starts_at = models.DateTimeField()
    duration_in_minutes = models.IntegerField()

    @property
    def provider(self):
        return self.clinic.provider


class ClinicStatus(models.Model):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

    STATE_CHOICES = [
        (SCHEDULED, "Scheduled"),
        (IN_PROGRESS, "In progress"),
        (CLOSED, "Closed"),
        (CANCELLED, "Cancelled"),
    ]

    class Meta:
        ordering = ["-created_at"]

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    state = models.CharField(choices=STATE_CHOICES, max_length=50)
    clinic = models.ForeignKey(
        Clinic, on_delete=models.PROTECT, related_name="statuses"
    )
