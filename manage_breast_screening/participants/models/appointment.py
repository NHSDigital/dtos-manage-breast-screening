import uuid
from datetime import date
from logging import getLogger

from django.db import models
from django.db.models import OuterRef, Prefetch, Subquery
from statemachine import Event, StateMachine
from statemachine.states import States

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
            AppointmentStatusNames.IN_PROGRESS,
        )

    def checked_in(self):
        return self.in_status(AppointmentStatusNames.CHECKED_IN)

    def in_progress(self):
        return self.in_status(AppointmentStatusNames.IN_PROGRESS)

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


class AppointmentStatusNames(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Scheduled"
    CHECKED_IN = "CHECKED_IN", "Checked in"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    CANCELLED = "CANCELLED", "Cancelled"
    DID_NOT_ATTEND = "DID_NOT_ATTEND", "Did not attend"
    SCREENED = "SCREENED", "Screened"
    PARTIALLY_SCREENED = "PARTIALLY_SCREENED", "Partially screened"
    ATTENDED_NOT_SCREENED = "ATTENDED_NOT_SCREENED", "Attended not screened"


class AppointmentStatus(models.Model):
    YET_TO_BEGIN_STATUSES = [
        AppointmentStatusNames.SCHEDULED,
        AppointmentStatusNames.CHECKED_IN,
    ]

    FINAL_STATUSES = [
        AppointmentStatusNames.CANCELLED,
        AppointmentStatusNames.DID_NOT_ATTEND,
        AppointmentStatusNames.SCREENED,
        AppointmentStatusNames.PARTIALLY_SCREENED,
        AppointmentStatusNames.ATTENDED_NOT_SCREENED,
    ]

    name = models.CharField(
        choices=AppointmentStatusNames,
        max_length=50,
        default=AppointmentStatusNames.SCHEDULED,
    )

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    appointment = models.ForeignKey(
        Appointment, on_delete=models.PROTECT, related_name="statuses"
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
        return self.name == AppointmentStatusNames.IN_PROGRESS

    def is_final_status(self):
        return self.name in self.FINAL_STATUSES

    def __str__(self):
        return self.name


class AppointmentMachine(StateMachine):
    _ = States.from_enum(
        AppointmentStatusNames,
        initial=AppointmentStatusNames.SCHEDULED,
        final=AppointmentStatus.FINAL_STATUSES,
    )

    check_in = Event(_.SCHEDULED.to(_.CHECKED_IN))
    start = Event(_.SCHEDULED.to(_.IN_PROGRESS) | _.CHECKED_IN.to(_.IN_PROGRESS))
    cancel = Event(_.SCHEDULED.to(_.CANCELLED))
    mark_did_not_attend = Event(_.SCHEDULED.to(_.DID_NOT_ATTEND))
    mark_attended_not_screened = Event(
        _.SCHEDULED.to(_.ATTENDED_NOT_SCREENED)
        | _.CHECKED_IN.to(_.ATTENDED_NOT_SCREENED)
        | _.IN_PROGRESS.to(_.ATTENDED_NOT_SCREENED)
    )
    screen = Event(_.IN_PROGRESS.to(_.SCREENED))
    partial_screen = Event(_.IN_PROGRESS.to(_.PARTIALLY_SCREENED))


class AppointmentWorkflowStepCompletion(models.Model):
    """
    Tracks progress through the mammography appointment workflow.
    """

    class StepNames(models.TextChoices):
        CONFIRM_IDENTITY = "CONFIRM_IDENTITY", "Confirm identity"
        REVIEW_MEDICAL_INFORMATION = (
            "REVIEW_MEDICAL_INFORMATION",
            "Review medical information",
        )
        TAKE_IMAGES = "TAKE_IMAGES", "Take images"
        CHECK_INFORMATION = "CHECK_INFORMATION", "Check information"

    step_name = models.CharField(choices=StepNames, max_length=50)
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.PROTECT,
        related_name="completed_workflow_steps",
    )
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True)


class AppointmentNote(BaseModel):
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.PROTECT,
        related_name="note",
    )
    content = models.TextField(blank=True)

    def __str__(self):
        return f"Note for appointment {self.appointment_id}"
