import uuid
from datetime import date
from logging import getLogger

from django.db import models
from statemachine import Event, StateMachine
from statemachine.mixins import MachineMixin
from statemachine.states import States

from manage_breast_screening.manual_images.models import Series, Study
from manage_breast_screening.users.models import User

from ...core.models import BaseModel
from .screening_episode import ScreeningEpisode

logger = getLogger(__name__)


class ActionPerformedByDifferentUser(Exception):
    """
    The action has already been performed, but by a different user.
    """


class AppointmentStatusNames(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Scheduled"
    CHECKED_IN = "CHECKED_IN", "Checked in"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    CANCELLED = "CANCELLED", "Cancelled"
    DID_NOT_ATTEND = "DID_NOT_ATTEND", "Did not attend"
    SCREENED = "SCREENED", "Screened"
    PARTIALLY_SCREENED = "PARTIALLY_SCREENED", "Partially screened"
    ATTENDED_NOT_SCREENED = "ATTENDED_NOT_SCREENED", "Attended not screened"
    PAUSED = "PAUSED", "Paused"


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


class AppointmentMachine(StateMachine):
    _ = States.from_enum(
        AppointmentStatusNames,
        initial=AppointmentStatusNames.SCHEDULED,
        final=FINAL_STATUSES,
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
    pause = Event(_.IN_PROGRESS.to(_.PAUSED))
    resume = Event(_.PAUSED.to(_.IN_PROGRESS))

    def can(self, action) -> bool:
        return action in self.allowed_events


class AppointmentQuerySet(models.QuerySet):
    def in_status(self, *statuses):
        return self.filter(status__in=statuses)

    def remaining(self):
        return self.in_status(*YET_TO_BEGIN_STATUSES)

    def checked_in(self):
        return self.in_status(AppointmentStatusNames.CHECKED_IN)

    def in_progress_or_paused(self):
        return self.in_status(
            AppointmentStatusNames.IN_PROGRESS, AppointmentStatusNames.PAUSED
        )

    def for_participant(self, participant_id):
        return self.filter(screening_episode__participant_id=participant_id)

    def complete(self):
        return self.in_status(*FINAL_STATUSES)

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
                return self.in_progress_or_paused()
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


class Appointment(MachineMixin, BaseModel):
    state_machine_name = (
        "manage_breast_screening.participants.models.appointment.AppointmentMachine"
    )
    state_machine_attr = "sm"
    state_field_name = "status"
    bind_events_as_methods = True

    objects = AppointmentQuerySet.as_manager()

    screening_episode = models.ForeignKey(ScreeningEpisode, on_delete=models.PROTECT)
    clinic_slot = models.ForeignKey(
        "clinics.ClinicSlot",
        on_delete=models.PROTECT,
    )
    reinvite = models.BooleanField(default=False)
    stopped_reasons = models.JSONField(null=True, blank=True)

    status = models.CharField(
        choices=AppointmentStatusNames,
        max_length=50,
        default=AppointmentStatusNames.SCHEDULED,
    )
    status_changed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="appointment_status_changes",
    )
    status_changed_at = models.DateTimeField(null=True, blank=True)

    @property
    def current_status(self):
        return AppointmentStatus(appointment=self)

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
    def active(self):
        return self.is_in_progress() or self.is_yet_to_begin()

    def is_yet_to_begin(self):
        return self.status in YET_TO_BEGIN_STATUSES

    def is_in_progress(self):
        return self.status == AppointmentStatusNames.IN_PROGRESS

    def is_in_progress_with(self, user):
        return self.is_in_progress() and self.status_changed_by == user

    def is_final_status(self):
        return self.status in FINAL_STATUSES

    def series(self):
        """
        Get the series associated with this appointment, if any.
        """
        try:
            return self.study.series_set.all()
        except Study.DoesNotExist:
            return Series.objects.none()

    def has_study(self):
        try:
            self.study
            return True
        except Study.DoesNotExist:
            return False

    def recent_reported_mammograms(self, since_date=None):
        """
        Get reported mammograms for this appointment, optionally filtered
        to those created after a given date (e.g. the last confirmed mammogram date).
        """
        qs = self.reported_mammograms.select_related(
            "created_by",
            "appointment__clinic_slot__clinic__setting__provider",
        ).order_by("-created_at")

        if since_date:
            qs = qs.filter(created_at__gt=since_date)

        return qs


class AppointmentStatus:
    def __init__(self, appointment):
        self.appointment = appointment

    def get_name_display(self):
        return self.appointment.get_status_display()

    @property
    def name(self):
        return self.appointment.status

    @property
    def created_at(self):
        return self.appointment.updated_at

    @property
    def created_by(self):
        return self.appointment.status_changed_by

    @property
    def active(self):
        return self.appointment.active

    def is_yet_to_begin(self):
        return self.appointment.is_yet_to_begin()

    def is_in_progress(self):
        return self.appointment.is_in_progress()

    def is_in_progress_with(self, user):
        return self.appointment.is_in_progress_with(user)

    def is_final_status(self):
        return self.appointment.is_final_status()

    def __str__(self):
        return self.name


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
