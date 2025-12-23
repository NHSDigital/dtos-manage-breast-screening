import uuid
from datetime import date, timedelta
from enum import StrEnum

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import OuterRef, Subquery

from ..auth.models import Role
from ..core.models import BaseModel
from ..participants.models import Appointment, Participant


class Provider(BaseModel):
    name = models.TextField()

    def __str__(self):
        return self.name

    @property
    def appointments(self):
        return Appointment.objects.filter(clinic_slot__clinic__setting__provider=self)

    @property
    def clinics(self):
        return Clinic.objects.filter(setting__provider=self)

    @property
    def participants(self):
        return Participant.objects.filter(
            screeningepisode__appointment__clinic_slot__clinic__setting__provider=self
        ).distinct()


class Setting(BaseModel):
    name = models.TextField()
    provider = models.ForeignKey("clinics.Provider", on_delete=models.PROTECT)

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
                return self.last_seven_days()
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

    def last_seven_days(self):
        return self.filter(starts_at__date__gte=(date.today() - timedelta(days=7)))

    def completed(self):
        """
        Completed clinics that started in the past
        """
        from .models import ClinicStatus

        latest_status = (
            ClinicStatus.objects.filter(clinic=OuterRef("pk"))
            .order_by("-created_at")
            .values("state")[:1]
        )

        return (
            self.last_seven_days()
            .filter(starts_at__date__lt=date.today())
            .annotate(latest_status=Subquery(latest_status))
            .filter(latest_status__in=["CLOSED", "CANCELLED"])
            .order_by("-ends_at")
        )

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

    setting = models.ForeignKey("clinics.Setting", on_delete=models.PROTECT)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    type = models.CharField(choices=TYPE_CHOICES, max_length=50)
    risk_type = models.CharField(choices=RISK_TYPE_CHOICES, max_length=50)

    objects = ClinicQuerySet.as_manager()

    @property
    def appointments(self):
        return Appointment.objects.filter(clinic_slot__clinic=self)

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
    def filter_counts(cls, provider_id):
        queryset = cls.objects.filter(setting__provider_id=provider_id)

        return {
            ClinicFilter.ALL: queryset.last_seven_days().count(),
            ClinicFilter.TODAY: queryset.today().count(),
            ClinicFilter.UPCOMING: queryset.upcoming().count(),
            ClinicFilter.COMPLETED: queryset.completed().count(),
        }

    def __str__(self):
        return self.setting.name + " " + self.starts_at.strftime("%Y-%m-%d %H:%M")


class ClinicSlot(BaseModel):
    clinic = models.ForeignKey(
        "clinics.Clinic", on_delete=models.PROTECT, related_name="clinic_slots"
    )
    starts_at = models.DateTimeField()
    duration_in_minutes = models.IntegerField()

    @property
    def provider(self):
        return self.clinic.provider

    def __str__(self):
        return (
            self.clinic.setting.name + " " + self.starts_at.strftime("%Y-%m-%d %H:%M")
        )

    def clean(self):
        if self.starts_at.date() != self.clinic.starts_at.date():
            raise ValidationError(
                "Clinic slot must start on the same date as the clinic"
            )


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
        "clinics.Clinic", on_delete=models.PROTECT, related_name="statuses"
    )


class UserAssignment(BaseModel):
    """
    Join table linking users to providers they are assigned to work with.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assignments"
    )
    provider = models.ForeignKey(
        "clinics.Provider", on_delete=models.PROTECT, related_name="assignments"
    )
    roles = ArrayField(
        base_field=models.CharField(
            max_length=32,
            choices=[
                (Role.CLINICAL.value, Role.CLINICAL.value),
                (Role.ADMINISTRATIVE.value, Role.ADMINISTRATIVE.value),
            ],
        ),
        default=list,
        validators=[MinLengthValidator(1)],
        help_text="Roles granted to the user for this provider.",
    )

    def save(self, *args, **kwargs):
        if self.roles:
            # Remove duplicates and sort
            self.roles = sorted(list(set(self.roles)))
        super().save(*args, **kwargs)

    def make_current(self):
        self.user.current_provider = self.provider

    class Meta:
        unique_together = ["user", "provider"]
        verbose_name = "User provider assignment"
        verbose_name_plural = "User provider assignments"

    def __str__(self):
        return f"{self.user.get_full_name()} → {self.provider.name}"
