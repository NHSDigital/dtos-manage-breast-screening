from datetime import date
from enum import StrEnum

from django.db import models


class BaseModel(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Provider(BaseModel):
    name = models.TextField()

    def __str__(self):
        return f"Provider: {self.name}"


class Setting(BaseModel):
    name = models.TextField()
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)

    def __str__(self):
        return f"Setting: {self.name}"


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


class Clinic(BaseModel):
    class State:
        SCHEDULED = "SCHEDULED"
        IN_PROGRESS = "IN_PROGRESS"
        CLOSED = "CLOSED"
        CANCELLED = "CANCELLED"

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

    STATE_CHOICES = {
        State.SCHEDULED: "Scheduled",
        State.IN_PROGRESS: "In progress",
        State.CLOSED: "Closed",
        State.CANCELLED: "Cancelled",
    }

    RISK_TYPE_CHOICES = {
        RiskType.MIXED_RISK: "Mixed risk",
        RiskType.ROUTINE_RISK: "Routine risk",
        RiskType.MOBILE: "Mobile screening",
    }

    TYPE_CHOICES = {Type.ASSESSMENT: "Assessment", Type.SCREENING: "Screening"}

    setting = models.ForeignKey(Setting, on_delete=models.CASCADE)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    type = models.CharField(choices=TYPE_CHOICES, max_length=50)
    risk_type = models.CharField(choices=RISK_TYPE_CHOICES, max_length=50)
    state = models.CharField(choices=STATE_CHOICES, max_length=50)

    objects = ClinicQuerySet.as_manager()

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
        Clinic, on_delete=models.CASCADE, related_name="clinic_slots"
    )
    starts_at = models.DateTimeField()
    duration_in_minutes = models.IntegerField()


class ScreeningEpisode(BaseModel):
    participant = models.ForeignKey(
        "participants.Participant", on_delete=models.CASCADE
    )

    def screening_history(self):
        """
        Return all previous screening episodes, excluding this one, prefetching
        their appointment details as well.
        """
        return (
            ScreeningEpisode.objects.prefetch_related(
                "appointment_set__clinic_slot__clinic__setting__provider"
            )
            .filter(participant__pk=self.participant.pk, pk__lt=self.pk)
            .order_by("-pk")
        )

    def previous(self) -> "ScreeningEpisode | None":
        """
        Return the last known screening episode
        """
        try:
            return self.screening_history()[0]
        except IndexError:
            return None


class Appointment(BaseModel):
    class Status:
        CONFIRMED = "CONFIRMED"
        CANCELLED = "CANCELLED"
        DID_NOT_ATTEND = "DID_NOT_ATTEND"
        CHECKED_IN = "CHECKED_IN"
        SCREENED = "SCREENED"
        PARTIALLY_SCREENED = "PARTIALLY_SCREENED"
        ATTENDED_NOT_SCREENED = "ATTENDED_NOT_SCREENED"

    STATUS_CHOICES = {
        Status.CONFIRMED: "Confirmed",
        Status.CANCELLED: "Cancelled",
        Status.DID_NOT_ATTEND: "Did not attend",
        Status.CHECKED_IN: "Checked in",
        Status.SCREENED: "Screened",
        Status.PARTIALLY_SCREENED: "Partially screened",
        Status.ATTENDED_NOT_SCREENED: "Attended not screened",
    }

    screening_episode = models.ForeignKey(ScreeningEpisode, on_delete=models.CASCADE)
    clinic_slot = models.ForeignKey(ClinicSlot, on_delete=models.CASCADE)
    status = models.CharField(
        choices=STATUS_CHOICES, max_length=50, default=Status.CONFIRMED
    )
    reinvite = models.BooleanField(default=False)
    stopped_reasons = models.JSONField(null=True, blank=True)
