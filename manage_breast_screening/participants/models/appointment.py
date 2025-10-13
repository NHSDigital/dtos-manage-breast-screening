import uuid
from datetime import date
from logging import getLogger

from django.db import models
from django.db.models import OuterRef, Subquery

from ...core.models import BaseModel
from ...core.querysets import ProviderScopedQuerySet
from .screening_episode import ScreeningEpisode

logger = getLogger(__name__)


class AppointmentQuerySet(ProviderScopedQuerySet):
    def _provider_filter_kwargs(self, provider_id):
        return {"clinic_slot__clinic__setting__provider_id": provider_id}

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
        )

    def checked_in(self):
        return self.in_status(AppointmentStatus.CHECKED_IN)

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

    def for_clinic_and_filter(self, clinic, filter):
        queryset = self.filter(clinic_slot__clinic=clinic)
        match filter:
            case "remaining":
                return queryset.remaining()
            case "checked_in":
                return queryset.checked_in()
            case "complete":
                return queryset.complete()
            case "all":
                return queryset
            case _:
                raise ValueError(filter)

    def filter_counts_for_clinic(self, clinic):
        counts = {}
        for filter in ["remaining", "checked_in", "complete", "all"]:
            counts[filter] = self.for_clinic_and_filter(clinic, filter).count()
        return counts


class Appointment(BaseModel):
    objects = AppointmentQuerySet.as_manager()

    screening_episode = models.ForeignKey(ScreeningEpisode, on_delete=models.PROTECT)
    clinic_slot = models.ForeignKey(
        "clinics.ClinicSlot",
        on_delete=models.PROTECT,
    )
    reinvite = models.BooleanField(default=False)
    stopped_reasons = models.JSONField(null=True, blank=True)

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
    def in_progress(self):
        return self.current_status.in_progress


class AppointmentStatus(models.Model):
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
    state = models.CharField(choices=STATUS_CHOICES, max_length=50, default=CONFIRMED)

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    appointment = models.ForeignKey(
        Appointment, on_delete=models.PROTECT, related_name="statuses"
    )

    class Meta:
        ordering = ["-created_at"]

    @property
    def in_progress(self):
        """
        Is this state one of the in-progress states?
        """
        return self.state in [self.CONFIRMED, self.CHECKED_IN]
