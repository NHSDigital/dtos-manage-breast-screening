import uuid
from datetime import date
from logging import getLogger

from django.db import models
from django.db.models import OuterRef, Subquery

from manage_breast_screening.users.models import User

from ...core.models import BaseModel
from .screening_episode import ScreeningEpisode

logger = getLogger(__name__)


class AppointmentQuerySet(models.QuerySet):
    def in_status(self, *statuses):
        return self.filter(
            statuses=Subquery(
                AppointmentStatus.objects.filter(
                    appointment=OuterRef("pk"),
                    state__in=statuses,
                )
                .values("pk")
                .order_by("-created_at")[:1]
            )
        )

    def remaining(self):
        return self.in_status(
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.CHECKED_IN,
            AppointmentStatus.IN_PROGRESS,
        )

    def checked_in(self):
        return self.in_status(AppointmentStatus.CHECKED_IN)

    def in_progress(self):
        return self.in_status(AppointmentStatus.IN_PROGRESS)

    def complete(self):
        return self.in_status(
            AppointmentStatus.CANCELLED,
            AppointmentStatus.DID_NOT_ATTEND,
            AppointmentStatus.SCREENED,
            AppointmentStatus.PARTIALLY_SCREENED,
            AppointmentStatus.ATTENDED_NOT_SCREENED,
        )

    def upcoming(self):
        return self.filter(clinic_slot__starts_at__date__gte=date.today())

    def past(self):
        return self.filter(clinic_slot__starts_at__date__lt=date.today())

    def for_filter(self, filter):
        match filter:
            case "remaining":
                return self.remaining()
            case "checked_in":
                return self.checked_in()
            case "in_progress":
                return self.in_progress()
            case "complete":
                return self.complete()
            case "all":
                return self
            case _:
                raise ValueError(filter)

    def order_by_starts_at(self, desc=False):
        return self.order_by(
            "-clinic_slot__starts_at" if desc else "clinic_slot__starts_at"
        )


class Appointment(BaseModel):
    objects = AppointmentQuerySet.as_manager()

    screening_episode = models.ForeignKey(ScreeningEpisode, on_delete=models.PROTECT)
    clinic_slot = models.ForeignKey(
        "clinics.ClinicSlot",
        on_delete=models.PROTECT,
    )
    reinvite = models.BooleanField(default=False)
    stopped_reasons = models.JSONField(null=True, blank=True)

    @classmethod
    def filter_counts_for_clinic(cls, clinic):
        counts = {}
        for filter in ["remaining", "checked_in", "in_progress", "complete", "all"]:
            counts[filter] = clinic.appointments.for_filter(filter).count()
        return counts

    @property
    def provider(self):
        return self.clinic_slot.provider

    @property
    def participant(self):
        return self.screening_episode.participant

    @property
    def current_status(self) -> "AppointmentStatus":
        """
        Fetch the most recent status associated with this appointment.
        If there are no statuses for any reason, assume the default one.
        """
        # avoid `first()` here so that `statuses` can be prefetched
        # when fetching many appointments
        statuses = list(self.statuses.order_by("-created_at").all())

        if not statuses:
            status = AppointmentStatus()
            logger.info(
                f"Appointment {self.pk} has no statuses. Assuming {status.state}"
            )
            return status

        return statuses[0]

    @property
    def active(self):
        return self.current_status.active


class AppointmentStatus(models.Model):
    CONFIRMED = "CONFIRMED"
    CHECKED_IN = "CHECKED_IN"
    IN_PROGRESS = "IN_PROGRESS"
    CANCELLED = "CANCELLED"
    DID_NOT_ATTEND = "DID_NOT_ATTEND"
    SCREENED = "SCREENED"
    PARTIALLY_SCREENED = "PARTIALLY_SCREENED"
    ATTENDED_NOT_SCREENED = "ATTENDED_NOT_SCREENED"

    STATUS_CHOICES = {
        CONFIRMED: "Confirmed",
        CHECKED_IN: "Checked in",
        IN_PROGRESS: "In progress",
        CANCELLED: "Cancelled",
        DID_NOT_ATTEND: "Did not attend",
        SCREENED: "Screened",
        PARTIALLY_SCREENED: "Partially screened",
        ATTENDED_NOT_SCREENED: "Attended not screened",
    }
    state = models.CharField(choices=STATUS_CHOICES, max_length=50, default=CONFIRMED)

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    appointment = models.ForeignKey(
        "participants.Appointment", on_delete=models.PROTECT, related_name="statuses"
    )
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True)

    class Meta:
        ordering = ["-created_at"]

        # Note: this is only valid as long as we can't undo a state transition.
        # https://nhsd-jira.digital.nhs.uk/browse/DTOSS-11522
        unique_together = ("appointment", "state")

    @property
    def active(self):
        """
        Is this state one of the active, non-final states?
        """
        return self.state in [self.CONFIRMED, self.CHECKED_IN, self.IN_PROGRESS]

    def __str__(self):
        return self.state
