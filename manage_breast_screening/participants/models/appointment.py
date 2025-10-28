from datetime import date
from functools import wraps
from logging import getLogger

from django.db import models
from django_fsm import FSMField, transition

from manage_breast_screening.users.models import User

from ...core.models import BaseModel
from .screening_episode import ScreeningEpisode

logger = getLogger(__name__)


def with_current_user(fn):
    @wraps(fn)
    def wrapped(instance, current_user, *args, **kwargs):
        instance.last_updated_by = current_user
        return fn(instance, *args, **kwargs)

    return wrapped


class AppointmentQuerySet(models.QuerySet):
    def in_status(self, *statuses):
        return self.filter(state__in=statuses)

    def remaining(self):
        return self.in_status(
            Appointment.CONFIRMED,
            Appointment.CHECKED_IN,
        )

    def checked_in(self):
        return self.in_status(Appointment.CHECKED_IN)

    def complete(self):
        return self.in_status(
            Appointment.CANCELLED,
            Appointment.DID_NOT_ATTEND,
            Appointment.SCREENED,
            Appointment.PARTIALLY_SCREENED,
            Appointment.ATTENDED_NOT_SCREENED,
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
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    DID_NOT_ATTEND = "DID_NOT_ATTEND"
    CHECKED_IN = "CHECKED_IN"
    SCREENED = "SCREENED"
    PARTIALLY_SCREENED = "PARTIALLY_SCREENED"
    ATTENDED_NOT_SCREENED = "ATTENDED_NOT_SCREENED"

    STATUS_CHOICES = {
        CONFIRMED: "Confirmed",
        CANCELLED: "Cancelled",
        DID_NOT_ATTEND: "Did not attend",
        CHECKED_IN: "Checked in",
        SCREENED: "Screened",
        PARTIALLY_SCREENED: "Partially screened",
        ATTENDED_NOT_SCREENED: "Attended not screened",
    }

    objects = AppointmentQuerySet.as_manager()

    screening_episode = models.ForeignKey(ScreeningEpisode, on_delete=models.PROTECT)
    clinic_slot = models.ForeignKey(
        "clinics.ClinicSlot",
        on_delete=models.PROTECT,
    )
    reinvite = models.BooleanField(default=False)
    stopped_reasons = models.JSONField(null=True, blank=True)

    state = FSMField(
        choices=STATUS_CHOICES, max_length=50, default=CONFIRMED, protected=True
    )
    last_updated_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True)

    @with_current_user
    @transition(field=state, source=CONFIRMED, target=CHECKED_IN)
    def check_in(self):
        pass

    @with_current_user
    @transition(field=state, source=[CONFIRMED, CHECKED_IN], target=SCREENED)
    def screen(self):
        pass

    @with_current_user
    @transition(field=state, source=[CONFIRMED, CHECKED_IN], target=PARTIALLY_SCREENED)
    def partially_screen(self):
        pass

    @with_current_user
    @transition(field=state, source=[CONFIRMED, CHECKED_IN], target=DID_NOT_ATTEND)
    def mark_did_not_screen(self):
        pass

    @with_current_user
    @transition(field=state, source=CONFIRMED, target=CANCELLED)
    def cancel(self):
        pass

    @with_current_user
    @transition(field=state, source=CONFIRMED, target=DID_NOT_ATTEND)
    def mark_did_not_attend(self):
        pass

    @classmethod
    def filter_counts_for_clinic(cls, clinic):
        counts = {}
        for filter in ["remaining", "checked_in", "complete", "all"]:
            counts[filter] = clinic.appointments.for_filter(filter).count()
        return counts

    @property
    def provider(self):
        return self.clinic_slot.provider

    @property
    def participant(self):
        return self.screening_episode.participant

    @property
    def in_progress(self):
        return self.state in [self.CONFIRMED, self.CHECKED_IN]
