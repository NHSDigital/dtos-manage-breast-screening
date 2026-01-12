import uuid
from datetime import date
from logging import getLogger

from django.db import models
from django.db.models import OuterRef, Prefetch, Subquery

from manage_breast_screening.users.models import User

from ...core.models import BaseModel
from .screening_episode import ScreeningEpisode

logger = getLogger(__name__)


class AppointmentQuerySet(models.QuerySet):
    def in_status(self, *statuses):
        # Get the most recent status name for each appointment
        most_recent_status = (
            AppointmentStatus.objects.filter(appointment=OuterRef("pk"))
            .order_by("-created_at")
            .values("name")[:1]
        )

        # Filter appointments where the most recent status name is in the provided list
        return self.annotate(current_status_name=Subquery(most_recent_status)).filter(
            current_status_name__in=statuses
        )

    def remaining(self):
        return self.in_status(
            *AppointmentStatus.YET_TO_BEGIN_STATUSES,
            *AppointmentStatus.IN_PROGRESS_STATUSES,
        )

    def checked_in(self):
        return self.in_status(AppointmentStatus.CHECKED_IN)

    def in_progress(self):
        return self.in_status(*AppointmentStatus.IN_PROGRESS_STATUSES)

    def for_participant(self, participant_id):
        return self.filter(screening_episode__participant_id=participant_id)

    def complete(self):
        return self.in_status(*AppointmentStatus.FINAL_STATUSES)

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

    def prefetch_current_status(self):
        return self.prefetch_related(
            Prefetch(
                "statuses",
                queryset=AppointmentStatus.objects.select_related(
                    "created_by"
                ).order_by("-created_at")[:1],  # Limit to most recent
                to_attr="_prefetched_current_status",  # Store in named attribute
            )
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
        Check if a prefetched status is available, otherwise do a query.
        If there are no statuses for any reason, assume the default one.
        """
        prefetched_current_status = getattr(self, "_prefetched_current_status", None)
        if prefetched_current_status:
            return prefetched_current_status[0]

        statuses = list(self.statuses.order_by("-created_at").all())
        if not statuses:
            status = AppointmentStatus()
            logger.info(
                f"Appointment {self.pk} has no statuses. Assuming {status.name}"
            )
            return status

        return statuses[0]

    @property
    def active(self):
        return self.current_status.active


class AppointmentStatus(models.Model):
    CONFIRMED = "CONFIRMED"
    CHECKED_IN = "CHECKED_IN"
    STARTED = "STARTED"
    IDENTITY_CONFIRMED = "IDENTITY_CONFIRMED"
    MEDICAL_INFORMATION_REVIEWED = "MEDICAL_INFORMATION_REVIEWED"
    IMAGES_TAKEN = "IMAGES_TAKEN"
    CANCELLED = "CANCELLED"
    DID_NOT_ATTEND = "DID_NOT_ATTEND"
    SCREENED = "SCREENED"
    PARTIALLY_SCREENED = "PARTIALLY_SCREENED"
    ATTENDED_NOT_SCREENED = "ATTENDED_NOT_SCREENED"

    STATUS_CHOICES = {
        CONFIRMED: "Confirmed",
        CHECKED_IN: "Checked in",
        STARTED: "Started",
        IDENTITY_CONFIRMED: "Identity confirmed",
        MEDICAL_INFORMATION_REVIEWED: "Medical information reviewed",
        IMAGES_TAKEN: "Images taken",
        CANCELLED: "Cancelled",
        DID_NOT_ATTEND: "Did not attend",
        SCREENED: "Screened",
        PARTIALLY_SCREENED: "Partially screened",
        ATTENDED_NOT_SCREENED: "Attended not screened",
    }

    YET_TO_BEGIN_STATUSES = [
        CONFIRMED,
        CHECKED_IN,
    ]

    IN_PROGRESS_STATUSES = [
        STARTED,
        IDENTITY_CONFIRMED,
        MEDICAL_INFORMATION_REVIEWED,
        IMAGES_TAKEN,
    ]

    FINAL_STATUSES = [
        CANCELLED,
        DID_NOT_ATTEND,
        SCREENED,
        PARTIALLY_SCREENED,
        ATTENDED_NOT_SCREENED,
    ]

    name = models.CharField(choices=STATUS_CHOICES, max_length=50, default=CONFIRMED)

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    appointment = models.ForeignKey(
        "participants.Appointment", on_delete=models.PROTECT, related_name="statuses"
    )
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True)

    class Meta:
        ordering = ["-created_at"]

        # Note: this is only valid as long as we can't undo a status transition.
        # https://nhsd-jira.digital.nhs.uk/browse/DTOSS-11522
        unique_together = ("appointment", "name")

    @property
    def active(self):
        """
        Is this status one of the active, non-final statuses?
        """
        return self.is_in_progress() or self.is_yet_to_begin()

    def is_yet_to_begin(self):
        return self.name in self.YET_TO_BEGIN_STATUSES

    def is_in_progress(self):
        return self.name in self.IN_PROGRESS_STATUSES

    def is_final_status(self):
        return self.name in self.FINAL_STATUSES

    def __str__(self):
        return self.name


class AppointmentNote(BaseModel):
    appointment = models.OneToOneField(
        "participants.Appointment",
        on_delete=models.PROTECT,
        related_name="note",
    )
    content = models.TextField(blank=True)

    def __str__(self):
        return f"Note for appointment {self.appointment_id}"
